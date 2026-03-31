#!/usr/bin/env python3
"""Cross-platform repo safety and public-release checks."""

from __future__ import annotations

import csv
import json
import os
import re
import shutil
import socket
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = REPO_ROOT / "public"
GIT_EXCLUDE = REPO_ROOT / ".git" / "info" / "exclude"
PREPARE_PUBLIC_DATA = REPO_ROOT / "scripts" / "prepare_public_data.py"
EXAMPLE_CSV = REPO_ROOT / "public" / "data" / "ricce-ontology-sample.csv"
EXAMPLE_MANIFEST = REPO_ROOT / "public" / "data" / "ricce-ontology-sample.manifest.json"
LOCAL_PREVIEW_CSV = REPO_ROOT / "public" / "data" / "local" / "ricce-ontology-private-preview.csv"
RAW_TOOL_GLOBS = ("*.csv", "*.xml", "*.xls", "*.xlsx", "*.xlsm", "*.zip")
EXTERNAL_ASSET_PATTERN = re.compile(r"https://(unpkg|cdnjs|ajax\.googleapis|fonts\.googleapis|fonts\.gstatic)")
SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{35}|ghp_[A-Za-z0-9]{36}|-----BEGIN [A-Z ]*PRIVATE KEY-----)"
)


class CheckRunner:
    def __init__(self) -> None:
        self.failures = 0
        self.warnings = 0

    def pass_(self, message: str) -> None:
        print(f"[PASS] {message}")

    def warn(self, message: str) -> None:
        print(f"[WARN] {message}")
        self.warnings += 1

    def fail(self, message: str) -> None:
        print(f"[FAIL] {message}")
        self.failures += 1


def run_git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=check,
        text=True,
        capture_output=True,
    )


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def path_is_under(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def file_contains(path: Path, pattern: str) -> bool:
    if not path.exists():
        return False
    return pattern in read_text(path)


def any_public_text_matches(pattern: re.Pattern[str]) -> bool:
    for path in PUBLIC_DIR.rglob("*"):
        if not path.is_file():
            continue
        if "vendor" in path.parts:
            continue
        if path.suffix.lower() not in {".html", ".js", ".css"}:
            continue
        if pattern.search(read_text(path)):
            return True
    return False


def process_tracked(path_fragment: str) -> bool:
    tracked = run_git("ls-files", check=False)
    return any(line.strip() == path_fragment or line.strip().startswith(f"{path_fragment}/") for line in tracked.stdout.splitlines())


def port_is_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex((host, port)) == 0


def run_prepare_check_only(runner: CheckRunner) -> None:
    private_csv = REPO_ROOT / "data" / "private" / "ricce-ontology-master.csv"
    if not private_csv.exists():
        runner.warn("Private master CSV is missing. Source-side validation was skipped.")
        return

    result = subprocess.run(
        [sys.executable, str(PREPARE_PUBLIC_DATA), "--check-only"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    if result.returncode == 0:
        runner.pass_("Local preview pipeline validates the private master CSV.")
    else:
        runner.fail("Pipeline validation failed against the private master CSV.")


def validate_example_dataset(runner: CheckRunner) -> None:
    if not EXAMPLE_CSV.exists() or not EXAMPLE_MANIFEST.exists():
        runner.fail("Bundled example dataset validation failed.")
        return

    with EXAMPLE_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        expected = ["Name", "Organization", "Service Area"]
        rows = list(reader)
        if reader.fieldnames != expected or not rows:
            runner.fail("Bundled example dataset validation failed.")
            return

    email_pattern = re.compile(r"@")
    phone_pattern = re.compile(r"\d{3}[-.)\s]?\d{3}")
    for row in rows:
        serialized = " | ".join(row.values())
        if email_pattern.search(serialized) or phone_pattern.search(serialized):
            runner.fail("Bundled example dataset validation failed.")
            return

    manifest = json.loads(EXAMPLE_MANIFEST.read_text(encoding="utf-8"))
    if (
        manifest.get("dataset_profile") != "example"
        or manifest.get("contains_real_people") is not False
        or manifest.get("row_count") != len(rows)
    ):
        runner.fail("Bundled example dataset validation failed.")
        return

    runner.pass_("Bundled example dataset is shaped correctly and contains no obvious PII.")


def validate_secret_scan(runner: CheckRunner) -> None:
    ignored_dir_names = {".git", "node_modules", "__pycache__", ".firebase"}
    ignored_subpaths = {
        REPO_ROOT / "data" / "private",
        REPO_ROOT / "public" / "assets" / "vendor",
    }
    ignored_suffixes = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".woff", ".woff2"}

    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in ignored_dir_names for part in path.parts):
            continue
        if any(path_is_under(path, subpath) for subpath in ignored_subpaths):
            continue
        if path.suffix.lower() in ignored_suffixes:
            continue
        if path.name.endswith(".example"):
            continue

        try:
            contents = read_text(path)
        except OSError:
            continue
        if SECRET_PATTERN.search(contents):
            runner.fail("Potential secrets were detected in the repo.")
            return

    runner.pass_("No obvious committed secrets were detected in scoped files.")


def validate_history_warning(runner: CheckRunner) -> None:
    result = run_git(
        "rev-list",
        "-n",
        "1",
        "HEAD",
        "--",
        "data/private",
        "public/data/local",
        check=False,
    )
    if result.stdout.strip():
        runner.warn(
            "Sensitive or local-only paths exist in git history. Rewrite history or publish from a fresh sanitized repo before making the GitHub repo public."
        )
    else:
        runner.pass_("No sensitive or local-only paths were detected in git history.")


def main() -> int:
    os.chdir(REPO_ROOT)
    runner = CheckRunner()

    required_files = [
        "firebase.json",
        "config/public-data-pipeline.json",
        "public/index.html",
        "public/assets/js/site-config.js",
        "public/data/ricce-ontology-sample.csv",
        "public/data/ricce-ontology-sample.manifest.json",
        "public/tools/examples/grants-opportunities-sample.xml",
        "public/tools/examples/sam-contract-opportunities-sample.csv",
        "scripts/prepare_public_data.py",
        "scripts/publish_public_data.sh",
        "scripts/deploy_hosting_safe.sh",
        "scripts/install_git_hooks.sh",
        "scripts/preview_hosting_safe.sh",
        "scripts/set_firebase_project.sh",
        "scripts/run_menu.py",
        "scripts/security_checks.py",
        "run.sh",
        "run.ps1",
        ".githooks/pre-commit",
    ]

    for path_str in required_files:
        path = REPO_ROOT / path_str
        if path.is_file():
            runner.pass_(f"Found {path_str}")
        else:
            runner.fail(f"Missing {path_str}")

    if any_public_text_matches(EXTERNAL_ASSET_PATTERN):
        runner.fail("Public app still contains hot-linked external assets.")
    else:
        runner.pass_("Public app is using local vendored frontend assets.")

    if file_contains(REPO_ROOT / "firebase.json", '"Content-Security-Policy"'):
        runner.pass_("firebase.json defines a Content-Security-Policy header.")
    else:
        runner.fail("firebase.json is missing a Content-Security-Policy header.")

    if file_contains(REPO_ROOT / "firebase.json", '"data/local/**"'):
        runner.pass_("Firebase Hosting ignores local preview data.")
    else:
        runner.fail("Firebase Hosting does not ignore local preview data.")

    gitignore_text = read_text(REPO_ROOT / ".gitignore") if (REPO_ROOT / ".gitignore").exists() else ""
    if re.search(r"^\.env$", gitignore_text, re.MULTILINE) and re.search(r"^\.env\.\*$", gitignore_text, re.MULTILINE):
        runner.pass_(".env files are ignored by git.")
    else:
        runner.fail(".env files are not fully ignored.")

    if re.search(r"^data/private/$", gitignore_text, re.MULTILINE) and re.search(r"^data/raw/$", gitignore_text, re.MULTILINE):
        runner.pass_("Private and raw data folders are gitignored.")
    else:
        runner.fail("Private and raw data folders are not both gitignored.")

    if re.search(r"^public/data/local/$", gitignore_text, re.MULTILINE):
        runner.pass_("Local preview output is gitignored.")
    else:
        runner.fail("Local preview output is not gitignored.")

    if GIT_EXCLUDE.exists() and re.search(r"^\.local/$", read_text(GIT_EXCLUDE), re.MULTILINE):
        runner.pass_(".git/info/exclude keeps local run artifacts out of git status.")
    else:
        runner.warn(".git/info/exclude is missing the .local/ local-only rule.")

    public_data_root = REPO_ROOT / "public" / "data"
    unexpected_public_data = [
        path.name
        for path in public_data_root.glob("*")
        if path.is_file() and path.name not in {EXAMPLE_CSV.name, EXAMPLE_MANIFEST.name}
    ]
    if unexpected_public_data:
        runner.fail("Unexpected extra files exist directly under public/data/.")
    else:
        runner.pass_("Only approved sample files exist directly under public/data/.")

    raw_tool_extracts = []
    tools_dir = REPO_ROOT / "public" / "tools"
    for pattern in RAW_TOOL_GLOBS:
        raw_tool_extracts.extend(path for path in tools_dir.glob(pattern) if path.is_file())
    if raw_tool_extracts:
        runner.fail("Raw tool extracts are sitting directly under public/tools/.")
    else:
        runner.pass_("No raw tool extracts are sitting directly under public/tools/.")

    run_prepare_check_only(runner)
    validate_example_dataset(runner)

    if shutil.which("firebase"):
        runner.pass_("Firebase CLI is installed.")
    else:
        runner.warn("Firebase CLI is not installed.")

    for port in (4000, 5000, 5001, 8000, 8080, 8085, 9000):
        if port_is_open("127.0.0.1", port):
            runner.warn(f"Port {port} is already in use. Local preview may need a different port.")
        else:
            runner.pass_(f"Port {port} is available.")

    validate_secret_scan(runner)
    validate_history_warning(runner)

    print(f"\nSummary: {runner.failures} failure(s), {runner.warnings} warning(s)")
    return 1 if runner.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
