# Requirements: MVP, verification attestations in git

Phases 1 to 4 of `specs/roadmap.md`, on one branch, `mvp`, in this repository.
Target: a Python repository runs its checks in CI, the results land in git as
signed attestations, a policy file says what an agent-authored change must
carry, and `veridict verify` answers pass or fail from a clone.

## Scope

### In

- `veridict` Python package, `src/` layout, console script `veridict`.
- The attestation record and its DSSE envelope, below.
- Notes storage and sync, below.
- Python adapter: mypy, pytest, crosshair, selecting files the way
  `templates/veridict-spec-gate.yml` in the hackathon repository does.
- Signing: Ed25519 keys locally; Sigstore keyless in GitHub Actions through
  the optional `sigstore` extra.
- Policy file and evaluation, below.
- `veridict verify`: offline in key mode; network only for Sigstore material.
- Authorship: a `prepare-commit-msg` hook, trailer inference, and an
  authorship attestation.
- GitHub adapter: composite `action.yml`, a consumer workflow template, and
  a live run on `vayu-network/anonymous-review-demo`.
- CI for this repository: pytest on push and pull request.

### Out, with the phase that takes it

- SMT certificates, the rerun tier, evidence refs for large blobs: Phase 5.
- GitLab and the bare-remote hook: Phase 6.
- Evidence bundle export beyond a JSON dump, SLSA Source summary, named
  human-approval predicate: Phase 7.
- Anonymous approvals and the nullifier: Phase 8.
- Reuse of in-toto `test-result/v0.1`: revisit at Phase 7.

## The record

| Field | Value |
|---|---|
| `_type` | `https://in-toto.io/Statement/v1` |
| `subject[0].name` | Repository identity: the `origin` URL without scheme, credentials or `.git`; the directory name when there is no remote |
| `subject[0].digest` | `{"gitCommit": <40 hex>, "gitTree": <40 hex>}` |
| `predicateType` | `https://veridict.dev/verification/v1` or `https://veridict.dev/authorship/v1` |

Verification predicate:

| Field | Type | Meaning |
|---|---|---|
| `checker.name` | string | `mypy`, `pytest`, `crosshair` |
| `checker.version` | string | as reported by the tool |
| `tier` | string | `signed` in the MVP; `certificate` and `rerun` reserved |
| `result` | string | `pass`, `fail`, `skipped` |
| `scope.paths` | list | files the checker was given |
| `command` | string | exact command line |
| `environment.python` | string | interpreter version |
| `evidence.summary` | string | last meaningful line of tool output |
| `evidence.counterexamples` | list | crosshair only: `{location, call, message}` per finding |
| `startedAt`, `finishedAt` | string | RFC 3339, UTC |

Authorship predicate:

| Field | Type | Meaning |
|---|---|---|
| `authorClass` | string | `human`, `agent`, `assisted` |
| `agent.product`, `agent.model`, `agent.session` | string | optional |
| `source` | string | `hook`, `trailer`, `ci-inference` |
| `strength` | string | `strong` when produced at commit time from hook data; `weak` when inferred from trailers |

Envelope: DSSE with `payloadType` `application/vnd.in-toto+json`, the
statement as base64 payload, and `signatures[]` of `{keyid, sig}`. PAE per
the DSSE specification. `keyid` is `sha256:` plus the hex SHA-256 of the raw
32-byte Ed25519 public key. In Sigstore mode the envelope is inside a Sigstore
bundle and the bundle is stored whole.

Note line, one per attestation, compact JSON, no embedded newlines:

| Kind | Shape |
|---|---|
| key-signed | `{"v": 1, "kind": "dsse", "envelope": {...}}` |
| keyless | `{"v": 1, "kind": "sigstore", "bundle": {...}}` |

Refs:

| Ref | Use |
|---|---|
| `refs/notes/veridict` | Notes on the attested commit; lines appended; merge strategy `cat_sort_uniq` configured by the tool on first use |
| push | `git push <remote> refs/notes/veridict:refs/notes/veridict` |
| fetch | fetch into a temporary ref, then `git notes --ref=veridict merge` |

Policy, `.veridict/policy.toml`:

```toml
version = 1

[trust]
keys = ["sha256:<keyid>"]

[[trust.identities]]
issuer = "https://token.actions.githubusercontent.com"
identity = "https://github.com/OWNER/REPO/.github/workflows/veridict.yml@refs/heads/main"

[options]
allow_tree_match = false
unknown_author = "agent"

[[rule]]
name = "agent-written python"
paths = ["**/*.py"]
authors = ["agent", "assisted", "unknown"]
require = [
  { checker = "mypy", result = ["pass"] },
  { checker = "pytest", result = ["pass"] },
  { checker = "crosshair", result = ["pass", "skipped"] },
]
```

Semantics, per commit in the range:

1. Changed paths come from `git diff-tree`.
2. The author class is the strongest trusted authorship attestation on the
   commit; otherwise trailers (`Assisted-by:`, `Co-Authored-By:` naming a
   known agent) give `assisted` as weak evidence; otherwise `unknown`, which
   the policy maps through `options.unknown_author`.
3. Every rule whose `paths` match a changed path and whose `authors`
   include the class applies. Each requirement is met by at least one
   trusted verification attestation whose subject is this commit, or this
   commit's tree when `allow_tree_match` is true, with the named checker and
   a result in the allowed set.
4. If `.veridict/policy.toml` changed and no rule matches it, the commit
   fails. Fail closed.

CLI:

| Command | Effect |
|---|---|
| `veridict keygen [--out PATH]` | Ed25519 key, prints the keyid |
| `veridict attest --adapter python [--paths ...] [--sign key\|sigstore] [--key PATH] [--rev REV]` | Run the checkers, append one envelope per checker |
| `veridict authorship --class C [--agent PRODUCT] [--model M] [--sign ...]` | Append an authorship attestation for REV |
| `veridict verify REV[..REV] [--policy PATH] [--json]` | Evaluate the policy; exit 0 met, 1 not met, 2 error |
| `veridict show REV` | Human summary of attestations on REV |
| `veridict export REV` | All note lines for REV as a JSON array |
| `veridict push [REMOTE]`, `veridict fetch [REMOTE]` | Sync the notes ref |
| `veridict hook install` | Install the `prepare-commit-msg` hook |

## Decisions

- **One verification predicate for every checker**, not in-toto
  `test-result`. One shape keeps policy evaluation to a single matcher today;
  `test-result` reuse is revisited when export needs interoperability.
- **Evidence inline**, not under an evidence ref. Counterexamples are a few
  hundred bytes. Proof blobs arrive with SMT certificates in Phase 5.
- **TOML through `tomllib`**, not YAML. Zero new dependencies for policy.
- **Ed25519 keys plus optional Sigstore**, not Sigstore only. Tests and
  offline development need a signer with no network and no identity provider.
- **One note line per envelope with `cat_sort_uniq`**, not one document per
  commit. Appends from different machines merge without conflicts; the
  git-appraise precedent.
- **Subprocess `git`**, not dulwich or pygit2. No dependency, and behaviour
  identical to the user's git.
- **Unknown authorship maps to `agent`** by default. Fail closed toward the
  strict class.
- **Tree matching off by default.** Carrying evidence across a rebase is a
  policy choice a repository opts into.
- **Composite GitHub Action**, not a JavaScript action. Shell steps need no
  build and install the package from this repository at a pinned ref.
- **Package `veridict`, repository `veridict-core`.** PyPI publication is a
  follow-up; the action installs from git meanwhile.

## Context

**Trust boundaries.** Private keys never enter the repository; `keygen`
writes outside it and `.gitignore` excludes `*.pem`. In CI the signer is the
workflow's OIDC identity, and policy names it by issuer and identity. Verify
in key mode touches no network; in Sigstore mode it needs the Sigstore trust
root and log, cached after first use. The core never calls a forge API; only
`action.yml` knows about GitHub.

**Code to follow.** File selection and checker invocation mirror
`templates/veridict-spec-gate.yml` in `Zkred/veridict`: implementation files
are `*.py` minus `test_*`, `conftest`, `z3_*`; crosshair runs only when a
`pre:` or `post:` line exists; pytest runs only when test files exist.
crosshair 0.0.110 prints `PATH:LINE: error: false when calling CALL (which
returns VALUE)` and exits 1 on a counterexample, 0 when none. mypy exits 1 on
errors. pytest exits 5 when no tests are collected, which counts as
`skipped`.

**Demo repository.** `vayu-network/anonymous-review-demo`, public, default
branch `main`, modules `ring_buffer.py` and `backoff_scheduler.py` with
`post:` contracts in `ring_buffer.py`, tests, and `z3_*.py` property files.
It already runs `veridict-spec-gate.yml`; the new `veridict.yml` runs beside
it.

**Must not break.** Nothing in `Zkred/veridict` changes; its deployment is
untouched. The demo repository's existing gate keeps running.

**Open questions, resolved by the live run.** A notes push with `GITHUB_TOKEN`
needs only `contents: write`. Sigstore's ambient credential detection works
inside the composite action with `id-token: write`. Two things the run taught:

- **Verify races attest.** A push and its pull request fire at the same time,
  so the first verify saw no notes and failed. The action's verify mode now
  waits up to `wait-seconds` for attestations on the head commit.
- **Shared hooks paths.** `git rev-parse --git-path hooks` honours
  `core.hooksPath`; an early version of `hook install` wrote into a
  developer's global hooks directory. The installer now refuses a shared
  path unless `--shared` is given, and the tests ignore global git config.
