"""Enforces the project rule: no Python file may exceed 150 physical lines.

Counts ALL physical lines, including blank lines and comments — this is a stricter,
explicit project rule (see docs/PLAN.md ADR-006) layered on top of the submission
guidelines' logical-line cap. Scans src/, tests/, and tools/ (if present).
"""

from pathlib import Path

import pytest

LINE_LIMIT = 150
SCAN_DIRS = ["src", "tests", "tools"]
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _iter_python_files() -> list[Path]:
    found: list[Path] = []
    for dir_name in SCAN_DIRS:
        root = PROJECT_ROOT / dir_name
        if root.exists():
            found.extend(sorted(root.rglob("*.py")))
    return found


def _physical_line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


@pytest.mark.parametrize(
    "path",
    _iter_python_files(),
    ids=lambda p: str(p.relative_to(PROJECT_ROOT)),
)
def test_python_file_within_line_limit(path: Path) -> None:
    count = _physical_line_count(path)
    assert count <= LINE_LIMIT, (
        f"{path.relative_to(PROJECT_ROOT)} has {count} physical lines, exceeds the "
        f"{LINE_LIMIT}-line project limit (docs/PLAN.md ADR-006) — split into smaller modules."
    )


def test_at_least_one_python_file_was_scanned() -> None:
    """Guards against this check silently passing because nothing was found."""
    assert len(_iter_python_files()) > 0
