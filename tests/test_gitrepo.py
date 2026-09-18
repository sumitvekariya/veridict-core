import subprocess

from veridict import NOTES_REF
from veridict.gitrepo import Repo
from veridict.notes import parse_lines, wrap_bundle


def test_notes_append_then_read_twice(fixture_repo):
    commit = fixture_repo.commit({"a.py": "x = 1\n"})
    repo = fixture_repo.repo
    assert repo.notes_read(commit) == []
    repo.notes_append(commit, '{"v":1,"kind":"sigstore","bundle":{"n":1}}')
    repo.notes_append(commit, '{"v":1,"kind":"sigstore","bundle":{"n":2}}')
    lines = repo.notes_read(commit)
    assert len(lines) == 2
    parsed = parse_lines(lines)
    assert [e.bundle["n"] for e in parsed.entries] == [1, 2]
    assert parsed.warnings == []


def test_changed_paths_and_trailers(fixture_repo):
    fixture_repo.commit({"a.py": "x = 1\n", "b.py": "y = 2\n"}, "root")
    second = fixture_repo.commit({"b.py": "y = 3\n"}, "tweak\n\nAssisted-by: claude-code\nSigned-off-by: A <a@x>")
    repo = fixture_repo.repo
    root = repo.commits_in(f"{second}~1")[0]
    assert sorted(repo.changed_paths(root)) == ["a.py", "b.py"]
    assert repo.changed_paths(second) == ["b.py"]
    assert ("Assisted-by", "claude-code") in repo.trailers(second)
    assert repo.commits_in(f"{root}..{second}") == [second]


def test_push_and_fetch_merge_without_conflict(make_repo, tmp_path):
    bare = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
    a = make_repo("a")
    commit = a.commit({"a.py": "x = 1\n"})
    a._git("remote", "add", "origin", str(bare))
    a._git("push", "-q", "origin", "main")
    subprocess.run(["git", "clone", "-q", str(bare), str(tmp_path / "b")], check=True)
    b = Repo(tmp_path / "b")
    b.run("config", "user.name", "B"); b.run("config", "user.email", "b@example.invalid")

    a.repo.notes_append(commit, wrap_bundle({"from": "a"}))
    a.repo.push_notes("origin")
    b.notes_append(commit, wrap_bundle({"from": "b"}))
    b.push_notes("origin")  # fetches, merges with cat_sort_uniq, then pushes

    assert a.repo.fetch_notes("origin") is True
    froms = sorted(e.bundle["from"] for e in parse_lines(a.repo.notes_read(commit)).entries)
    assert froms == ["a", "b"]
    assert a.repo.ref_exists(NOTES_REF)
