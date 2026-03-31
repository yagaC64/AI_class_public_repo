#!/usr/bin/env python3
"""Cross-platform local operator launcher."""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HOST = os.environ.get("RICCE_HOST", "127.0.0.1")
PORT = int(os.environ.get("RICCE_PORT", "8000"))
LOCAL_DIR = REPO_ROOT / ".local"
PID_FILE = LOCAL_DIR / "http-server.pid"
LOG_FILE = LOCAL_DIR / "http-server.log"
MAX_LOG_BYTES = 2 * 1024 * 1024
SAMPLE_URL = f"http://{HOST}:{PORT}/"
PRIVATE_PREVIEW_URL = f"{SAMPLE_URL}?csv=/data/local/ricce-ontology-private-preview.csv"


def ensure_local_dir() -> None:
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)


def rotate_log_if_needed() -> None:
    ensure_local_dir()
    if LOG_FILE.exists() and LOG_FILE.stat().st_size >= MAX_LOG_BYTES:
        previous = LOG_FILE.with_suffix(".log.previous")
        if previous.exists():
            previous.unlink()
        LOG_FILE.rename(previous)


def process_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def server_pid() -> int | None:
    if not PID_FILE.exists():
        return None
    try:
        pid = int(PID_FILE.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        PID_FILE.unlink(missing_ok=True)
        return None

    if process_exists(pid):
        return pid

    PID_FILE.unlink(missing_ok=True)
    return None


def port_in_use() -> bool:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex((HOST, PORT)) == 0


def wait_for_http() -> bool:
    for _ in range(5):
        try:
            with urllib.request.urlopen(SAMPLE_URL, timeout=1):
                return True
        except (urllib.error.URLError, TimeoutError):
            time.sleep(1)
    return False


def open_url(url: str) -> None:
    if not webbrowser.open(url):
        print(f"Open this URL manually: {url}")


def run_command(args: list[str]) -> int:
    return subprocess.run(args, cwd=REPO_ROOT).returncode


def run_preflight() -> int:
    return run_command([sys.executable, str(REPO_ROOT / "scripts" / "security_checks.py")])


def build_private_preview() -> int:
    private_csv = REPO_ROOT / "data" / "private" / "ricce-ontology-master.csv"
    if not private_csv.exists():
        print("[FAIL] Missing data/private/ricce-ontology-master.csv", file=sys.stderr)
        return 1

    result = run_command([sys.executable, str(REPO_ROOT / "scripts" / "prepare_public_data.py")])
    if result != 0:
        return result

    result = run_preflight()
    if result != 0:
        return result

    print("\nLocal private-preview dataset is current and excluded from Firebase Hosting.")
    print("Preview CSV: public/data/local/ricce-ontology-private-preview.csv")
    print("Manifest: public/data/local/ricce-ontology-private-preview.manifest.json")
    return 0


def start_server() -> int:
    existing_pid = server_pid()
    if existing_pid is not None:
        print(f"Local server already running on {SAMPLE_URL} (PID {existing_pid}).")
        return 0

    if port_in_use():
        print(f"[FAIL] Port {PORT} is already in use. Set RICCE_PORT or stop the conflicting service.", file=sys.stderr)
        return 1

    rotate_log_if_needed()
    ensure_local_dir()
    LOG_FILE.write_text("", encoding="utf-8")

    with LOG_FILE.open("a", encoding="utf-8") as log_handle:
        popen_kwargs: dict[str, object] = {
            "cwd": REPO_ROOT,
            "stdout": log_handle,
            "stderr": subprocess.STDOUT,
        }
        if os.name == "nt":
            creationflags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            if creationflags:
                popen_kwargs["creationflags"] = creationflags
        else:
            popen_kwargs["start_new_session"] = True

        process = subprocess.Popen(
            [sys.executable, "-m", "http.server", str(PORT), "--bind", HOST, "--directory", "public"],
            **popen_kwargs,
        )

    PID_FILE.write_text(str(process.pid), encoding="utf-8")

    if wait_for_http():
        print(f"Local server is ready at {SAMPLE_URL}")
        return 0

    print(f"[FAIL] Local server did not become ready. Check {LOG_FILE}", file=sys.stderr)
    return 1


def stop_server() -> int:
    pid = server_pid()
    if pid is None:
        print("No local server is currently running.")
        return 0

    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass

        deadline = time.time() + 2
        while time.time() < deadline:
            if not process_exists(pid):
                break
            time.sleep(0.1)

        if process_exists(pid):
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass

    PID_FILE.unlink(missing_ok=True)
    print("Stopped local server.")
    return 0


def show_status() -> int:
    pid = server_pid()
    if pid is not None:
        print(f"Server: RUNNING (PID {pid})")
        print(f"Sample URL: {SAMPLE_URL}")
    else:
        print("Server: STOPPED")

    if (REPO_ROOT / "public" / "data" / "local" / "ricce-ontology-private-preview.csv").exists():
        print("Private preview CSV: READY")
        print(f"Private preview URL: {PRIVATE_PREVIEW_URL}")
    else:
        print("Private preview CSV: NOT BUILT")

    if LOG_FILE.exists():
        print(f"Server log: {LOG_FILE}")
    else:
        print("Server log: none yet")
    return 0


def show_log_tail() -> int:
    if not LOG_FILE.exists():
        print("No log file exists yet.")
        return 0

    lines = LOG_FILE.read_text(encoding="utf-8", errors="ignore").splitlines()
    for line in lines[-20:]:
        print(line)
    return 0


def ask_yes_no_quit(prompt: str, default: str = "Y") -> str:
    while True:
        try:
            reply = input(prompt)
        except EOFError:
            return "q"

        reply = (reply or default).strip()
        if reply.lower() in {"y", "n", "q"}:
            return reply.lower()
        print("Choose Y, n, or q.")


def start_sample_site() -> int:
    result = start_server()
    if result != 0:
        return result
    print(f"Open the public sample site at {SAMPLE_URL}")
    if ask_yes_no_quit("Open it in the browser now? (Y/n/q) ", "Y") == "y":
        open_url(SAMPLE_URL)
    return 0


def start_private_preview_site() -> int:
    result = build_private_preview()
    if result != 0:
        return result
    result = start_server()
    if result != 0:
        return result
    print(f"Open the local private preview at {PRIVATE_PREVIEW_URL}")
    if ask_yes_no_quit("Open it in the browser now? (Y/n/q) ", "Y") == "y":
        open_url(PRIVATE_PREVIEW_URL)
    return 0


def print_menu() -> None:
    print(
        """
RICCE operator menu
1. Run preflight security and readiness checks
2. Start local sample site
3. Build local private preview dataset
4. Start local private preview site
5. Show status
6. Stop local server
7. Show recent server log lines
q. Quit
"""
    )


def run_interactive() -> int:
    actions = {
        "1": run_preflight,
        "2": start_sample_site,
        "3": build_private_preview,
        "4": start_private_preview_site,
        "5": show_status,
        "6": stop_server,
        "7": show_log_tail,
    }

    while True:
        print_menu()
        try:
            choice = input("Choose an option: ").strip()
        except EOFError:
            return 0

        if choice.lower() == "q":
            return 0

        action = actions.get(choice)
        if action is None:
            print("Unknown option. Choose 1-7 or q.")
            continue

        result = action()
        if result != 0:
            return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        nargs="?",
        choices=["preflight", "sample", "build-private-preview", "private-preview", "status", "stop", "logs"],
        help="Run a single action instead of the interactive menu.",
    )
    return parser.parse_args()


def main() -> int:
    os.chdir(REPO_ROOT)
    args = parse_args()

    if not args.action:
        return run_interactive()

    action_map = {
        "preflight": run_preflight,
        "sample": start_sample_site,
        "build-private-preview": build_private_preview,
        "private-preview": start_private_preview_site,
        "status": show_status,
        "stop": stop_server,
        "logs": show_log_tail,
    }
    return action_map[args.action]()


if __name__ == "__main__":
    raise SystemExit(main())
