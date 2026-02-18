import os
import subprocess
from datetime import datetime
from xml.etree import ElementTree

from app.config import ROBOT_RUNS_PATH, ROBOT_ROOT
from app.db import SessionLocal
from app.models import TestRun


def _status_from_output_xml(runs_path: str, latest: str | None) -> str | None:
    if not latest:
        return None

    output_path = os.path.join(runs_path, latest, "output.xml")
    if not os.path.exists(output_path):
        return None

    try:
        tree = ElementTree.parse(output_path)
        root = tree.getroot()

        # Prefer total statistics, fall back to first suite stat
        stat = root.find("./statistics/total/stat")
        if stat is None:
            stat = root.find("./statistics/suite/stat")

        if stat is None:
            return None

        failed = int(stat.get("fail", "0"))
        return "finished" if failed == 0 else "failed"
    except Exception:
        return None


def run_robot(env: str = "dev", test_type: str = "smoke", target_url: str | None = None):
    cmd = [
        "python",
        os.path.join(ROBOT_ROOT, "runner", "run_tests.py"),
        "--env",
        env,
    ]

    if target_url:
        cmd.extend(["--base-url", target_url])

    # pass tag include properly
    if test_type:
        cmd.extend(["--include", test_type])

    result = subprocess.run(cmd, capture_output=True, text=True)

    latest = None
    if os.path.exists(ROBOT_RUNS_PATH):
        folders = sorted(os.listdir(ROBOT_RUNS_PATH), reverse=True)
        if folders:
            latest = folders[0]

    # ---------- interpret Robot outcome ----------
    status_code = result.returncode

    interpreted_status = _status_from_output_xml(ROBOT_RUNS_PATH, latest)
    if interpreted_status is None:
        if status_code == 0:
            interpreted_status = "finished"
        elif status_code == 1:
            interpreted_status = "failed"
        else:
            interpreted_status = "error"

    return {
        "returncode": status_code,
        "interpreted_status": interpreted_status,
        "run_folder": latest,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def update_run_result(run_id: int, result: dict) -> None:
    """Update a TestRun with robot execution result."""
    db = SessionLocal()
    try:
        run = db.get(TestRun, run_id)
        if run:
            run.status = result.get("interpreted_status", "error")
            run.run_folder = result.get("run_folder")
            run.finished_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()
