import os
from pathlib import Path
import subprocess
import sys


def test_demo_runs_twice_without_touching_configured_database(tmp_path):
    script = Path(__file__).resolve().parents[1] / "demo.py"
    database = tmp_path / "personal.db"
    for _ in range(2):
        result = subprocess.run(
            [sys.executable, str(script)], cwd=tmp_path,
            env={**os.environ, "APPLICATIONS_DB": str(database)},
            check=True, capture_output=True, text=True,
        )
        assert result.stdout.splitlines() == ["Application 1: interview", "Interviews: 1"]
    assert not database.exists()
