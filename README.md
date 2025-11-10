```markdown
# GPT Linux 5

GPT Linux 5 is a Kali-compatible command-line tool and optional system daemon that analyzes shell commands and scripts using a web-backed LLM (OpenAI-compatible or custom endpoint). It can optionally execute commands locally (with sandboxing support) and include the real output when asking the LLM for analysis.

This repository includes:
- CLI: src/gptlinux5.py
- Daemon: src/gptlinux5d.py (simple HTTP token-auth API)
- Docker sandbox: docker/
- Firejail/unshare sandbox wrapper: sandbox/
- Tests: tests/
- Debian packaging: debian/
- GitHub Actions CI: .github/workflows/ci.yml

Security notice
- Do not send secrets or sensitive data to remote LLM endpoints.
- Executing arbitrary commands is dangerous. Use sandboxing (Docker, Firejail, unshare) and run only trusted code.
- If you shared any credentials (PAT, API keys) publicly, revoke them immediately.

Quick usage examples
- CLI help:
  ./src/gptlinux5.py --help

- Analyze a command without executing:
  ./src/gptlinux5.py --cmd "nmap -sS -p1-65535 10.0.0.5"

- Analyze a script file:
  ./src/gptlinux5.py --script ./myscript.sh

- Execute in Docker sandbox:
  ./src/gptlinux5.py --cmd "uname -a" --exec --docker

Daemon mode (gptlinux5d)
- The daemon runs an HTTP endpoint (default listening on a Unix socket or localhost if configured).
- Auth: token passed in header `Authorization: Bearer <TOKEN>`.
- Configure environment variables:
  - GPTLINUX5_API_URL, GPTLINUX5_API_KEY (for LLM access)
  - GPTLINUX5_DAEMON_TOKEN (token for HTTP API)
  - GPTLINUX5_DAEMON_SOCKET (optional unix socket path)
  - GPTLINUX5_DAEMON_HOST / PORT (optional TCP)

Building the Debian package
- Ensure dependencies: dpkg-deb, debhelper, python3, python3-requests
- Run:
  chmod +x build_deb.sh
  ./build_deb.sh
- Install:
  sudo dpkg -i gptlinux5_1.0-1_all.deb

CI
- GitHub Actions workflow will lint (flake8), run pytest, and build the .deb.

If you'd like, I can:
- Provide exact git commands to push this repo to GitHub.
- Produce an alternative daemon auth (unix-socket + peer credentials).
- Help create a new PAT securely (walkthrough) and push the repo for you.
```
