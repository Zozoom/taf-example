from datetime import datetime
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler

from app.db import SessionLocal
from app.models import TestRun
from app.runner_service import run_robot, update_run_result

scheduler = BackgroundScheduler()
scheduler.start()


def schedule_run(run_id: int, run_time) -> None:
    scheduler.add_job(
        func=execute_scheduled_run,
        trigger="date",
        run_date=run_time,
        args=[run_id],
        id=str(run_id),
        replace_existing=True,
    )


def cancel_scheduled_run(run_id: int) -> None:
    try:
        scheduler.remove_job(str(run_id))
    except Exception:
        pass


def execute_recurring_run(env: str, test_type: str, target_url: Optional[str]) -> None:
    """Create a TestRun and execute it (for daily/weekly recurring)."""
    db = SessionLocal()
    try:
        run = TestRun(env=env, test_type=test_type, status="running", target_url=target_url)
        db.add(run)
        db.commit()
        db.refresh(run)
        run_id = run.id
    finally:
        db.close()
    result = run_robot(env, test_type, target_url=target_url)
    update_run_result(run_id, result)


def schedule_recurring(
    schedule_type: str,
    env: str,
    test_type: str,
    target_url: Optional[str],
    hour: int,
    minute: int,
    day_of_week: Optional[str] = None,
) -> str:
    """Add daily or weekly recurring job. Returns job_id."""
    job_id = f"recurring-{schedule_type}-{env}-{test_type}-{id(datetime.now())}"
    trigger_kw = {"hour": hour, "minute": minute}
    if schedule_type == "weekly" and day_of_week:
        trigger_kw["day_of_week"] = day_of_week
    scheduler.add_job(
        func=execute_recurring_run,
        trigger="cron",
        id=job_id,
        replace_existing=True,
        args=[env, test_type, target_url],
        **trigger_kw,
    )
    return job_id


def execute_scheduled_run(run_id: int) -> None:
    db = SessionLocal()
    try:
        run = db.get(TestRun, run_id)
        if not run:
            return
        env, test_type, target_url = run.env, run.test_type, run.target_url
        run.status = "running"
        db.commit()
    finally:
        db.close()
    result = run_robot(env, test_type, target_url=target_url)
    update_run_result(run_id, result)
