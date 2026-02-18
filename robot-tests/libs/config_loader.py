import os
import yaml

DEFAULTS = {
    "base_url": "",
    "timeout": 10,
    "env_name": "dev",
}


def load_config(env: str) -> dict:
    project_root = os.path.dirname(os.path.dirname(__file__))
    config_path = os.path.join(project_root, "config", f"{env}.yaml")

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config not found for env: {env}")

    with open(config_path, "r", encoding="utf-8") as f:
        loaded = yaml.safe_load(f) or {}
    return {**DEFAULTS, **loaded}
