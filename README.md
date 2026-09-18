# Veridict

**Verification evidence for AI-written code, stored in git.**

Every check a repository runs becomes a signed attestation bound to the
commit, kept in a git notes ref, demanded by a policy file, and verifiable
from any clone with no forge involved. A model reviewing a pull request is
judgment; this is evidence.

```
$ veridict verify main..feature
PASS 3f2a9c1e0b7d author=assisted (trailer) rules=agent-written python
   ok   mypy=pass by sigstore:https://github.com/acme/api/.github/workflows/veridict.yml@refs/heads/feature
   ok   pytest=pass by sigstore:https://github.com/acme/api/.github/workflows/veridict.yml@refs/heads/feature
   ok   crosshair=pass by sigstore:https://github.com/acme/api/.github/workflows/veridict.yml@refs/heads/feature
policy met
```

## Why

About half of committed code is now written by models, its security pass
rate has not moved in a year, and agents produce more change than humans can
read. Attackers forge CI identities and replace tags at the source layer.
Regulators and auditors ask for provenance and evidence of checks. All three
pressures land on the same object, the commit. Veridict records, on the
commit, what was verified, by what, who or what authored the change, and who
vouched. See [`specs/mission.md`](specs/mission.md).

## How it works

1. **Attest.** In CI, `veridict attest` runs the checkers the repository
   already uses (mypy, pytest, crosshair for Python today) and turns each
   verdict into an [in-toto](https://in-toto.io) statement whose subject is
   the commit and its tree. The statement is wrapped in a DSSE envelope and
   signed, keylessly through [Sigstore](https://sigstore.dev) with the
   workflow's OIDC identity, or with an Ed25519 key.
2. **Store.** Each envelope is one line in a note under `refs/notes/veridict`.
   Notes merge with `cat_sort_uniq`, so machines can append independently.
   `veridict push` and `veridict fetch` sync the ref like any other.
3. **Author.** A `prepare-commit-msg` hook adds `Assisted-by:` when a commit
   is made from an agent session, and an authorship attestation records the
   author class with its evidence strength. Missing authorship counts as
   agent-authored.
4. **Verify.** `veridict verify BASE..HEAD` reads the notes from a clone,
   checks every signature against the identities and keys the policy trusts,
   checks the subject binds to the commit, and evaluates the rules. Exit
   code 0 means met, 1 not met, 2 error.

Every checker verdict carries a **tier**: `certificate` when an independent
checker can re-check a proof, `rerun` when a pinned toolchain can reproduce
it, `signed` when only a signature vouches for it. Today's adapters are
signed-tier; a counterexample is always replayable evidence.

## Quick start

```bash
pip install "veridict[checks] @ git+https://github.com/OWNER/veridict-core"
cd your-repo
veridict keygen                       # prints a keyid
mkdir -p .veridict && cp templates/policy.toml .veridict/policy.toml
# paste the keyid into [trust].keys
veridict attest --adapter python      # runs mypy, pytest, crosshair; appends 3 notes
veridict show HEAD
veridict verify HEAD
veridict hook install                 # Assisted-by trailer from agent sessions
```

## In GitHub Actions

Copy [`templates/veridict.yml`](templates/veridict.yml) to
`.github/workflows/` and [`templates/policy.toml`](templates/policy.toml) to
`.veridict/policy.toml`, then set the workflow identity in the policy:

```toml
[[trust.identities]]
issuer = "https://token.actions.githubusercontent.com"
identity = "https://github.com/OWNER/REPO/.github/workflows/veridict.yml@refs/heads/*"
```

On every push the checks run and their verdicts are pushed to
`refs/notes/veridict`, signed with the workflow's identity. On every pull
request the range is verified and the verdict appears in the job summary.
Nothing about the core depends on GitHub; the action is a thin wrapper.

## Policy

```toml
version = 1

[trust]
keys = ["sha256:..."]                       # from `veridict keygen`

[[trust.identities]]                        # Sigstore, globs allowed
issuer = "https://token.actions.githubusercontent.com"
identity = "https://github.com/OWNER/REPO/.github/workflows/veridict.yml@refs/heads/*"

[options]
allow_tree_match = false                    # evidence survives rebases when true
unknown_author = "agent"                    # fail closed toward the strict class

[[rule]]
name = "agent-written python"
paths = ["**/*.py"]
authors = ["agent", "assisted"]
require = [
  { checker = "mypy", result = ["pass"] },
  { checker = "pytest", result = ["pass"] },
  { checker = "crosshair", result = ["pass", "skipped"] },
]
```

A change to the policy file must itself be covered by a rule; otherwise
verification fails.

## Commands

| Command | Effect |
|---|---|
| `veridict keygen` | Create an Ed25519 key outside the repository |
| `veridict attest --adapter python [--sign key\|sigstore]` | Run checkers, append signed verdicts to the commit |
| `veridict authorship --class human\|assisted\|agent` | Record who or what authored the commit |
| `veridict authorship --infer` | Weak authorship attestation from trailers, for CI |
| `veridict verify REV[..REV] [--json]` | Evaluate the policy offline |
| `veridict show REV`, `veridict export REV` | Inspect attestations |
| `veridict push`, `veridict fetch` | Sync `refs/notes/veridict` |
| `veridict hook install` | Install the `prepare-commit-msg` hook |

## Formats

Statements are in-toto Statement v1 with `gitCommit` and `gitTree` digests.
Envelopes are DSSE. Keyless signatures are Sigstore bundles. Predicate types
live under `https://veridict.dev/` and will be proposed upstream. Details in
[`specs/2026-09-18-mvp/requirements.md`](specs/2026-09-18-mvp/requirements.md).

## Roadmap

SMT proof certificates checked by an independent checker, GitLab and bare
remotes, an evidence export mapped to SLSA Source, anonymous credentialed
approvals over zero-knowledge proofs, and Rust through Kani. See
[`specs/roadmap.md`](specs/roadmap.md).

## Developing

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest
```

The repository follows a spec-driven loop; see [`AGENTS.md`](AGENTS.md).

## Licence

Apache-2.0.
