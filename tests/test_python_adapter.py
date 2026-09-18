import pytest

from veridict.adapters import python_checks as pc

BAD = '''
def consume(tokens: int, n: int) -> bool:
    """
    pre: tokens >= 0 and n >= 0
    post: __return__ == (tokens >= n)
    """
    return tokens >= n - 1
'''
GOOD = BAD.replace("tokens >= n - 1", "tokens >= n")
PLAIN = "def f(x: int) -> int:\n    return x + 1\n"
TEST = "from mod import f\n\ndef test_f():\n    assert f(1) == 2\n"


def test_counterexample_is_parsed(fixture_repo):
    fixture_repo.commit({"bucket.py": BAD})
    r = pc.run_crosshair(fixture_repo.repo, ["bucket.py"], per_condition_timeout=10)
    assert r.result == "fail"
    assert len(r.counterexamples) == 1
    assert r.counterexamples[0]["call"].startswith("consume(")
    assert r.counterexamples[0]["location"].startswith("bucket.py:")
    pred = r.to_predicate()
    assert pred["checker"]["name"] == "crosshair" and pred["tier"] == "signed"
    assert pred["evidence"]["counterexamples"] == r.counterexamples


def test_correct_contracts_pass(fixture_repo):
    fixture_repo.commit({"bucket.py": GOOD})
    r = pc.run_crosshair(fixture_repo.repo, ["bucket.py"], per_condition_timeout=10)
    assert r.result == "pass" and r.counterexamples == []


def test_no_contracts_is_skipped(fixture_repo):
    fixture_repo.commit({"mod.py": PLAIN})
    r = pc.run_crosshair(fixture_repo.repo, ["mod.py"])
    assert r.result == "skipped" and "no pre/post" in r.summary


def test_run_all_selection_and_pytest_states(fixture_repo):
    fixture_repo.commit({"mod.py": PLAIN, "z3_mod.py": "x = 1\n"})
    results = {r.checker: r for r in pc.run_all(fixture_repo.repo)}
    assert results["mypy"].result == "pass" and results["mypy"].paths == ["mod.py"]
    assert results["pytest"].result == "skipped"
    assert results["crosshair"].result == "skipped"
    fixture_repo.commit({"test_mod.py": TEST})
    results = {r.checker: r for r in pc.run_all(fixture_repo.repo)}
    assert results["pytest"].result == "pass" and results["pytest"].paths == ["test_mod.py"]


def test_mypy_failure(fixture_repo):
    fixture_repo.commit({"mod.py": "def f(x: int) -> str:\n    return x\n"})
    r = pc.run_mypy(fixture_repo.repo, ["mod.py"])
    assert r.result == "fail" and "error" in r.summary
