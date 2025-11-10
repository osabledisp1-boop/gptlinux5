#!/usr/bin/env python3
"""
Simple daemon that exposes an HTTP API to analyze commands using the same prompt logic.
Auth: Bearer token in Authorization header. Token must match GPTLINUX5_DAEMON_TOKEN env var.
"""
import os
import json
from flask import Flask, request, jsonify, abort
from src.gptlinux5 import build_prompt, call_openai_chat, run_command_local

app = Flask(__name__)

def require_token(f):
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        token = None
        if auth.startswith("Bearer "):
            token = auth.split(" ", 1)[1]
        expected = os.environ.get("GPTLINUX5_DAEMON_TOKEN")
        if not expected or token != expected:
            abort(401)
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@app.route("/analyze", methods=["POST"])
@require_token
def analyze():
    data = request.json or {}
    cmd = data.get("cmd") or data.get("script")
    do_exec = bool(data.get("exec"))
    docker = bool(data.get("docker"))
    model = data.get("model") or os.environ.get("GPTLINUX5_MODEL", "gpt-4o-mini")
    api_url = os.environ.get("GPTLINUX5_API_URL")
    api_key = os.environ.get("GPTLINUX5_API_KEY")
    if not cmd:
        return jsonify({"error": "missing cmd/script"}), 400
    exec_output = None
    if do_exec:
        if docker:
            # Best-effort docker sandbox
            import shlex, shutil
            if shutil.which("docker"):
                docker_image = "python:3.11-slim"
                docker_cmd = f"docker run --rm {docker_image} bash -lc {shlex.quote(cmd)}"
                exec_output = run_command_local(docker_cmd, use_shell=True)
            else:
                return jsonify({"error": "docker not available on host"}), 400
        else:
            exec_output = run_command_local(cmd, use_shell=True)
    prompt = build_prompt(cmd, exec_output=exec_output)
    if not api_key or not api_url:
        return jsonify({"prompt": prompt, "exec_output": exec_output}), 200
    try:
        response = call_openai_chat(api_url, api_key, model, prompt)
    except Exception as e:
        return jsonify({"error": "api error", "detail": str(e)}), 500
    return jsonify({"analysis": response, "exec_output": exec_output})

if __name__ == "__main__":
    # Simple local run: prefer unix socket if provided
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8080)
    args = p.parse_args()
    app.run(host=args.host, port=args.port)
