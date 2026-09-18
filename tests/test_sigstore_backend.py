import os

import pytest

sigstore = pytest.importorskip("sigstore")

from veridict import sigstore_backend as sb
from veridict.policy import Identity


def test_identity_glob_matching():
    assert sb.identity_matches("https://github.com/o/r/.github/workflows/v.yml@refs/heads/*",
                               "https://github.com/o/r/.github/workflows/v.yml@refs/heads/main")
    assert not sb.identity_matches("https://github.com/o/r/*", "https://github.com/x/r/a")


def test_policy_for_exact_and_glob():
    from sigstore.verify import policy as sp
    exact = sb.policy_for(Identity(sb.GITHUB_ISSUER, "https://github.com/o/r/.github/workflows/v.yml@refs/heads/main"))
    assert isinstance(exact, sp.Identity)
    glob = sb.policy_for(Identity(sb.GITHUB_ISSUER, "https://github.com/o/r/.github/workflows/v.yml@refs/heads/*"))
    assert isinstance(glob, sp.AllOf)


def test_raw_statement_carries_git_digests():
    raw = b'{"_type":"https://in-toto.io/Statement/v1","predicate":{},"predicateType":"t","subject":[{"digest":{"gitCommit":"' + b"a" * 40 + b'"},"name":"n"}]}'
    st = sb._raw_statement(raw)
    assert st._contents == raw


def test_verify_entry_requires_identities():
    from veridict.notes import NoteEntry
    with pytest.raises(ValueError):
        sb.verify_entry(NoteEntry("sigstore", {"bundle": {}}), [])


@pytest.mark.skipif(not os.environ.get("VERIDICT_SIGSTORE_IT"), reason="needs an ambient OIDC credential")
def test_sign_and_verify_round_trip_with_ambient_identity():
    from veridict.notes import parse_lines
    signer = sb.SigstoreSigner()
    raw = b'{"_type":"https://in-toto.io/Statement/v1","predicate":{"a":1},"predicateType":"t","subject":[{"digest":{"gitCommit":"' + b"a" * 40 + b'"},"name":"n"}]}'
    line = signer.sign(raw)
    entry = parse_lines([line]).entries[0]
    ident = os.environ["VERIDICT_SIGSTORE_IDENTITY"]
    payload, label = sb.verify_entry(entry, [Identity(sb.GITHUB_ISSUER, ident)])
    assert payload == raw and label.startswith("sigstore:")
