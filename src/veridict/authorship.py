"""Who or what wrote a change: environment detection, trailers, hook."""

from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Any, Mapping

from .gitrepo import Repo

# Environment markers set by agent sessions. Best effort; VERIDICT_AGENT wins.
AGENT_ENV_MARKERS: tuple[tuple[str, str], ...] = (
    ("VERIDICT_AGENT", ""),
    ("CLAUDECODE", "claude-code"),
    ("CLAUDE_CODE_ENTRYPOINT", "claude-code"),
    ("CODEX_SANDBOX", "codex"),
    ("CURSOR_AGENT", "cursor"),
    ("GEMINI_CLI", "gemini-cli"),
    ("AIDER_MODEL", "aider"),
)

KNOWN_AGENT_NAMES = ("claude", "copilot", "codex", "cursor", "gemini", "devin", "aider", "jules", "windsurf", "amazon q")

AUTHOR_CLASSES = ("human", "assisted", "agent")


def detect_agent_env(env: Mapping[str, str] | None = None) -> str | None:
    env = os.environ if env is None else env
    explicit = env.get("VERIDICT_AGENT")
    if explicit:
        return explicit
    for var, product in AGENT_ENV_MARKERS[1:]:
        if env.get(var):
            return product
    return None


def authorship_predicate(author_class: str, agent: str | None = None, model: str | None = None,
                         session: str | None = None, source: str = "hook", strength: str = "strong") -> dict[str, Any]:
    if author_class not in AUTHOR_CLASSES:
        raise ValueError(f"author class must be one of {AUTHOR_CLASSES}")
    predicate: dict[str, Any] = {"authorClass": author_class, "source": source, "strength": strength}
    agent_info = {k: v for k, v in (("product", agent), ("model", model), ("session", session)) if v}
    if agent_info:
        predicate["agent"] = agent_info
    return predicate


def class_from_trailers(trailers: list[tuple[str, str]]) -> tuple[str, str] | None:
    """Return (author_class, agent) inferred from trailers, or None."""
    for key, value in trailers:
        k = key.lower()
        if k == "assisted-by":
            return ("assisted", value.split("<")[0].strip())
        if k == "co-authored-by" and any(name in value.lower() for name in KNOWN_AGENT_NAMES):
            return ("assisted", value.split("<")[0].strip())
    return None


def resolve_author_class(attested: list[dict[str, Any]], trailers: list[tuple[str, str]], unknown_author: str) -> tuple[str, str]:
    """Strongest evidence wins: strong attestation, weak attestation, trailer, default."""
    for strength in ("strong", "weak"):
        for predicate in attested:
            if predicate.get("strength", "strong") == strength and predicate.get("authorClass") in AUTHOR_CLASSES:
                return str(predicate["authorClass"]), f"attestation:{strength}"
    inferred = class_from_trailers(trailers)
    if inferred:
        return inferred[0], "trailer"
    return unknown_author, "default"


HOOK_MARKER = "# veridict prepare-commit-msg hook"

HOOK_SCRIPT = f"""#!/bin/sh
{HOOK_MARKER}
# Adds an Assisted-by trailer when the commit is made from an agent session.
msgfile="$1"
product="${{VERIDICT_AGENT:-}}"
if [ -z "$product" ]; then
  if [ -n "${{CLAUDECODE:-}}" ] || [ -n "${{CLAUDE_CODE_ENTRYPOINT:-}}" ]; then product="claude-code";
  elif [ -n "${{CODEX_SANDBOX:-}}" ]; then product="codex";
  elif [ -n "${{CURSOR_AGENT:-}}" ]; then product="cursor";
  elif [ -n "${{GEMINI_CLI:-}}" ]; then product="gemini-cli";
  fi
fi
[ -z "$product" ] && exit 0
if grep -qi '^Assisted-by:' "$msgfile"; then exit 0; fi
git interpret-trailers --in-place --if-exists doNothing --trailer "Assisted-by: $product" "$msgfile"
exit 0
"""


def hooks_dirs(repo: Repo) -> tuple[Path, Path]:
    """Return (repository hooks dir, hooks dir git will actually use)."""
    git_dir = Path(repo.run("rev-parse", "--git-dir").strip())
    if not git_dir.is_absolute():
        git_dir = repo.root / git_dir
    local = (git_dir / "hooks").resolve()
    effective = Path(repo.run("rev-parse", "--git-path", "hooks").strip())
    if not effective.is_absolute():
        effective = repo.root / effective
    return local, effective.resolve()


def install_hook(repo: Repo, force: bool = False, allow_shared: bool = False) -> Path:
    """Install the prepare-commit-msg hook into this repository.

    Refuses to write into a shared hooks directory (core.hooksPath) unless
    allow_shared is set, because that would change every repository on the
    machine.
    """
    local, effective = hooks_dirs(repo)
    if effective != local and not allow_shared:
        raise PermissionError(
            f"git runs hooks from {effective} (core.hooksPath), not from this repository; "
            "pass --shared to install there for every repository, or unset core.hooksPath"
        )
    hooks_dir = effective if allow_shared else local
    hooks_dir.mkdir(parents=True, exist_ok=True)
    target = hooks_dir / "prepare-commit-msg"
    if target.exists() and HOOK_MARKER not in target.read_text() and not force:
        raise FileExistsError(f"{target} exists and is not a veridict hook; use --force to replace it")
    target.write_text(HOOK_SCRIPT)
    target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return target
