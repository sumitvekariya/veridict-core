from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from veridict import dsse
from veridict.keys import keyid


def test_pae_matches_spec_golden_vector():
    # From the DSSE protocol document.
    assert dsse.pae("http://example.com/HelloWorld", b"hello world") == (
        b"DSSEv1 29 http://example.com/HelloWorld 11 hello world"
    )


def test_sign_and_verify_round_trip():
    key = Ed25519PrivateKey.generate()
    env = dsse.sign(b'{"a":1}', key)
    kid = keyid(key.public_key())
    assert env.signatures[0].keyid == kid
    assert dsse.verify(env, {kid: key.public_key()}) == [kid]
    # JSON round trip preserves verification.
    again = dsse.Envelope.from_json(env.to_json())
    assert dsse.verify(again, {kid: key.public_key()}) == [kid]


def test_tampered_payload_is_rejected():
    key = Ed25519PrivateKey.generate()
    env = dsse.sign(b'{"a":1}', key)
    env.payload = b'{"a":2}'
    assert dsse.verify(env, {keyid(key.public_key()): key.public_key()}) == []


def test_unknown_key_is_not_trusted():
    signer = Ed25519PrivateKey.generate()
    other = Ed25519PrivateKey.generate()
    env = dsse.sign(b"x", signer)
    assert dsse.verify(env, {keyid(other.public_key()): other.public_key()}) == []


def test_malformed_envelope_raises():
    import pytest
    with pytest.raises(ValueError):
        dsse.Envelope.from_dict({"payloadType": "t"})
