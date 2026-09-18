import json

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from veridict import AUTHORSHIP_PREDICATE, VERIFICATION_PREDICATE
from veridict.adapters.base import CheckResult
from veridict.attest import KeySigner, attest_authorship, attest_results
from veridict.authorship import authorship_predicate
from veridict.policy import parse
from veridict.verify import verify_range


def result(checker, outcome="pass"):
    return CheckResult(checker, "1", outcome, ["a.py"], checker, "ok", "t", "t")


def policy_for(signer, **options):
    return parse({
        "version": 1,
        "trust": {"keys": [signer.keyid]},
        "options": options,
        "rule": [{"name": "py", "paths": ["**/*.py"], "authors": ["agent", "assisted", "unknown"],
                  "require": [{"checker": "mypy"}, {"checker": "pytest", "result": ["pass", "skipped"]}]}],
    })


def test_met_policy_passes_and_reports(fixture_repo):
    commit = fixture_repo.commit({"a.py": "x = 1\n"})
    signer = KeySigner(Ed25519PrivateKey.generate())
    attest_results(fixture_repo.repo, "HEAD", [result("mypy"), result("pytest", "skipped")], signer)
    report = verify_range(fixture_repo.repo, "HEAD", policy_for(signer))
    assert report.ok, report.render()
    c = report.commits[0]
    assert c.commit == commit and c.author_class == "agent" and c.author_source == "default"
    assert any(s.startswith("mypy=pass") for s in c.satisfied)
    assert json.loads(report.to_json())["ok"] is True


def test_missing_checker_fails(fixture_repo):
    fixture_repo.commit({"a.py": "x = 1\n"})
    signer = KeySigner(Ed25519PrivateKey.generate())
    attest_results(fixture_repo.repo, "HEAD", [result("mypy")], signer)
    report = verify_range(fixture_repo.repo, "HEAD", policy_for(signer))
    assert not report.ok and "needs pytest" in report.render()


def test_tampered_note_fails(fixture_repo):
    commit = fixture_repo.commit({"a.py": "x = 1\n"})
    signer = KeySigner(Ed25519PrivateKey.generate())
    attest_results(fixture_repo.repo, "HEAD", [result("mypy"), result("pytest")], signer)
    lines = fixture_repo.repo.notes_read(commit)
    obj = json.loads(lines[0])
    payload = json.loads(__import__("base64").b64decode(obj["envelope"]["payload"]))
    payload["predicate"]["result"] = "pass" if payload["predicate"]["result"] != "pass" else "pass"
    payload["predicate"]["checker"]["name"] = "mypy"; payload["predicate"]["evidence"]["summary"] = "edited"
    obj["envelope"]["payload"] = __import__("base64").b64encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()).decode()
    fixture_repo._git("notes", "--ref=refs/notes/veridict", "add", "-f", "-F", "-", commit,
                      stdin="\n".join([json.dumps(obj, separators=(",", ":"), sort_keys=True), lines[1]]) + "\n")
    report = verify_range(fixture_repo.repo, "HEAD", policy_for(signer))
    assert not report.ok and "does not verify" in report.render()


def test_replayed_attestation_is_ignored(fixture_repo):
    first = fixture_repo.commit({"a.py": "x = 1\n"})
    signer = KeySigner(Ed25519PrivateKey.generate())
    attest_results(fixture_repo.repo, first, [result("mypy"), result("pytest")], signer)
    second = fixture_repo.commit({"a.py": "x = 2\n"})
    for line in fixture_repo.repo.notes_read(first):
        fixture_repo.repo.notes_append(second, line)
    report = verify_range(fixture_repo.repo, second, policy_for(signer))
    assert not report.ok and "another commit" in report.render()
    # Tree matching does not rescue it either: the tree changed.
    report = verify_range(fixture_repo.repo, second, policy_for(signer, allow_tree_match=True))
    assert not report.ok


def test_tree_match_carries_evidence_across_rebase_only_when_enabled(fixture_repo):
    root = fixture_repo.commit({"b.py": "y = 0\n"}, "root")
    first = fixture_repo.commit({"a.py": "x = 1\n"}, "feature")
    signer = KeySigner(Ed25519PrivateKey.generate())
    attest_results(fixture_repo.repo, first, [result("mypy"), result("pytest")], signer)
    # A rebase-like twin: same tree and same parent, different message, so a
    # different commit id with the same diff against its parent.
    tree = fixture_repo.repo.tree_of(first)
    twin = fixture_repo._git("commit-tree", tree, "-p", root, "-m", "feature (rebased)").strip()
    assert twin != first and fixture_repo.repo.changed_paths(twin) == ["a.py"]
    for line in fixture_repo.repo.notes_read(first):
        fixture_repo.repo.notes_append(twin, line)
    assert not verify_range(fixture_repo.repo, twin, policy_for(signer)).ok
    assert verify_range(fixture_repo.repo, twin, policy_for(signer, allow_tree_match=True)).ok


def test_untrusted_key_fails(fixture_repo):
    fixture_repo.commit({"a.py": "x = 1\n"})
    signer = KeySigner(Ed25519PrivateKey.generate())
    other = KeySigner(Ed25519PrivateKey.generate())
    attest_results(fixture_repo.repo, "HEAD", [result("mypy"), result("pytest")], signer)
    report = verify_range(fixture_repo.repo, "HEAD", policy_for(other))
    assert not report.ok and "untrusted key" in report.render()


def test_authorship_attestation_changes_class(fixture_repo):
    fixture_repo.commit({"a.py": "x = 1\n"})
    signer = KeySigner(Ed25519PrivateKey.generate())
    attest_authorship(fixture_repo.repo, "HEAD", authorship_predicate("human"), signer)
    report = verify_range(fixture_repo.repo, "HEAD", policy_for(signer))
    assert report.ok and report.commits[0].author_class == "human"


def test_policy_change_without_rule_fails(fixture_repo):
    fixture_repo.commit({".veridict/policy.toml": "version = 1\n"})
    signer = KeySigner(Ed25519PrivateKey.generate())
    report = verify_range(fixture_repo.repo, "HEAD", policy_for(signer))
    assert not report.ok and "no rule covers it" in report.render()


def test_range_evaluates_every_commit(fixture_repo):
    a = fixture_repo.commit({"a.py": "x = 1\n"})
    b = fixture_repo.commit({"a.py": "x = 2\n"})
    signer = KeySigner(Ed25519PrivateKey.generate())
    attest_results(fixture_repo.repo, b, [result("mypy"), result("pytest")], signer)
    report = verify_range(fixture_repo.repo, f"{a}..{b}", policy_for(signer))
    assert [c.commit for c in report.commits] == [b] and report.ok
