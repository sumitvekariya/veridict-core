"""Offline verification: signatures, subject binding, policy evaluation."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from . import AUTHORSHIP_PREDICATE, VERIFICATION_PREDICATE
from .authorship import resolve_author_class
from .dsse import verify as dsse_verify
from .gitrepo import Repo
from .keys import keyid as compute_keyid, public_from_b64
from .notes import NoteEntry, read_entries
from .policy import POLICY_PATH, Policy, tier_satisfies
from .statement import parse_statement, subject_matches


@dataclass
class Attestation:
    kind: str
    signer: str
    predicate_type: str
    predicate: dict[str, Any]
    statement: dict[str, Any]


@dataclass
class Finding:
    level: str  # error | warning | info
    message: str


@dataclass
class CommitReport:
    commit: str
    author_class: str = "unknown"
    author_source: str = "default"
    changed_paths: list[str] = field(default_factory=list)
    rules: list[str] = field(default_factory=list)
    satisfied: list[str] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(f.level == "error" for f in self.findings)


@dataclass
class Report:
    commits: list[CommitReport] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(c.ok for c in self.commits)

    def to_json(self) -> str:
        return json.dumps({"ok": self.ok, "commits": [
            {**asdict(c), "ok": c.ok} for c in self.commits]}, indent=2)

    def render(self) -> str:
        lines = []
        for c in self.commits:
            status = "PASS" if c.ok else "FAIL"
            lines.append(f"{status} {c.commit[:12]} author={c.author_class} ({c.author_source}) rules={','.join(c.rules) or '-'}")
            for s in c.satisfied:
                lines.append(f"   ok   {s}")
            for f in c.findings:
                lines.append(f"   {f.level:<5} {f.message}")
        lines.append("policy met" if self.ok else "policy NOT met")
        return "\n".join(lines)


def _authenticate(entry: NoteEntry, policy: Policy) -> tuple[bytes, str]:
    """Return (statement bytes, signer label) or raise ValueError."""
    if entry.kind == "dsse":
        signer = entry.signer
        pub_b64, claimed = signer.get("publicKey"), signer.get("keyid")
        if not pub_b64:
            raise ValueError("key-signed entry carries no public key")
        public = public_from_b64(pub_b64)
        kid = compute_keyid(public)
        if claimed and claimed != kid:
            raise ValueError("declared keyid does not match the public key")
        if kid not in policy.keys:
            raise ValueError(f"untrusted key {kid}")
        env = entry.envelope
        if not dsse_verify(env, {kid: public}):
            raise ValueError(f"signature by {kid} does not verify")
        return env.payload, kid
    if entry.kind == "sigstore":
        from . import sigstore_backend  # optional dependency, imported lazily

        return sigstore_backend.verify_entry(entry, policy.identities)
    raise ValueError(f"unknown entry kind {entry.kind}")


def collect(repo: Repo, commit: str, policy: Policy) -> tuple[list[Attestation], list[Finding]]:
    tree = repo.tree_of(commit)
    parsed = read_entries(repo, commit)
    findings = [Finding("warning", w) for w in parsed.warnings]
    attestations: list[Attestation] = []
    for i, entry in enumerate(parsed.entries, 1):
        try:
            payload, signer = _authenticate(entry, policy)
            statement = parse_statement(payload)
        except ValueError as exc:
            findings.append(Finding("warning", f"note {i}: rejected: {exc}"))
            continue
        if not subject_matches(statement, commit, tree, policy.allow_tree_match):
            findings.append(Finding("warning", f"note {i}: subject is another commit, ignored"))
            continue
        attestations.append(Attestation(entry.kind, signer, statement["predicateType"], statement["predicate"], statement))
    return attestations, findings


def evaluate(repo: Repo, policy: Policy, commit: str) -> CommitReport:
    report = CommitReport(commit=commit)
    attestations, findings = collect(repo, commit, policy)
    report.findings.extend(findings)
    report.changed_paths = repo.changed_paths(commit)

    authorship = [a.predicate for a in attestations if a.predicate_type == AUTHORSHIP_PREDICATE]
    report.author_class, report.author_source = resolve_author_class(authorship, repo.trailers(commit), policy.unknown_author)

    verifications = [a for a in attestations if a.predicate_type == VERIFICATION_PREDICATE]
    rules = policy.applicable_rules(report.changed_paths, report.author_class)
    report.rules = [r.name for r in rules]

    if POLICY_PATH in report.changed_paths and not policy.rules_for_path(POLICY_PATH):
        report.findings.append(Finding("error", f"{POLICY_PATH} changed and no rule covers it"))

    for rule in rules:
        for req in rule.require:
            match = next((v for v in verifications
                          if v.predicate.get("checker", {}).get("name") == req.checker
                          and v.predicate.get("result") in req.results
                          and tier_satisfies(str(v.predicate.get("tier", "signed")), req.tier)), None)
            if match is None:
                seen = [f"{v.predicate.get('checker', {}).get('name')}={v.predicate.get('result')}" for v in verifications]
                report.findings.append(Finding(
                    "error", f"rule '{rule.name}' needs {req.checker} in {list(req.results)}; have {seen or 'no verification attestations'}"))
            else:
                report.satisfied.append(f"{req.checker}={match.predicate.get('result')} by {match.signer}")
    return report


def verify_range(repo: Repo, spec: str, policy: Policy) -> Report:
    return Report([evaluate(repo, policy, c) for c in repo.commits_in(spec)])
