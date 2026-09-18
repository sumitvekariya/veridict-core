from __future__ import annotations

import subprocess
from pathlib import Path

import os

import pytest

from veridict.gitrepo import Repo

AGENT_MARKERS = ("VERIDICT_AGENT", "CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "CODEX_SANDBOX", "CURSOR_AGENT", "GEMINI_CLI", "AIDER_MODEL")


@pytest.fixture(autouse=True)
def isolated_git_environment(monkeypatch):
    """Ignore the developer's global git config and agent session markers.

    Without this, a global core.hooksPath or an agent environment variable
    would leak into fixture repositories and change what the tests observe.
    """
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    for var in AGENT_MARKERS:
        monkeypatch.delenv(var, raising=False)


class FixtureRepo:
    """A throwaway git repository with a helper to add commits."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self._git("init", "-q", "-b", "main")
        self._git("config", "user.name", "Fixture")
        self._git("config", "user.email", "fixture@example.invalid")
        self._git("config", "commit.gpgsign", "false")
        self.repo = Repo(root)

    def _git(self, *args: str, stdin: str | None = None) -> str:
        return subprocess.run(
            ["git", *args], cwd=self.root, check=True, text=True,
            capture_output=True, input=stdin,
        ).stdout

    def commit(self, files: dict[str, str], message: str = "change") -> str:
        for rel, content in files.items():
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            self._git("add", rel)
        self._git("commit", "-q", "--allow-empty", "-m", message)
        return self._git("rev-parse", "HEAD").strip()


@pytest.fixture
def fixture_repo(tmp_path: Path) -> FixtureRepo:
    return FixtureRepo(tmp_path / "repo")


@pytest.fixture
def make_repo(tmp_path: Path):
    """Factory for several fixture repositories in one test."""
    counter = {"n": 0}

    def _make(name: str | None = None) -> FixtureRepo:
        counter["n"] += 1
        return FixtureRepo(tmp_path / (name or f"repo{counter['n']}"))

    return _make
