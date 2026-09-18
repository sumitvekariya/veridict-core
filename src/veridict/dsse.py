"""DSSE envelopes signed with Ed25519.

Spec: https://github.com/secure-systems-lab/dsse/blob/master/protocol.md
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from .keys import keyid as compute_keyid

PAYLOAD_TYPE = "application/vnd.in-toto+json"


def pae(payload_type: str, payload: bytes) -> bytes:
    """Pre-Authentication Encoding from the DSSE protocol."""
    pt = payload_type.encode("utf-8")
    return b"DSSEv1 %d %s %d %s" % (len(pt), pt, len(payload), payload)


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _unb64(data: str) -> bytes:
    return base64.b64decode(data, validate=True)


@dataclass
class Signature:
    keyid: str
    sig: bytes


@dataclass
class Envelope:
    payload_type: str
    payload: bytes
    signatures: list[Signature] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "payloadType": self.payload_type,
            "payload": _b64(self.payload),
            "signatures": [{"keyid": s.keyid, "sig": _b64(s.sig)} for s in self.signatures],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), separators=(",", ":"), sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict) -> "Envelope":
        try:
            sigs = [
                Signature(keyid=str(s.get("keyid", "")), sig=_unb64(s["sig"]))
                for s in data["signatures"]
            ]
            return cls(
                payload_type=str(data["payloadType"]),
                payload=_unb64(data["payload"]),
                signatures=sigs,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"malformed DSSE envelope: {exc}") from exc

    @classmethod
    def from_json(cls, raw: str | bytes) -> "Envelope":
        return cls.from_dict(json.loads(raw))


def sign(payload: bytes, private_key: Ed25519PrivateKey, payload_type: str = PAYLOAD_TYPE) -> Envelope:
    sig = private_key.sign(pae(payload_type, payload))
    return Envelope(
        payload_type=payload_type,
        payload=payload,
        signatures=[Signature(keyid=compute_keyid(private_key.public_key()), sig=sig)],
    )


def verify(envelope: Envelope, trusted: dict[str, Ed25519PublicKey]) -> list[str]:
    """Return the keyids of trusted keys whose signature verifies.

    Empty list means no trusted signature. Unknown keyids are ignored so a
    multi-signed envelope still verifies on the keys we do trust.
    """
    message = pae(envelope.payload_type, envelope.payload)
    good: list[str] = []
    for s in envelope.signatures:
        key = trusted.get(s.keyid)
        if key is None:
            continue
        try:
            key.verify(s.sig, message)
        except InvalidSignature:
            continue
        good.append(s.keyid)
    return good
