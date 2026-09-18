from veridict.cli import main


def test_keygen_attest_verify_end_to_end(fixture_repo, tmp_path, capsys):
    fixture_repo.commit({"mod.py": "def f(x: int) -> int:\n    return x + 1\n"})
    key = tmp_path / "k.pem"
    assert main(["keygen", "--out", str(key)]) == 0
    kid = [ln.split()[1] for ln in capsys.readouterr().out.splitlines() if ln.startswith("keyid ")][0]
    repo = str(fixture_repo.root)
    assert main(["--repo", repo, "attest", "--key", str(key), "--only", "mypy,pytest"]) == 0
    out = capsys.readouterr().out
    assert "mypy       pass" in out and "2 attestation(s) appended" in out

    policy = fixture_repo.root / ".veridict" / "policy.toml"
    policy.parent.mkdir()
    policy.write_text(f'version = 1\n[trust]\nkeys = ["{kid}"]\n[[rule]]\nname = "py"\npaths = ["**/*.py"]\n'
                      'require = [ {{ checker = "mypy" }}, {{ checker = "pytest", result = ["pass", "skipped"] }} ]\n'.replace("{{", "{").replace("}}", "}"))
    assert main(["--repo", repo, "verify", "HEAD"]) == 0
    assert "policy met" in capsys.readouterr().out
    assert main(["--repo", repo, "show", "HEAD"]) == 0
    assert "verification mypy=pass" in capsys.readouterr().out

    policy.write_text(policy.read_text().replace('{ checker = "mypy" }', '{ checker = "mypy" }, { checker = "crosshair" }'))
    assert main(["--repo", repo, "verify", "HEAD", "--json"]) == 1
    assert main(["--repo", repo, "verify", "HEAD", "--policy", str(tmp_path / "missing.toml")]) == 2
    assert main(["--repo", repo, "attest", "--key", str(tmp_path / "nokey.pem")]) == 2


def test_authorship_infer_and_hook(fixture_repo, tmp_path, capsys):
    fixture_repo.commit({"a.py": "x = 1\n"}, "change\n\nAssisted-by: claude-code")
    key = tmp_path / "k.pem"
    assert main(["keygen", "--out", str(key)]) == 0
    repo = str(fixture_repo.root)
    assert main(["--repo", repo, "authorship", "--infer", "--key", str(key)]) == 0
    assert "authorship assisted (ci-inference, weak)" in capsys.readouterr().out
    assert main(["--repo", repo, "hook", "install"]) == 0
