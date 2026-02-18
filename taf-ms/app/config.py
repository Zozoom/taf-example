"""Shared configuration and path constants."""
import os
from typing import Any

import yaml

ROBOT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../robot-tests")
)
ROBOT_RUNS_PATH = os.path.join(ROBOT_ROOT, "artifacts", "robot", "runs")
CONFIG_DIR = os.path.join(ROBOT_ROOT, "config")
TESTS_DIR = os.path.join(ROBOT_ROOT, "tests")
RESOURCES_DIR = os.path.join(ROBOT_ROOT, "resources")


def load_env_configs() -> dict[str, Any]:
    """Read environment configs from robot-tests/config/*.yaml."""
    configs: dict[str, Any] = {}
    if not os.path.isdir(CONFIG_DIR):
        return configs

    for name in sorted(os.listdir(CONFIG_DIR)):
        if not name.endswith(".yaml"):
            continue
        env_name = name[:-5]
        path = os.path.join(CONFIG_DIR, name)
        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            configs[env_name] = {
                "env_name": data.get("env_name", env_name),
                "base_url": data.get("base_url", ""),
            }
        except Exception:
            continue
    return configs
