import os
import subprocess
import sys
import json
from pathlib import Path

def test_build_prompt_and_no_key(tmp_path):
    # Ensure script returns prompt when no API key present
    script = Path("src/gptlinux5.py")
    assert script.exists()
    env = os.environ.copy()
    env.pop("GPTLINUX5_API_KEY", None)
    env.pop("OPENAI_API_KEY", None)
    p = subprocess.run([sys.executable, str(script), "--cmd", "echo hello"], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out = p.stdout + p.stderr
    assert "PROMPT" in out or "Prompt" in out

def test_daemon_requires_token(tmp_path):
    # Ensure daemon 401s without token (quick functional check by calling the Flask route using test client)
    from src import gptlinux5d
    app = gptlinux5d.app
    client = app.test_client()
    rv = client.post("/analyze", json={"cmd": "echo hi"})
    assert rv.status_code == 401
