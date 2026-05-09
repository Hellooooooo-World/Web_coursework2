"""Process-level smoke test: CLI loads like a real user invocation."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from tests.conftest import PROJECT_ROOT


def test_cli_help_via_module_invocation() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "src.main", "-c", "help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "build" in proc.stdout and "find" in proc.stdout


def test_cli_load_missing_index_shows_message(tmp_path: Path) -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "src.main", "-c", "load", "-i", str(tmp_path / "missing.json")],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "No index file" in proc.stdout
