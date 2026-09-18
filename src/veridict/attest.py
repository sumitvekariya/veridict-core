"""Build, sign and store attestations."""

from __future__ import annotations

from typing import Any, Protocol

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from . import AUTHORSHIP_PREDICATE, VERIFICATION_PREDICATE
from .adapters.base import CheckResult
from .dsse import sign as dsse_sign
from .gitrepo import Repo
from .keys import keyid, public_to_b64
from .notes import append_entry, wrap_dsse
from .statement import build_statement, encode_statement, subject_for


class Signer(Protocol):
    name: str

    def sign(self, statement: bytes) -> str:
        """Return a note line for the signed statement."""


class KeySigner:
    name = "key"

    def __init__(self, private_key: Ed25519PrivateKey) -> None:
        self._key = private_key
        self.keyid = keyid(private_key.public_key())

    def sign(self, statement: bytes) -> str:
        env = dsse_sign(statement, self._key)
        return wrap_dsse(env, self.keyid, public_to_b64(self._key.public_key()))


def attest_predicates(repo: Repo, rev: str, predicates: list[tuple[str, dict[str, Any]]], signer: Signer) -> list[str]:
    """Sign one statement per (predicateType, predicate) and append them as notes."""
    commit = repo.rev_parse(rev)
    subject = subject_for(repo, commit)
    lines: list[str] = []
    for predicate_type, predicate in predicates:
        statement = encode_statement(build_statement(subject, predicate_type, predicate))
        line = signer.sign(statement)
        append_entry(repo, commit, line)
        lines.append(line)
    return lines


def attest_results(repo: Repo, rev: str, results: list[CheckResult], signer: Signer) -> list[str]:
    return attest_predicates(repo, rev, [(VERIFICATION_PREDICATE, r.to_predicate()) for r in results], signer)


def attest_authorship(repo: Repo, rev: str, predicate: dict[str, Any], signer: Signer) -> str:
    return attest_predicates(repo, rev, [(AUTHORSHIP_PREDICATE, predicate)], signer)[0]
