#!/usr/bin/env python3
"""
GPT Linux 5 CLI

Usage:
  gptlinux5 --cmd "ls -la" [--exec] [--docker]
  gptlinux5 --script path/to/script.sh [--exec]
"""

import argparse
import os
import sys
import subprocess
import shlex
import json
import requests
from textwrap import dedent

DEFAULT_OPENAI_CHAT_COMPLETIONS = "https://api.openai.com/v1/chat/completions"

def build_prompt(command_or_script_text, exec_output=None, extra_instructions=None):
    base = dedent("""
    You are an assistant running on a local Kali-like machine called "GPT Linux 5".
    The user provided a command or shell script below. Provide an accurate, concise,
    and safety-focused analysis: what the command does, possible side effects,
    suggestions to improve/harden it, potential security concerns, and a simulated expected output.
    """).strip()

    prompt = base + "\n\n-- COMMAND/SCRIPT --\n" + command_or_script_text.strip()

    if exec_output is not None:
        prompt += "\n\n-- REAL EXECUTION OUTPUT --\n" + exec_output

    if extra_instructions:
        prompt += "\n\n-- EXTRA INSTRUCTIONS --\n" + extra_instructions

    prompt += "\n\nAnswer in clear sections: Summary, Potential Risks, Suggestions, Simulated Output."
    return prompt

def call_openai_chat(api_url, api_key, model, prompt, timeout=60, temperature=0.0):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful, concise assistant for security-minded command analysis."},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": 800,
    }
    resp = requests.post(api_url, headers=headers, json=data, timeout=timeout)
    resp.raise_for_status()
    j = resp.json()
    if "choices" in j and len(j["choices"]) > 0:
        content = j["choices"][0].get("message", {}).get("content")
        if content:
            return content
        return j["choices"][0].get("text", "")
    if "text" in j:
        return j["text"]
    return json.dumps(j, indent=2)

def run_command_local(cmd, timeout=30, use_shell=False):
    if isinstance(cmd, str) and not use_shell:
        args = shlex.split(cmd)
    else:
        args = cmd
    try:
        if use_shell:
            completed = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, text=True)
        else:
            completed = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, text=True)
        return completed.stdout
    except subprocess.TimeoutExpired:
        return "[Execution timed out after {}s]".format(timeout)
    except Exception as e:
        return "[Execution error: {}]".format(e)

def confirm(prompt):
    try:
        reply = input(prompt + " [y/N]: ").strip().lower()
        return reply == 'y' or reply == 'yes'
    except KeyboardInterrupt:
        print()
        return False

def main():
    p = argparse.ArgumentParser(description="GPT Linux 5 - analyze scripts/commands and optionally use an LLM")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--cmd", type=str, help="single command string to analyze")
    group.add_argument("--script", type=str, help="path to a script file to analyze")
    p.add_argument("--exec", action="store_true", help="execute the command locally and include real output (dangerous)")
    p.add_argument("--docker", action="store_true", help="execute inside Docker sandbox (if --exec)")
    p.add_argument("--model", default="gpt-4o-mini", help="LLM model name")
    p.add_argument("--timeout", type=int, default=30, help="local execution timeout in seconds")
    p.add_argument("--web-timeout", type=int, default=60, help="web API timeout in seconds")
    p.add_argument("--temp", type=float, default=0.0, help="temperature for LLM responses")
    p.add_argument("--no-confirm", action="store_true", help="do not prompt for confirmation before local execution")
    args = p.parse_args()

    if args.script:
        if not os.path.isfile(args.script):
            print("Script not found:", args.script, file=sys.stderr)
            sys.exit(2)
        with open(args.script, "r", encoding="utf-8") as f:
            cmd_text = f.read()
    else:
        cmd_text = args.cmd

    exec_output = None

    if args.exec:
        if args.docker:
            import shutil
            if not shutil.which("docker"):
                print("Docker requested but not available; running locally instead.", file=sys.stderr)
            else:
                docker_image = "python:3.11-slim"
                docker_cmd = f"docker run --rm {docker_image} bash -lc {shlex.quote(cmd_text)}"
                print("Running inside Docker (best-effort sandbox).")
                exec_output = run_command_local(docker_cmd, timeout=args.timeout, use_shell=True)
        if exec_output is None:
            if not args.no_confirm:
                ok = confirm("About to execute the command/script locally. This is potentially unsafe. Proceed?")
                if not ok:
                    print("Execution aborted by user; continuing without execution.")
                else:
                    exec_output = run_command_local(cmd_text, timeout=args.timeout, use_shell=True)
            else:
                exec_output = run_command_local(cmd_text, timeout=args.timeout, use_shell=True)

    prompt = build_prompt(cmd_text, exec_output=exec_output)

    api_key = os.environ.get("GPTLINUX5_API_KEY") or os.environ.get("OPENAI_API_KEY")
    api_url = os.environ.get("GPTLINUX5_API_URL") or DEFAULT_OPENAI_CHAT_COMPLETIONS
    if not api_key:
        print("No API key found in environment (GPTLINUX5_API_KEY or OPENAI_API_KEY). The CLI will print the prompt instead.")
        print("\n--- PROMPT ---\n")
        print(prompt)
        if exec_output:
            print("\n--- REAL EXECUTION OUTPUT ---\n")
            print(exec_output)
        sys.exit(0)

    try:
        print("Sending request to LLM endpoint...")
        response = call_openai_chat(api_url, api_key, args.model, prompt, timeout=args.web_timeout, temperature=args.temp)
    except Exception as e:
        print("Error calling API:", e, file=sys.stderr)
        print("\n--- PROMPT (debug) ---\n")
        print(prompt)
        sys.exit(1)

    if exec_output is not None:
        print("\n--- REAL EXECUTION OUTPUT ---\n")
        print(exec_output)
    print("\n--- LLM ANALYSIS / SUGGESTED OUTPUT ---\n")
    print(response)

if __name__ == "__main__":
    main()
