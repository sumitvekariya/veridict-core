# Roadmap

Phases are intentionally small. Each is implementable in one focused session on
its own branch with its own spec directory under `specs/`. Phases 1 to 3 are
the MVP and may share one spec directory, as the course's MVP sprint did.

What shipped before this roadmap (browser proving, wasm verification, the
CI-sourced gate, crosshair, the Vercel deployment) is described in
`docs/V2-PLAN.md`, now a historical record. The ten interviews in
`backlog/2026-09-18-market-and-safety-trends.md` run alongside phases 1 to 4
and may reorder everything after them.

---

## Phase 1: Attestation record and Python attest

**Goal:** turn the checks a Python repository already runs into attestations
in git.

- [ ] `veridict/` package: in-toto Statement with `gitCommit` and `gitTree`
      subjects, DSSE envelope, predicate types for verification and authorship
- [ ] Key-based signing (Ed25519 or SSH key) with trusted-key verification
- [ ] Notes storage: one envelope per line under `refs/notes/veridict`,
      evidence blobs under `refs/veridict/evidence/<sha256>`
- [ ] Python adapter: mypy, pytest, crosshair, each a signed-tier verdict;
      crosshair counterexamples recorded as falsification evidence
- [ ] `veridict attest`, `veridict push`, `veridict fetch`
- [ ] pytest suite against a fixture repository; this starts the repository's
      own tests

---

## Phase 2: Policy and offline verify

**Goal:** answer pass or fail from a clone, with no forge API.

- [ ] `.veridict/policy.toml`: rules by path and author class requiring
      predicates, tiers and thresholds; trusted identities
- [ ] `veridict verify <rev-range>`: signatures, subject binding, policy
      evaluation, non-zero exit and a report of what is missing
- [ ] Policy self-protection: a change to the policy file must satisfy the
      policy
- [ ] Negative tests: tampered note, replayed attestation, wrong subject,
      untrusted key, missing predicate

---

## Phase 3: Authorship capture

**Goal:** record who or what wrote a change, strongest source first.

- [ ] `veridict hook install`: a `prepare-commit-msg` hook that adds an
      `Assisted-by:` trailer when an agent session is detected
- [ ] Authorship attestation from the agent side at commit time, starting
      with Claude Code hooks
- [ ] CI inference from trailers, marked as weak evidence
- [ ] Missing authorship treated as agent-authored by policy

---

## Phase 4: Keyless signing and the GitHub adapter

**Goal:** no key management in CI, and a check on the pull request.

- [ ] Sigstore keyless signing of envelopes with the workflow's OIDC identity
- [ ] Trusted identities as issuer and subject patterns in policy
- [ ] `templates/veridict-attest.yml`: attest and push on every push, verify
      on pull requests, publish a check run
- [ ] Run it on the demo repository end to end

---

## Phase 5: SMT certificates

**Goal:** the first certificate-tier verdict.

- [ ] SMT adapter: cvc5 with Alethe proof output, checked by carcara
- [ ] Move the demo repository's Z3 property scripts to SMT-LIB
- [ ] Verify re-checks stored proofs locally

---

## Phase 6: Second forge and bare remote

**Goal:** the same policy enforced without GitHub.

- [ ] GitLab CI template with merge-request status
- [ ] Pre-receive hook for a bare remote
- [ ] Demonstrate the full flow on a bare remote with no forge

---

## Phase 7: Evidence export

**Goal:** the artifact an auditor accepts.

- [ ] `veridict export`: evidence bundle for a range
- [ ] SLSA Source verification summary with organisation properties
- [ ] Mapping notes for the Cyber Resilience Act and SSDF attestation

---

## Phase 8: Anonymous approval predicate

**Goal:** approval without identity, over the existing ZK stack.

- [ ] Approval predicate authenticated by a Longfellow proof instead of a
      signature, verified by the wasm verifier
- [ ] Client-bound nullifier so one reviewer counts once
- [ ] Issuer and backend refactored as producers of this predicate

---

## Phase 9: Rust via Kani

**Goal:** the first re-run-tier adapter and the first non-Python ecosystem.

- [ ] Kani adapter with pinned toolchain digest and concrete-playback
      counterexamples
- [ ] Synthesis emits Kani harnesses and contracts

---

## Later, unscheduled

- Static-binary port of `verify` for hooks
- Lean tier via kernel replay
- Re-run tier for Dafny, CBMC and Frama-C
- Go, C, TypeScript and Java adapters per the backlog note
- In-circuit nullifier
- Refinement proofs and spec hash bound into the credential
