"""Thin subprocess wrapper over git: revisions, diffs, trailers and notes."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from . import NOTES_REF

NOTES_NAME = NOTES_REF.rsplit("/", 1)[1]
INCOMING_REF = NOTES_REF + "-incoming"


class GitError(RuntimeError):
    pass


@dataclass(frozen=True)
class Repo:
    root: Path

    @classmethod
    def discover(cls, path: Path | None = None) -> "Repo":
        cwd = path or Path.cwd()
        out = _run(["git", "rev-parse", "--show-toplevel"], cwd=cwd)
        return cls(Path(out.strip()))

    def run(self, *args: str, stdin: str | None = None, check: bool = True) -> str:
        return _run(["git", *args], cwd=self.root, stdin=stdin, check=check)

    # revisions -----------------------------------------------------------

    def rev_parse(self, rev: str) -> str:
        return self.run("rev-parse", "--verify", f"{rev}^{{commit}}").strip()

    def tree_of(self, rev: str) -> str:
        return self.run("rev-parse", "--verify", f"{rev}^{{tree}}").strip()

    def head(self) -> str:
        return self.rev_parse("HEAD")

    def commits_in(self, spec: str) -> list[str]:
        if ".." in spec:
            out = self.run("rev-list", "--reverse", spec)
            return [line for line in out.split() if line]
        return [self.rev_parse(spec)]

    def parents(self, commit: str) -> list[str]:
        out = self.run("rev-list", "--parents", "-n", "1", commit).split()
        return out[1:]

    def changed_paths(self, commit: str) -> list[str]:
        parents = self.parents(commit)
        if not parents:
            out = self.run("ls-tree", "-r", "--name-only", commit)
        else:
            out = self.run("diff", "--name-only", parents[0], commit)
        return [line for line in out.splitlines() if line]

    def commit_message(self, commit: str) -> str:
        return self.run("log", "-1", "--format=%B", commit)

    def trailers(self, commit: str) -> list[tuple[str, str]]:
        message = self.commit_message(commit)
        out = self.run("interpret-trailers", "--parse", stdin=message)
        result: list[tuple[str, str]] = []
        for line in out.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            result.append((key.strip(), value.strip()))
        return result

    def remote_url(self, name: str = "origin") -> str | None:
        out = self.run("remote", "get-url", name, check=False)
        return out.strip() or None

    def ref_exists(self, ref: str) -> bool:
        proc = subprocess.run(
            ["git", "show-ref", "--verify", "--quiet", ref], cwd=self.root
        )
        return proc.returncode == 0

    # notes -----------------------------------------------------------------

    def notes_read(self, commit: str, ref: str = NOTES_REF) -> list[str]:
        proc = subprocess.run(
            ["git", "notes", f"--ref={ref}", "show", commit],
            cwd=self.root, text=True, capture_output=True,
        )
        if proc.returncode != 0:
            return []
        return [line for line in proc.stdout.splitlines() if line.strip()]

    def notes_append(self, commit: str, line: str, ref: str = NOTES_REF) -> None:
        if "\n" in line:
            raise ValueError("a note line must not contain newlines")
        existing = self.notes_read(commit, ref)
        content = "\n".join([*existing, line]) + "\n"
        self.run("notes", f"--ref={ref}", "add", "-f", "-F", "-", commit, stdin=content)
        self.ensure_merge_strategy()

    def ensure_merge_strategy(self) -> None:
        self.run("config", f"notes.{NOTES_NAME}.mergeStrategy", "cat_sort_uniq")

    def push_notes(self, remote: str = "origin") -> None:
        if not self.ref_exists(NOTES_REF):
            raise GitError("no local notes to push")
        self.fetch_notes(remote)
        self.run("push", remote, f"{NOTES_REF}:{NOTES_REF}")

    def fetch_notes(self, remote: str = "origin") -> bool:
        """Fetch the remote notes and merge them. Returns False if the remote has none."""
        proc = subprocess.run(
            ["git", "fetch", remote, f"+{NOTES_REF}:{INCOMING_REF}"],
            cwd=self.root, text=True, capture_output=True,
        )
        if proc.returncode != 0:
            return False
        if not self.ref_exists(NOTES_REF):
            self.run("update-ref", NOTES_REF, INCOMING_REF)
        else:
            self.run("notes", f"--ref={NOTES_REF}", "merge", "-s", "cat_sort_uniq", INCOMING_REF)
        self.run("update-ref", "-d", INCOMING_REF)
        return True


def _run(cmd: list[str], cwd: Path, stdin: str | None = None, check: bool = True) -> str:
    proc = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, input=stdin)
    if check and proc.returncode != 0:
        raise GitError(f"{' '.join(cmd)} failed ({proc.returncode}): {proc.stderr.strip()}")
    return proc.stdout
