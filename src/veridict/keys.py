"""Ed25519 key generation, loading and identifiers."""

from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


def keyid(public_key: Ed25519PublicKey) -> str:
    raw = public_key.public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def public_to_b64(public_key: Ed25519PublicKey) -> str:
    raw = public_key.public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    return base64.b64encode(raw).decode("ascii")


def public_from_b64(data: str) -> Ed25519PublicKey:
    raw = base64.b64decode(data, validate=True)
    if len(raw) != 32:
        raise ValueError("Ed25519 public key must be 32 bytes")
    return Ed25519PublicKey.from_public_bytes(raw)


def default_key_path() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "veridict" / "key.pem"


def generate(path: Path | None = None) -> tuple[str, Path]:
    """Write a new private key (PKCS8 PEM, mode 0600) and its public half."""
    path = path or default_key_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    private = Ed25519PrivateKey.generate()
    pem = private.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as fh:
        fh.write(pem)
    pub_pem = private.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    path.with_suffix(".pub").write_bytes(pub_pem)
    return keyid(private.public_key()), path


def load_private(path: Path | None = None) -> Ed25519PrivateKey:
    path = path or default_key_path()
    key = serialization.load_pem_private_key(path.read_bytes(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise ValueError(f"{path} is not an Ed25519 private key")
    return key


def load_public(path: Path) -> Ed25519PublicKey:
    key = serialization.load_pem_public_key(path.read_bytes())
    if not isinstance(key, Ed25519PublicKey):
        raise ValueError(f"{path} is not an Ed25519 public key")
    return key
