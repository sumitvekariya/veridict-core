# Mission

Veridict is open-source infrastructure for verification evidence on AI-written
code. Every check a repository runs and every approval it receives becomes a
signed or certificate-backed attestation bound to the commit, stored in git,
demanded by a policy, and verifiable from any clone with no forge involved.

## Purpose

About half of committed code is now written by models. It compiles, its
generated tests pass, and its security pass rate has stalled at 56% for a year.
The canonical case from this project: a token-bucket limiter with `>= n`
changed to `>= n - 1` passed mypy, nine generated tests and Z3, and only a
contract check found `consume(TokenBucket(1, 1), 2)`.

Three pressures now converge on the same object, the commit:

- **Attackers** forge CI identities, replace tags with imposter commits, and
  push malicious workflow commits at scale.
- **Regulators and auditors** ask for provenance and evidence of checks: the
  Cyber Resilience Act's obligations began on 11 September 2026, SLSA's Source
  track defines two-party review attestations, and SOC 2 auditors ask to see
  the approval artifact behind an agent's action.
- **Agents** produce more change than humans can read, so the question moves
  from "did a human read it" to "what was verified, by what, and who vouched".

The crowded layer is judgment: a model reads the pull request and opines. The
empty layer is evidence. Veridict separates the two questions a merge must
answer and makes both answers verifiable by anyone:

1. **Does the implementation satisfy its specification?** Answered by the
   checkers the repository already runs, in its own CI, never inside
   Veridict. Each verdict is recorded with its tier: a certificate an
   independent checker can re-check, a deterministic re-run, or a signed
   result.
2. **Who or what authored and approved it?** Answered by authorship
   attestations bound to workload identity and by approval attestations,
   named today and anonymous in a later phase.

Both answers are in-toto statements in a notes ref. A policy file in the
repository says what an agent-authored change must carry. `veridict verify`
reads notes from a clone and exits pass or fail. GitHub, GitLab, Gitea and
bare remotes all carry git objects, so they all carry the evidence.

## Why it exists

The incidents share one shape: trust tied to a single identity, no formal gate
before approval, and reviewers paying the cost.

- **bincode, December 2024.** A forge migration looked like a supply-chain
  attack, the investigation turned into doxxing, the maintainer shut the
  project down.
- **xz-utils, March 2024.** Two years of earned credibility, then a backdoor
  caught by accident.
- **curl, 2024 to 2026.** AI-generated reports and patches that look right and
  are subtly wrong; the bug bounty ended in January 2026.
- **May 2026.** Imposter commits replaced the tags of popular GitHub Actions,
  and thousands of malicious workflow commits landed under throwaway CI-bot
  identities in six hours.

## Primary audience

**Platform and security teams** at organisations where agents write a large
share of the code and an auditor, a regulator or a SLSA level asks for
evidence. They run more than one forge, or expect to. When two audiences pull
in different directions, this one decides.

**Open-source maintainers** who need checks and agent disclosure before they
spend time reading a pull request. Free forever, and the adoption channel.

**Developers studying the codebase.** Attestation formats, certificate
checking, policy evaluation and git plumbing are each unusual enough that
clarity outranks cleverness. Every trust boundary is documented where it is
enforced.

## Stakeholder voices

- **Reviewer 1, hackathon judge:** "This could be better integrated with Git
  (as opposed to GitHub) and existing infrastructure like Sign-offs."
- **Reviewer 2, hackathon judge:** Z3 checked the spec, not the code (closed
  by crosshair). The issuer generated the key (closed by browser proving). No
  nullifier (deferred with the anonymous predicate).
- **Maintainer, Sumit Vekariya:** open source first, standards first, so the
  work qualifies as a public good for grants and incubation, and so the
  formats outlive the tool.

## Principles

- **Evidence, not judgment.** Veridict records what checkers and people
  concluded. It never concludes on its own.
- **Standards first.** in-toto statements, DSSE envelopes, Sigstore keyless
  signing, SLSA Source vocabulary. New predicates are proposed upstream.
- **Forge-agnostic core.** Anything that touches a forge API is an adapter.
- **Fail closed.** Unknown checker, tier, predicate or identity means the
  policy is not met.
- **Nothing secret in git.** Notes hold claims and evidence, never keys.

## What success looks like

- `veridict verify <commit>` on a fresh clone answers pass or fail from git
  objects alone, and rejects a tampered, replayed or unsigned attestation.
- One policy is enforced identically on GitHub, GitLab and a bare remote.
- An auditor accepts the exported bundle as evidence for SLSA Source, the
  Cyber Resilience Act or an SSDF attestation.
- A maintainer gates external pull requests on it at no cost.
- The protocol never requires a reviewer's identity; anonymous credentialed
  approval is one predicate among others when it lands.

## What Veridict is not

- Not a reviewer. It does not judge whether the change is good.
- Not a proof of correctness. The gate is bounded by the contracts and
  properties the code declares.
- Not a forge product. GitHub is the first adapter, not the core.
- Not a synthesis tool. The synthesis pipeline in `issuer/` is a demo of a
  consumer, not the product.
