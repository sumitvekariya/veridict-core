"""Note lines: how one attestation is stored under refs/notes/veridict."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from .dsse import Envelope
from .gitrepo import Repo

NOTE_VERSION = 1


@dataclass
class NoteEntry:
    kind: str  # "dsse" or "sigstore"
    raw: dict[str, Any]

    @property
    def envelope(self) -> Envelope:
        if self.kind != "dsse":
            raise ValueError("not a key-signed entry")
        return Envelope.from_dict(self.raw["envelope"])

    @property
    def signer(self) -> dict[str, str]:
        return dict(self.raw.get("signer", {}))

    @property
    def bundle(self) -> dict[str, Any]:
        if self.kind != "sigstore":
            raise ValueError("not a Sigstore entry")
        return dict(self.raw["bundle"])


@dataclass
class ParsedNotes:
    entries: list[NoteEntry] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def wrap_dsse(envelope: Envelope, keyid: str, public_key_b64: str) -> str:
    return json.dumps(
        {
            "v": NOTE_VERSION,
            "kind": "dsse",
            "envelope": envelope.to_dict(),
            "signer": {"keyid": keyid, "publicKey": public_key_b64},
        },
        separators=(",", ":"),
        sort_keys=True,
    )


def wrap_bundle(bundle_json: str | dict[str, Any]) -> str:
    bundle = json.loads(bundle_json) if isinstance(bundle_json, str) else bundle_json
    return json.dumps(
        {"v": NOTE_VERSION, "kind": "sigstore", "bundle": bundle},
        separators=(",", ":"),
        sort_keys=True,
    )


def parse_lines(lines: list[str]) -> ParsedNotes:
    parsed = ParsedNotes()
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            parsed.warnings.append(f"line {i}: not JSON, ignored")
            continue
        if not isinstance(obj, dict) or obj.get("v") != NOTE_VERSION:
            parsed.warnings.append(f"line {i}: unknown note version, ignored")
            continue
        kind = obj.get("kind")
        if kind == "dsse" and isinstance(obj.get("envelope"), dict):
            parsed.entries.append(NoteEntry("dsse", obj))
        elif kind == "sigstore" and isinstance(obj.get("bundle"), dict):
            parsed.entries.append(NoteEntry("sigstore", obj))
        else:
            parsed.warnings.append(f"line {i}: unknown kind {kind!r}, ignored")
    return parsed


def read_entries(repo: Repo, commit: str) -> ParsedNotes:
    return parse_lines(repo.notes_read(commit))


def append_entry(repo: Repo, commit: str, line: str) -> None:
    repo.notes_append(commit, line)
