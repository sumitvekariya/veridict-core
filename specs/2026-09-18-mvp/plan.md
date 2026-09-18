# Plan: MVP, verification attestations in git

Task groups are independently implementable. Tests live in the group that
introduces the behaviour.

## Group 1: Scaffold

1. `pyproject.toml`, `src/veridict/__init__.py`, `.gitignore`, `LICENSE`,
   `README.md`: done at bootstrap.
2. `.github/workflows/ci.yml`: install with `pip install -e .[dev]`, run
   `pytest` on push and pull request.
3. `tests/conftest.py`: a `fixture_repo` helper that runs `git init`, sets
   identity, and commits given files, returning the path.

## Group 2: Record

4. `src/veridict/statement.py`: `repo_identity(repo)`, `subject_for(repo,
   rev)`, `build_statement(subject, predicate_type, predicate)`, canonical
   compact JSON encoding, `parse_statement(bytes)`.
5. `src/veridict/dsse.py`: `pae(payload_type, payload)`, `Envelope`
   dataclass with `to_json` and `from_json`, `sign_envelope(payload, key)`,
   `verify_envelope(envelope, public_keys) -> list[keyid]`.
6. `src/veridict/keys.py`: `generate(path)`, `load_private(path)`,
   `keyid(public_key)`, `public_from_keyid_store`.
7. `tests/test_dsse.py`: PAE golden vector from the DSSE spec, sign and
   verify round trip, tampered payload rejected, unknown key rejected.
   `tests/test_statement.py`: subject digests are the commit and tree, JSON
   is compact and stable.

## Group 3: Git plumbing and notes

8. `src/veridict/gitrepo.py`: `run(args)`, `rev_parse`, `tree_of`,
   `commits_in(range)`, `changed_paths(commit)`, `trailers(commit)`,
   `notes_read(commit) -> list[str]`, `notes_append(commit, line)`,
   `ensure_merge_strategy()`, `push_notes(remote)`, `fetch_notes(remote)`.
9. `src/veridict/notes.py`: `NoteLine` wrapper: `wrap_dsse`, `wrap_bundle`,
   `parse_lines`, ignoring malformed lines with a warning.
10. `tests/test_gitrepo.py`: append then read on a fixture repo, two appends
    yield two lines, `changed_paths` and `trailers` on a crafted commit,
    push and fetch between two local repositories merge without conflict.

## Group 4: Python adapter

11. `src/veridict/adapters/base.py`: `CheckResult` dataclass and the
    `to_predicate()` mapping.
12. `src/veridict/adapters/python_checks.py`: `select_files(repo, paths)`,
    `run_mypy`, `run_pytest`, `run_crosshair` with counterexample parsing,
    `run_all(repo, paths) -> list[CheckResult]`; tool versions captured;
    missing tools produce `skipped` with the reason in `evidence.summary`.
13. `tests/test_python_adapter.py`: fixture project with a violated
    postcondition yields a `fail` with one parsed counterexample; a correct
    project yields `pass`; a project without contracts yields `skipped` for
    crosshair; pytest with no tests yields `skipped`.

## Group 5: Authorship

14. `src/veridict/authorship.py`: `detect_agent_env()` (Claude Code,
    Codex, Cursor, Gemini CLI markers), `authorship_predicate(...)`,
    `class_from_trailers(trailers)`, `strongest_class(attestations,
    trailers, options)`.
15. `hooks/prepare-commit-msg`: adds `Assisted-by: <product>` when an agent
    session is detected and the trailer is absent.
16. `veridict hook install` copies the hook into `.git/hooks` without
    clobbering an existing hook.
17. `tests/test_authorship.py`: trailer parsing, env detection with
    monkeypatched environment, precedence of strong over weak.

## Group 6: Policy and verify

18. `src/veridict/policy.py`: `Policy` dataclass, `load(path)`, validation
    with clear errors, glob matching with `**`, `applicable_rules(paths,
    author_class)`.
19. `src/veridict/verify.py`: `collect(repo, commit) -> list[Attestation]`
    with signature verification per kind, `evaluate(policy, commit,
    attestations) -> CommitReport`, `verify_range(repo, range, policy) ->
    Report` with `ok`, per-commit findings, and JSON rendering.
20. `tests/test_verify.py`: met policy passes; missing checker fails;
    tampered payload fails; envelope replayed onto another commit fails;
    untrusted key fails; tree match honoured only when enabled; policy file
    change without a matching rule fails.

## Group 7: Sigstore backend

21. `src/veridict/sigstore_backend.py`: `available()`, `sign(statement)`
    using ambient credentials, `verify(bundle, identities) -> identity`,
    all imports guarded so key mode works without the extra.
22. `tests/test_sigstore_backend.py`: bundle wrapping and identity matching
    with a fake verifier; an integration test that runs only when
    `VERIDICT_SIGSTORE_IT=1`.

## Group 8: CLI

23. `src/veridict/cli.py`: argparse subcommands from the requirements
    table; `main(argv) -> int`; human and `--json` output for verify.
24. `tests/test_cli.py`: `keygen`, `attest`, `verify` end to end on a
    fixture repo through `main`; exit codes 0, 1 and 2.

## Group 9: GitHub adapter

25. `action.yml`: composite action with inputs `mode` (`attest` or
    `verify`), `policy`, `ref`; installs the package from this repository,
    runs attest with Sigstore and pushes notes, or fetches notes and runs
    verify, writing a step summary.
26. `templates/veridict.yml`: consumer workflow, attest on push and verify
    on pull request, with `id-token: write` and `contents: write`.
27. `templates/policy.toml`: the example from the requirements.
28. `README.md`: install, quick start, policy, action.

## Group 10: Live run

29. On `vayu-network/anonymous-review-demo`: add `.veridict/policy.toml`
    and `.github/workflows/veridict.yml`, push, observe the attest run and
    the notes ref, open or update a pull request, observe the verify check.
30. Record outcomes in `validation.md`; tick roadmap items.
