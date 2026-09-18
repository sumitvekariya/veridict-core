"""in-toto Statement v1 construction and parsing.

Spec: https://github.com/in-toto/attestation/blob/main/spec/v1/statement.md
"""

from __future__ import annotations

import json
import re
from typing import Any

from . import STATEMENT_TYPE
from .gitrepo import Repo

_HEX40 = re.compile(r"^[0-9a-f]{40}$")


def canonical_json(obj: Any) -> bytes:
    return json.dumps(obj, separators=(",", ":"), sort_keys=True, ensure_ascii=False).encode("utf-8")


def normalize_remote(url: str) -> str:
    """Strip scheme, credentials and .git so the same repo has one name.

    git@github.com:org/repo.git        -> github.com/org/repo
    https://u:t@github.com/org/repo.git -> github.com/org/repo
    ssh://git@github.com/org/repo      -> github.com/org/repo
    """
    url = url.strip()
    scp = re.match(r"^(?:[^@/]+@)?([^:/]+):(?!//)(.+)$", url)
    if scp:
        host, path = scp.group(1), scp.group(2)
    else:
        m = re.match(r"^[a-z+]+://(?:[^@/]+@)?([^/:]+)(?::\d+)?/(.+)$", url)
        if not m:
            return url
        host, path = m.group(1), m.group(2)
    path = path.strip("/")
    if path.endswith(".git"):
        path = path[:-4]
    return f"{host}/{path}"


def repo_identity(repo: Repo) -> str:
    url = repo.remote_url("origin")
    if not url:
        return repo.root.name
    return normalize_remote(url)


def subject_for(repo: Repo, rev: str) -> dict[str, Any]:
    commit = repo.rev_parse(rev)
    tree = repo.tree_of(commit)
    return {"name": repo_identity(repo), "digest": {"gitCommit": commit, "gitTree": tree}}


def build_statement(subject: dict[str, Any], predicate_type: str, predicate: dict[str, Any]) -> dict[str, Any]:
    return {
        "_type": STATEMENT_TYPE,
        "subject": [subject],
        "predicateType": predicate_type,
        "predicate": predicate,
    }


def encode_statement(statement: dict[str, Any]) -> bytes:
    return canonical_json(statement)


def parse_statement(payload: bytes) -> dict[str, Any]:
    try:
        stmt = json.loads(payload)
    except ValueError as exc:
        raise ValueError(f"statement is not JSON: {exc}") from exc
    if not isinstance(stmt, dict) or stmt.get("_type") != STATEMENT_TYPE:
        raise ValueError("statement _type is not in-toto Statement v1")
    subjects = stmt.get("subject")
    if not isinstance(subjects, list) or not subjects:
        raise ValueError("statement has no subject")
    for s in subjects:
        if not isinstance(s, dict) or not isinstance(s.get("digest"), dict):
            raise ValueError("statement subject lacks a digest set")
    if not isinstance(stmt.get("predicateType"), str):
        raise ValueError("statement lacks predicateType")
    if not isinstance(stmt.get("predicate"), dict):
        raise ValueError("statement lacks predicate")
    return stmt


def subject_matches(statement: dict[str, Any], commit: str, tree: str, allow_tree: bool = False) -> bool:
    for s in statement["subject"]:
        digest = s.get("digest", {})
        if digest.get("gitCommit") == commit:
            return True
        if allow_tree and digest.get("gitTree") == tree:
            return True
    return False


def is_hex40(value: str) -> bool:
    return bool(_HEX40.match(value))
