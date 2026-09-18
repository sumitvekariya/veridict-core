import pytest

from veridict import policy as pol

SAMPLE = """
version = 1
[trust]
keys = ["sha256:abc"]
[[trust.identities]]
issuer = "https://token.actions.githubusercontent.com"
identity = "https://github.com/o/r/.github/workflows/veridict.yml@refs/heads/main"
[options]
allow_tree_match = true
unknown_author = "agent"
[[rule]]
name = "py"
paths = ["**/*.py"]
authors = ["agent", "assisted"]
require = [ { checker = "mypy" }, { checker = "crosshair", result = ["pass", "skipped"] } ]
[[rule]]
name = "docs"
paths = ["docs/**"]
authors = ["human"]
require = []
"""


def test_parse_and_applicable_rules(tmp_path):
    p = tmp_path / "policy.toml"; p.write_text(SAMPLE)
    policy = pol.load(p)
    assert policy.keys == {"sha256:abc"} and policy.allow_tree_match is True
    assert policy.identities[0].identity.endswith("@refs/heads/main")
    assert [r.name for r in policy.applicable_rules(["src/a.py"], "agent")] == ["py"]
    assert policy.applicable_rules(["src/a.py"], "human") == []
    assert [r.name for r in policy.applicable_rules(["docs/x.md"], "human")] == ["docs"]
    req = policy.rules[0].require[1]
    assert req.results == ("pass", "skipped") and req.tier == "signed"


@pytest.mark.parametrize("pattern,path,expected", [
    ("**/*.py", "a.py", True), ("**/*.py", "x/y/a.py", True), ("*.py", "x/a.py", False),
    ("src/**", "src/a/b.c", True), ("src/**", "lib/a", False), ("docs/*.md", "docs/a.md", True),
    (".veridict/policy.toml", ".veridict/policy.toml", True),
])
def test_glob(pattern, path, expected):
    assert pol.path_matches(pattern, path) is expected


def test_validation_errors(tmp_path):
    p = tmp_path / "policy.toml"
    p.write_text("version = 2\n")
    with pytest.raises(pol.PolicyError):
        pol.load(p)
    p.write_text('version = 1\n[[rule]]\nrequire = [ { checker = "x", tier = "magic" } ]\n')
    with pytest.raises(pol.PolicyError):
        pol.load(p)
    with pytest.raises(pol.PolicyError):
        pol.load(tmp_path / "missing.toml")


def test_tiers():
    assert pol.tier_satisfies("certificate", "signed") and not pol.tier_satisfies("signed", "certificate")
