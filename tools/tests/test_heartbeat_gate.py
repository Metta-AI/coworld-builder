"""Exercise the gate CLI without credentials; no provider calls or deployments."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory(prefix="coworld-heartbeat-gate-") as tmp:
    for args in ([], ["--fire"]):
        summary = Path(tmp) / ("fire.md" if args else "decide.md")
        env = {key: value for key, value in os.environ.items() if key != "ASANA_PAT"}
        env["GITHUB_STEP_SUMMARY"] = str(summary)
        result = subprocess.run(
            [sys.executable, "fleet/bin/heartbeat_gate.py", *args],
            cwd=root,
            env=env,
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode == 1, result
        decision = json.loads(result.stdout)
        assert decision["board_error"] == "ASANA_PAT is not set", decision
        assert not decision["work"], decision
        assert "fired" not in decision, decision
        assert decision["board_error"] in summary.read_text()

print("Gate CLI reports missing credentials as failure, including --fire")
