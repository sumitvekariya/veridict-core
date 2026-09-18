# Tech Stack

This repository holds the Python core package and CLI for attestations in git, adapters around the
checkers a repository already runs, and thin forge adapters. The hackathon-era
issuer and backend live in the `Zkred/veridict` repository as the reference consumer and the
future producer of the anonymous approval predicate.

## Core package: `veridict/`

- **Python 3.11+**, standard library first. TOML policy via `tomllib`,
  subprocess `git` for all repository operations, `argparse` for the CLI.
- **Attestation format:** in-toto Statement v1 with two digests per subject,
  `gitCommit` and `gitTree`. DSSE envelope. Predicate types under a Veridict
  namespace for verification and authorship, in-toto `test-result/v0.1`
  reused where a checker is a plain test suite.
- **Signing:** Ed25519 and SSH keys via `cryptography` locally; Sigstore
  keyless via `sigstore` as an optional extra in CI (Phase 4).
- **Storage:** `refs/notes/veridict`, one JSON envelope per line, merged with
  `cat_sort_uniq`; evidence blobs under `refs/veridict/evidence/<sha256>`.
- **Adapters:** `veridict/adapters/python.py` (mypy, pytest, crosshair).
  Later: `smt.py` (cvc5 Alethe proofs checked by carcara), `kani.py`.
- **Tiers:** `certificate`, `rerun`, `signed`; falsification always carries a
  replayable counterexample.
- **Tests:** pytest under `tests/` against a fixture repository built in a
  temporary directory. `pytest` is the validation command for every phase.
- **Licence:** Apache-2.0 (LICENSE at the root).
  The ecosystem default: Sigstore, in-toto, gittuf, SLSA.

## Reference deployment: issuer and backend

Kept as they shipped; see `docs/V2-PLAN.md` for what was built and measured.

- **Issuer** (`issuer/`): FastAPI. GitHub OAuth, PR loading, CI spec-gate
  reader (`spec_gate.py`), MDOC credential minting (`mdoc_builder.py`),
  Claude synthesis (`synthesizer.py`), reviewer UI.
- **Backend** (`backend/`): FastAPI. Proof verification in-process under
  `wasmtime` (`wasm_verifier.py`), approvals, GitHub App status and comment.
- **Zero knowledge:** Google Longfellow ZK pinned to `c849531` with patches in
  `patches/`; cached circuit in `prover/circuits/`; browser proving from
  `issuer/static/`; wasm build via `prover/wasm/build.sh`. Used only by the
  anonymous approval predicate, Phase 8.
- **Deployment:** two Vercel projects selected by `VERIDICT_ROLE` through
  `api/index.py`, two Neon databases. Constraints recorded in README
  "Deployment".

## The existing gate

`templates/veridict-spec-gate.yml` runs mypy, pytest, crosshair and Z3
property files in the reviewed repository's CI and publishes a check run. The
Python adapter in the core package produces attestations from the same
checks, so the template evolves into `templates/veridict-attest.yml` in
Phase 4.

## Testing and validation

- `pytest` for `veridict/` and its adapters.
- `scripts/validate_v2.sh` and the other `scripts/validate_*` for the
  reference deployment; unchanged.
- No CI runs on this repository's own pull requests yet; adding a workflow
  that runs `pytest` is part of Phase 4.

## Tooling

- `scripts/bootstrap.sh` builds the ZK toolchain for the reference
  deployment; not needed for the core package.
- No linter or formatter configured.

## Gaps

1. **Python-only checkers.** Closed adapter by adapter; options and order in
   `backlog/2026-09-18-multi-language-spec-checks.md`.
2. **Key management in CI** until Sigstore keyless lands in Phase 4.
3. **No certificate-tier adapter** until Phase 5.
4. **GitHub-only adapter** until Phase 6.
5. **No nullifier and no anonymous approval** until Phase 8.
6. **Distribution into hooks** needs a static binary; Later.
