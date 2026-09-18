"""Python adapter: mypy, pytest and crosshair as signed-tier verdicts.

File selection mirrors the veridict-spec-gate workflow: implementation files
are tracked *.py minus tests, conftest and z3 property files; crosshair runs
only when a pre:/post: contract exists; pytest runs only when tests exist.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

from ..gitrepo import Repo
from .base import CheckResult, now_rfc3339

_TEST_FILE = re.compile(r"(^|/)(test_[^/]*\.py|[^/]*_test\.py|conftest\.py)$")
_Z3_FILE = re.compile(r"(^|/)z3_[^/]*\.py$|_z3\.py$")
_CONTRACT = re.compile(r"^\s*(pre|post):", re.MULTILINE)
_COUNTEREXAMPLE = re.compile(r"^(?P<location>.+?:\d+): error: (?P<message>.*?when calling (?P<call>.+?)(?: \(which .*\))?)$")

DEFAULT_TIMEOUT = 600
CHECKERS = ("mypy", "pytest", "crosshair")


def tracked_python_files(repo: Repo, paths: list[str] | None = None) -> list[str]:
    args = ["ls-files", "--", *(paths or ["*.py"])]
    files = [f for f in repo.run(*args).splitlines() if f.endswith(".py")]
    return sorted(set(files))


def implementation_files(files: list[str]) -> list[str]:
    return [f for f in files if not _TEST_FILE.search(f) and not _Z3_FILE.search(f)]


def test_files(files: list[str]) -> list[str]:
    return [f for f in files if _TEST_FILE.search(f) and not f.endswith("conftest.py")]


def has_contracts(repo: Repo, files: list[str]) -> bool:
    for f in files:
        try:
            text = (repo.root / f).read_text(errors="replace")
        except OSError:
            continue
        if _CONTRACT.search(text):
            return True
    return False


def _tool(name: str) -> list[str] | None:
    """Prefer the running interpreter's copy of a tool, then anything on PATH.

    The interpreter that runs veridict is the one whose site-packages hold the
    project under test; a different pytest on PATH would not import it.
    """
    module = {"mypy": "mypy", "pytest": "pytest", "crosshair": "crosshair"}[name]
    probe = subprocess.run([sys.executable, "-c", f"import {module}"], capture_output=True)
    if probe.returncode == 0:
        return [sys.executable, "-m", module]
    exe = shutil.which(name)
    return [exe] if exe else None


def _version(cmd: list[str], name: str) -> str:
    try:
        out = subprocess.run([*cmd, "--version"], capture_output=True, text=True, timeout=60)
        text = (out.stdout or out.stderr).strip().splitlines()
        return text[0] if text else "unknown"
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"


def _run(cmd: list[str], cwd: Path, timeout: int) -> tuple[int, str]:
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return 124, f"timed out after {timeout}s"
    return proc.returncode, (proc.stdout + proc.stderr)


def _summary(output: str) -> str:
    lines = [ln.strip() for ln in output.strip().splitlines() if ln.strip()]
    return lines[-1] if lines else ""


def _skipped(checker: str, paths: list[str], reason: str) -> CheckResult:
    t = now_rfc3339()
    return CheckResult(checker, "unknown", "skipped", paths, "", reason, t, t)


def run_mypy(repo: Repo, files: list[str], timeout: int = DEFAULT_TIMEOUT) -> CheckResult:
    if not files:
        return _skipped("mypy", files, "no implementation files")
    cmd = _tool("mypy")
    if cmd is None:
        return _skipped("mypy", files, "mypy not installed")
    full = [*cmd, "--ignore-missing-imports", *files]
    started = now_rfc3339()
    code, out = _run(full, repo.root, timeout)
    return CheckResult("mypy", _version(cmd, "mypy"), "pass" if code == 0 else "fail", files,
                       " ".join(["mypy", "--ignore-missing-imports", *files]), _summary(out), started, now_rfc3339())


def run_pytest(repo: Repo, tests: list[str], timeout: int = DEFAULT_TIMEOUT) -> CheckResult:
    if not tests:
        return _skipped("pytest", tests, "no tests present")
    cmd = _tool("pytest")
    if cmd is None:
        return _skipped("pytest", tests, "pytest not installed")
    full = [*cmd, "--tb=short", "-q", "-p", "no:cacheprovider", *tests]
    started = now_rfc3339()
    code, out = _run(full, repo.root, timeout)
    result = "pass" if code == 0 else "skipped" if code == 5 else "fail"
    return CheckResult("pytest", _version(cmd, "pytest"), result, tests,
                       " ".join(["pytest", "--tb=short", "-q", *tests]), _summary(out), started, now_rfc3339())


def run_crosshair(repo: Repo, files: list[str], timeout: int = DEFAULT_TIMEOUT, per_condition_timeout: int = 20) -> CheckResult:
    if not files:
        return _skipped("crosshair", files, "no implementation files")
    if not has_contracts(repo, files):
        return _skipped("crosshair", files, "no pre/post contracts declared")
    cmd = _tool("crosshair")
    if cmd is None:
        return _skipped("crosshair", files, "crosshair not installed")
    args = ["check", f"--per_condition_timeout={per_condition_timeout}", *files]
    started = now_rfc3339()
    code, out = _run([*cmd, *args], repo.root, timeout)
    counterexamples: list[dict[str, str]] = []
    for line in out.splitlines():
        m = _COUNTEREXAMPLE.match(line.strip())
        if m:
            location = m.group("location")
            root = str(repo.root) + "/"
            if location.startswith(root):
                location = location[len(root):]
            counterexamples.append({"location": location, "call": m.group("call"), "message": m.group("message")})
    result = "pass" if code == 0 else "fail"
    summary = _summary(out) if out.strip() else "no counterexamples found"
    return CheckResult("crosshair", _version(cmd, "crosshair"), result, files,
                       " ".join(["crosshair", *args]), summary, started, now_rfc3339(), counterexamples)


def run_all(repo: Repo, paths: list[str] | None = None, which: tuple[str, ...] = CHECKERS,
            timeout: int = DEFAULT_TIMEOUT) -> list[CheckResult]:
    files = tracked_python_files(repo, paths)
    impl, tests = implementation_files(files), test_files(files)
    results: list[CheckResult] = []
    if "mypy" in which:
        results.append(run_mypy(repo, impl, timeout))
    if "pytest" in which:
        results.append(run_pytest(repo, tests, timeout))
    if "crosshair" in which:
        results.append(run_crosshair(repo, impl, timeout))
    return results
