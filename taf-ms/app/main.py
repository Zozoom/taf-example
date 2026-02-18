import os
import shutil
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Iterator, List

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, text
from sqlalchemy.exc import OperationalError

from app.config import RESOURCES_DIR, ROBOT_RUNS_PATH, TESTS_DIR, load_env_configs
from app.test_discovery import discover_tests
from app.db import Base, SessionLocal, engine
from app.models import TestRun
from app.runner_service import run_robot, update_run_result
from app.scheduler import cancel_scheduled_run, schedule_recurring, schedule_run


def _wait_for_db(max_tries: int = 30, delay: float = 2.0) -> None:
    """Block until the database is reachable (Docker startup)."""
    for _ in range(max_tries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except OperationalError:
            time.sleep(delay)
    raise RuntimeError("Database unavailable after waiting.")


_wait_for_db()

Base.metadata.create_all(bind=engine)

# Add finished_at column if missing (migration)
try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE test_runs ADD COLUMN finished_at TIMESTAMP NULL"))
except Exception:
    pass

app = FastAPI(title="TAF Dashboard")
templates = Jinja2Templates(directory="app/templates")


def _index_context(error: str | None = None) -> dict:
    """Base context for index template."""
    ctx = {
        "request": None,
        "env_configs": load_env_configs(),
        "test_discovery": discover_tests(),
    }
    if error:
        ctx["error"] = error
    return ctx


def _parse_time(s: str) -> tuple[int, int]:
    """Parse HH:MM or HH:MM:SS to (hour, minute)."""
    parts = s.split(":")
    return int(parts[0]), int(parts[1]) if len(parts) > 1 else 0


def _format_run_duration(run):
    """Return duration string for a run, or 'Running since...' for in-progress."""
    if run.status == "running" and run.created_at:
        return f"Running since {run.created_at.strftime('%H:%M')}"
    if run.finished_at and run.created_at:
        secs = (run.finished_at - run.created_at).total_seconds()
        if secs < 60:
            return f"{int(secs)}s"
        m, s = int(secs) // 60, int(secs) % 60
        return f"{m}m {s}s" if s else f"{m}m"
    return "—"


@contextmanager
def get_db() -> Iterator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _save_uploaded_tests(uploaded: List[UploadFile]) -> None:
    """Persist uploaded .robot / .resource files into robot-tests volume."""
    if not uploaded:
        return
    os.makedirs(TESTS_DIR, exist_ok=True)
    os.makedirs(RESOURCES_DIR, exist_ok=True)
    for f in uploaded:
        if not f.filename:
            continue
        name = os.path.basename(f.filename)
        ext = os.path.splitext(name.lower())[1]
        dest_dir = TESTS_DIR if ext == ".robot" else RESOURCES_DIR if ext == ".resource" else None
        if dest_dir:
            with open(os.path.join(dest_dir, name), "wb") as out:
                shutil.copyfileobj(f.file, out)


def _create_run(db, env: str, test_type: str, status: str, scheduled_for=None, target_url=None) -> TestRun:
    run = TestRun(
        env=env,
        test_type=test_type,
        status=status,
        scheduled_for=scheduled_for,
        target_url=target_url or None,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def _run_robot_background(run_id: int, env: str, test_type: str, target_url: str | None) -> None:
    """Execute run_robot in a thread and update the run when done."""
    result = run_robot(env, test_type, target_url=target_url)
    update_run_result(run_id, result)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    ctx = _index_context()
    ctx["request"] = request
    return templates.TemplateResponse("index.html", ctx)


@app.post("/run-now")
def run_now(
    request: Request,
    env: str = Form(...),
    test_mode: str = Form("suite"),
    test_suite: str = Form("smoke"),
    tags: str = Form(""),
    schedule_type: str = Form("immediate"),
    schedule_time: str = Form(None),
    schedule_daily_time: str = Form(None),
    schedule_weekly_day: str = Form(None),
    schedule_weekly_time: str = Form(None),
    target_url: str = Form(None),
    uploaded_tests: List[UploadFile] = File(None),
):
    uploaded = uploaded_tests or []

    if test_mode == "upload":
        robot_count = sum(1 for f in uploaded if f.filename and f.filename.lower().endswith(".robot"))
        resource_count = sum(1 for f in uploaded if f.filename and f.filename.lower().endswith(".resource"))
        if robot_count < 1 or resource_count < 1:
            ctx = _index_context("Upload mode requires at least one .robot and one .resource file.")
            ctx["request"] = request
            return templates.TemplateResponse("index.html", ctx, status_code=400)
        include_expr = ""  # run all tests
    elif test_mode == "custom":
        include_expr = (tags or "").strip()
        if not include_expr:
            ctx = _index_context("Custom tags mode requires a tag expression.")
            ctx["request"] = request
            return templates.TemplateResponse("index.html", ctx, status_code=400)
    else:
        include_expr = test_suite

    with get_db() as db:
        _save_uploaded_tests(uploaded)

        if schedule_type == "custom" and schedule_time:
            run_time = datetime.fromisoformat(schedule_time)
            run = _create_run(db, env, include_expr, "scheduled", scheduled_for=run_time, target_url=target_url)
            schedule_run(run.id, run_time)
        elif schedule_type == "daily" and schedule_daily_time:
            h, m = _parse_time(schedule_daily_time)
            schedule_recurring("daily", env, include_expr, target_url or None, h, m)
        elif schedule_type == "weekly" and schedule_weekly_day and schedule_weekly_time:
            h, m = _parse_time(schedule_weekly_time)
            schedule_recurring("weekly", env, include_expr, target_url or None, h, m, day_of_week=schedule_weekly_day)
        else:
            run = _create_run(db, env, include_expr, "running", target_url=target_url)
            run_id = run.id
            thread = threading.Thread(
                target=_run_robot_background,
                args=(run_id, env, include_expr, target_url or None),
                daemon=True,
            )
            thread.start()

    return RedirectResponse(url="/runs", status_code=303)


@app.get("/runs", response_class=HTMLResponse)
def list_runs(request: Request):
    with get_db() as db:
        runs = db.query(TestRun).order_by(TestRun.id.desc()).all()
    return templates.TemplateResponse(
        "runs.html",
        {"request": request, "runs": runs, "format_duration": _format_run_duration},
    )


@app.get("/stats", response_class=HTMLResponse)
def stats(request: Request):
    with get_db() as db:
        total_runs = db.query(TestRun).count()
        by_status = db.query(TestRun.status, func.count(TestRun.id)).group_by(TestRun.status).all()

    status_counts = {status or "unknown": count for status, count in by_status}
    return templates.TemplateResponse(
        "stats.html",
        {"request": request, "total_runs": total_runs, "status_counts": status_counts},
    )


@app.post("/rerun/{run_id}")
def rerun(run_id: int):
    """Create a new run with same params as the given run and start it immediately."""
    with get_db() as db:
        run = db.get(TestRun, run_id)
        if not run:
            return RedirectResponse(url="/runs", status_code=303)
        env, test_type, target_url = run.env, run.test_type, run.target_url
        new_run = _create_run(db, env, test_type, "running", target_url=target_url)
        run_id = new_run.id
        thread = threading.Thread(
            target=_run_robot_background,
            args=(run_id, env, test_type, target_url),
            daemon=True,
        )
        thread.start()
    return RedirectResponse(url="/runs", status_code=303)


@app.post("/cancel/{run_id}")
def cancel_run(run_id: int):
    with get_db() as db:
        run = db.get(TestRun, run_id)
        if run and run.status == "scheduled":
            cancel_scheduled_run(run_id)
            run.status = "cancelled"
            db.commit()
    return RedirectResponse(url="/runs", status_code=303)


@app.get("/report/{run_folder}", response_class=HTMLResponse)
def open_report_page(request: Request, run_folder: str):
    return templates.TemplateResponse("report.html", {"request": request, "run_folder": run_folder})


@app.get("/report-file/{run_folder}")
def open_report_file(run_folder: str, download: bool = False):
    report_path = os.path.join(ROBOT_RUNS_PATH, run_folder, "log.html")
    if not os.path.exists(report_path):
        return {"error": "Report not found"}
    headers = {}
    if download:
        headers["Content-Disposition"] = f'attachment; filename="report-{run_folder}.html"'
    return FileResponse(report_path, headers=headers)
