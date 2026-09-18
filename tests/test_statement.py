import json

import pytest

from veridict import STATEMENT_TYPE
from veridict.statement import (
    build_statement,
    encode_statement,
    normalize_remote,
    parse_statement,
    subject_for,
    subject_matches,
)


@pytest.mark.parametrize(
    "url,expected",
    [
        ("git@github.com:org/repo.git", "github.com/org/repo"),
        ("https://user:tok@github.com/org/repo.git", "github.com/org/repo"),
        ("ssh://git@github.com/org/repo", "github.com/org/repo"),
        ("https://gitlab.example.com:8443/group/sub/repo.git", "gitlab.example.com/group/sub/repo"),
    ],
)
def test_normalize_remote(url, expected):
    assert normalize_remote(url) == expected


def test_subject_has_commit_and_tree(fixture_repo):
    commit = fixture_repo.commit({"a.py": "x = 1\n"})
    subject = subject_for(fixture_repo.repo, "HEAD")
    assert subject["digest"]["gitCommit"] == commit
    assert len(subject["digest"]["gitTree"]) == 40
    assert subject["name"] == fixture_repo.root.name  # no remote configured


def test_statement_encoding_is_compact_and_stable():
    stmt = build_statement({"name": "n", "digest": {"gitCommit": "a" * 40}}, "https://veridict.dev/verification/v1", {"z": 1, "a": 2})
    raw = encode_statement(stmt)
    assert b"\n" not in raw and b": " not in raw
    assert raw == encode_statement(json.loads(raw))
    parsed = parse_statement(raw)
    assert parsed["_type"] == STATEMENT_TYPE


def test_parse_rejects_wrong_type():
    with pytest.raises(ValueError):
        parse_statement(b'{"_type":"nope","subject":[],"predicateType":"x","predicate":{}}')


def test_subject_matches_commit_or_tree_when_allowed():
    stmt = build_statement({"name": "n", "digest": {"gitCommit": "a" * 40, "gitTree": "b" * 40}}, "t", {})
    assert subject_matches(stmt, "a" * 40, "c" * 40)
    assert not subject_matches(stmt, "d" * 40, "b" * 40)
    assert subject_matches(stmt, "d" * 40, "b" * 40, allow_tree=True)
