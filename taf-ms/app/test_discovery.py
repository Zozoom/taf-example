"""Discover test files and tags from robot-tests."""
import os
import re

from app.config import RESOURCES_DIR, ROBOT_ROOT, TESTS_DIR

# Tags we consider "predefined suites"
PREDEFINED_TAGS = ("smoke", "regression")


def _tags_in_file(path: str) -> set[str]:
    """Extract [Tags] from a .robot file."""
    tags = set()
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            in_tags = False
            for line in f:
                line = line.rstrip()
                if re.match(r"^\s*\[\s*Tags\s*\]", line, re.IGNORECASE):
                    in_tags = True
                    rest = re.sub(r"^\s*\[\s*Tags\s*\]\s*", "", line, flags=re.IGNORECASE)
                    tags.update(t.strip().lower() for t in rest.split() if t.strip())
                    continue
                if in_tags:
                    if line.strip().startswith("[") or not line.strip():
                        in_tags = False
                    else:
                        tags.update(t.strip().lower() for t in line.split() if t.strip())
    except Exception:
        pass
    return tags


def discover_tests() -> dict:
    """
    Scan tests/ for .robot files and map tags to file names.
    Returns: { "tags": {...}, "all_tags": {...}, "robot_files": [...], "resource_files": [...] }
    """
    tags_to_files: dict[str, list[str]] = {t: [] for t in PREDEFINED_TAGS}
    all_tags_to_files: dict[str, list[str]] = {}
    robot_files: list[str] = []
    resource_files: list[str] = []

    if not os.path.isdir(TESTS_DIR):
        return {
            "tags": tags_to_files,
            "all_tags": all_tags_to_files,
            "robot_files": robot_files,
            "resource_files": resource_files,
        }

    for name in sorted(os.listdir(TESTS_DIR)):
        if not name.lower().endswith(".robot"):
            continue
        path = os.path.join(TESTS_DIR, name)
        if not os.path.isfile(path):
            continue
        robot_files.append(name)
        file_tags = _tags_in_file(path)
        for tag in PREDEFINED_TAGS:
            if tag in file_tags:
                tags_to_files[tag].append(name)
        for tag in file_tags:
            if tag not in all_tags_to_files:
                all_tags_to_files[tag] = []
            if name not in all_tags_to_files[tag]:
                all_tags_to_files[tag].append(name)

    if os.path.isdir(RESOURCES_DIR):
        for name in sorted(os.listdir(RESOURCES_DIR)):
            if name.lower().endswith(".resource"):
                resource_files.append(name)

    return {
        "tags": tags_to_files,
        "all_tags": all_tags_to_files,
        "robot_files": robot_files,
        "resource_files": resource_files,
    }
