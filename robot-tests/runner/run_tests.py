import os
import sys
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import argparse
from robot import run
from libs.config_loader import load_config

TESTS_DIR = os.path.join(PROJECT_ROOT, "tests")
ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, "artifacts", "robot", "runs")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", default="dev")
    parser.add_argument("--include", default=None)
    parser.add_argument("--base-url", dest="base_url", default=None)
    args = parser.parse_args()

    config = load_config(args.env)
    if args.base_url:
        config["base_url"] = args.base_url

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_output_dir = os.path.join(ARTIFACTS_DIR, timestamp)
    os.makedirs(run_output_dir, exist_ok=True)

    variables = [
        f"BASE_URL:{config['base_url']}",
        f"TIMEOUT:{config.get('timeout', 10)}",
        f"ENV_NAME:{config.get('env_name', args.env)}",
    ]
    robot_options = {
        "outputdir": run_output_dir,
        "loglevel": "INFO",
        "variable": variables,
    }
    if args.include:
        robot_options["include"] = args.include

    exit_code = run(
        TESTS_DIR,
        **robot_options,
    )

    print(f"\nRobot results stored in: {run_output_dir}")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
