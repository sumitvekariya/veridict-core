import subprocess

import pytest

from veridict import authorship as au


def test_detect_agent_env_prefers_explicit():
    assert au.detect_agent_env({"CLAUDECODE": "1"}) == "claude-code"
    assert au.detect_agent_env({"VERIDICT_AGENT": "codex", "CLAUDECODE": "1"}) == "codex"
    assert au.detect_agent_env({}) is None


def test_class_from_trailers():
    assert au.class_from_trailers([("Assisted-by", "claude-code")]) == ("assisted", "claude-code")
    assert au.class_from_trailers([("Co-Authored-By", "Claude <noreply@anthropic.com>")]) == ("assisted", "Claude")
    assert au.class_from_trailers([("Co-Authored-By", "Ada <ada@x>")]) is None


def test_resolution_precedence():
    strong = au.authorship_predicate("human", source="hook", strength="strong")
    weak = au.authorship_predicate("agent", source="ci-inference", strength="weak")
    assert au.resolve_author_class([weak, strong], [("Assisted-by", "x")], "agent") == ("human", "attestation:strong")
    assert au.resolve_author_class([weak], [], "agent") == ("agent", "attestation:weak")
    assert au.resolve_author_class([], [("Assisted-by", "x")], "agent") == ("assisted", "trailer")
    assert au.resolve_author_class([], [], "agent") == ("agent", "default")
    with pytest.raises(ValueError):
        au.authorship_predicate("robot")


def test_hook_refuses_shared_hooks_path(fixture_repo, tmp_path):
    fixture_repo.commit({"a.py": "x = 1\n"})
    shared = tmp_path / "shared-hooks"
    fixture_repo._git("config", "core.hooksPath", str(shared))
    with pytest.raises(PermissionError):
        au.install_hook(fixture_repo.repo)
    target = au.install_hook(fixture_repo.repo, allow_shared=True)
    assert target == (shared / "prepare-commit-msg").resolve()


def test_hook_install_and_effect(fixture_repo, monkeypatch):
    fixture_repo.commit({"a.py": "x = 1\n"})
    target = au.install_hook(fixture_repo.repo)
    assert target == (fixture_repo.root / ".git" / "hooks" / "prepare-commit-msg").resolve()
    assert target.exists() and target.stat().st_mode & 0o111
    # Idempotent for our own hook, refuses a foreign one without force.
    au.install_hook(fixture_repo.repo)
    target.write_text("#!/bin/sh\nexit 0\n")
    with pytest.raises(FileExistsError):
        au.install_hook(fixture_repo.repo)
    au.install_hook(fixture_repo.repo, force=True)

    env = {"PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin", "HOME": str(fixture_repo.root), "CLAUDECODE": "1",
           "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_AUTHOR_NAME": "F", "GIT_AUTHOR_EMAIL": "f@x", "GIT_COMMITTER_NAME": "F", "GIT_COMMITTER_EMAIL": "f@x"}
    (fixture_repo.root / "b.py").write_text("y = 2\n")
    subprocess.run(["git", "add", "b.py"], cwd=fixture_repo.root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "agent change"], cwd=fixture_repo.root, check=True, env=env)
    assert ("Assisted-by", "claude-code") in fixture_repo.repo.trailers("HEAD")

    env.pop("CLAUDECODE")
    (fixture_repo.root / "c.py").write_text("z = 3\n")
    subprocess.run(["git", "add", "c.py"], cwd=fixture_repo.root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "human change"], cwd=fixture_repo.root, check=True, env=env)
    assert fixture_repo.repo.trailers("HEAD") == []
