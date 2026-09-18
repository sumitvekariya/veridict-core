"""Keyless signing and verification through Sigstore (optional extra).

The in-toto spec allows gitCommit and gitTree digests; sigstore-python's
Statement validator only accepts SHA-2 and SHA-3 keys. Its signer and verifier
operate on the raw statement bytes, so a subclass that skips that validation
produces a fully standard DSSE bundle.
"""

from __future__ import annotations

import fnmatch
import json
from typing import Any

from .notes import NoteEntry, wrap_bundle
from .policy import Identity

PAYLOAD_TYPE = "application/vnd.in-toto+json"
GITHUB_ISSUER = "https://token.actions.githubusercontent.com"


class SigstoreUnavailable(RuntimeError):
    pass


def available() -> bool:
    try:
        import sigstore  # noqa: F401
    except ImportError:
        return False
    return True


def _require() -> None:
    if not available():
        raise SigstoreUnavailable("install the sigstore extra: pip install 'veridict[sigstore]'")


def _raw_statement(contents: bytes) -> Any:
    from sigstore import dsse

    class _RawStatement(dsse.Statement):
        def __init__(self, raw: bytes) -> None:  # bypass digest-key validation
            self._contents = raw
            self._inner = None  # type: ignore[assignment]

    return _RawStatement(contents)


class SigstoreSigner:
    name = "sigstore"

    def __init__(self, identity_token: str | None = None, staging: bool = False) -> None:
        _require()
        from sigstore.models import ClientTrustConfig
        from sigstore.oidc import IdentityToken, detect_credential
        from sigstore.sign import SigningContext

        token = identity_token or detect_credential()
        if not token:
            raise SigstoreUnavailable(
                "no ambient OIDC credential; run inside CI with id-token permission or pass --identity-token"
            )
        self._token = IdentityToken(token)
        config = ClientTrustConfig.staging() if staging else ClientTrustConfig.production()
        self._context = SigningContext.from_trust_config(config)
        self.identity = getattr(self._token, "identity", None) or "sigstore"

    def sign(self, statement: bytes) -> str:
        with self._context.signer(self._token) as signer:
            bundle = signer.sign_dsse(_raw_statement(statement))
        return wrap_bundle(bundle.to_json())


def identity_matches(pattern: str, value: str) -> bool:
    return fnmatch.fnmatchcase(value, pattern)


def _san_values(cert: Any) -> list[str]:
    from cryptography import x509

    try:
        san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
    except x509.ExtensionNotFound:
        return []
    values: list[str] = []
    values += san.get_values_for_type(x509.UniformResourceIdentifier)
    values += san.get_values_for_type(x509.RFC822Name)
    return values


def policy_for(identity: Identity) -> Any:
    """Exact identities use Sigstore's own policy; globs use a SAN matcher."""
    from sigstore.errors import VerificationError
    from sigstore.verify import policy as sp

    if not any(ch in identity.identity for ch in "*?["):
        return sp.Identity(identity=identity.identity, issuer=identity.issuer)

    class _SanGlob(sp.VerificationPolicy):  # type: ignore[misc]
        def verify(self, cert: Any) -> None:
            values = _san_values(cert)
            if not any(identity_matches(identity.identity, v) for v in values):
                raise VerificationError(f"certificate identity {values} does not match {identity.identity}")

    return sp.AllOf([sp.OIDCIssuer(identity.issuer), _SanGlob()])


def certificate_identity(bundle: Any) -> str:
    values = _san_values(bundle.signing_certificate)
    return values[0] if values else "unknown"


def verify_entry(entry: NoteEntry, identities: list[Identity], offline: bool = False, staging: bool = False) -> tuple[bytes, str]:
    """Return (statement bytes, signer label) or raise ValueError."""
    _require()
    from sigstore.errors import VerificationError
    from sigstore.models import Bundle
    from sigstore.verify import Verifier

    if not identities:
        raise ValueError("policy trusts no Sigstore identities")
    try:
        bundle = Bundle.from_json(json.dumps(entry.bundle))
    except Exception as exc:  # sigstore raises its own hierarchy
        raise ValueError(f"malformed Sigstore bundle: {exc}") from exc
    verifier = Verifier.staging(offline=offline) if staging else Verifier.production(offline=offline)
    errors: list[str] = []
    for identity in identities:
        try:
            payload_type, payload = verifier.verify_dsse(bundle, policy_for(identity))
        except VerificationError as exc:
            errors.append(str(exc))
            continue
        if payload_type != PAYLOAD_TYPE:
            raise ValueError(f"unexpected DSSE payload type {payload_type}")
        return payload, f"sigstore:{certificate_identity(bundle)}"
    raise ValueError("no trusted Sigstore identity verified the bundle: " + "; ".join(errors[-1:]))
