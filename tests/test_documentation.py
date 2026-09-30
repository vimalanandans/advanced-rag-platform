import subprocess
import sys
from pathlib import Path


def test_documentation_reference_matches_public_local_surface():
    root = Path(__file__).parent.parent
    result = subprocess.run(
        [sys.executable, "scripts/check_docs.py"], cwd=root, capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
