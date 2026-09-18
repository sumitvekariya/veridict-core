# Market and safety trends, September 2026: where a git-native verification tool fits

**Context:** before committing the roadmap to a git-native verification tool, a
survey of what buyers, regulators, attackers, standards bodies and the AI-safety
community are doing right now, and what that implies for product-market fit.
Web synthesis, not customer interviews. The validation plan at the end is what
turns these hypotheses into evidence.

## Ten signals

1. **AI writes about half of committed code and its security has stalled.**
   Veracode's 2026 report puts the security pass rate of generated code at 56%,
   unchanged year over year, with 44% of generation tasks introducing a risky
   flaw, while syntax pass rates are near 100%. The gap between "compiles and
   tests pass" and "is correct" is now the industry's default state.
   ([Veracode 2026](https://www.veracode.com/blog/2026-genai-code-security-report-ai-risk/),
   [SD Times](https://sdtimes.com/agentic-security/veracode-finds-ai-generated-code-security-has-barely-improved-since-last-year/))

2. **Coding agents are themselves attack surface.** One crafted PR title drove
   prompt injection through Claude Code, Gemini CLI and Copilot at once, leaking
   CI credentials. Cursor shipped CVE-2026-22708 (poisoned allowlisted
   commands). The first malicious MCP server appeared in the wild after
   fifteen clean releases. GitGuardian counted 24,000 secrets in public MCP
   configs. OWASP reports prompt injection still drives most agentic failures
   in production.
   ([Morph](https://www.morphllm.com/ai-coding-agent-security),
   [VentureBeat](https://venturebeat.com/security/ai-agent-runtime-security-system-card-audit-comment-and-control-2026),
   [Help Net Security](https://www.helpnetsecurity.com/2026/06/11/owasp-prompt-injection-ai-security-failures/))

3. **Supply-chain attacks moved to the source layer.** In March 2026 one
   unrotated PAT let attackers force-push poisoned tags over 75 of 76 versions
   of trivy-action. In May, imposter commits replaced every tag of two popular
   Actions, a poisoned VS Code extension led to the exfiltration of about
   3,800 GitHub-internal repositories, and the MEGALODON_CI campaign pushed
   5,718 malicious workflow commits to 5,561 repositories in six hours using
   throwaway CI-bot identities and backdated timestamps. The attacks are on
   *who committed what* and *whether a revision is what it claims*, which is
   exactly what source-level provenance is for.
   ([Zscaler](https://www.zscaler.com/blogs/security-research/supply-chain-attacks-surge-march-2026),
   [StepSecurity](https://www.stepsecurity.io/blog/5-supply-chain-attacks-in-48-hours-why-securing-one-layer-is-not-enough),
   [Phoenix Security](https://phoenix.security/accelerating-supply-chain-attacks-npm-pypi-vsx-ai-enabled-2026/))

4. **Maintainers are drowning, and the review trust model broke.** curl ended
   its bug bounty in January 2026 over AI slop. GitHub is designing a PR kill
   switch and contributor gating. A Genkit maintainer reports one in ten AI
   PRs is legitimate; an Azure maintainer says "reviewers can no longer assume
   authors understand" the code. OpenSSF and CNCF published a maintainers'
   guide for the age of AI in May 2026.
   ([The Register, curl](https://www.theregister.com/2026/01/21/curl_ends_bug_bounty/),
   [The Register, GitHub](https://www.theregister.com/2026/02/03/github_kill_switch_pull_requests_ai/),
   [The New Stack](https://thenewstack.io/ai-generated-code-crisis/),
   [OpenSSF guide](https://openssf.org/wp-content/uploads/2026/05/Securing-Open-Source-in-the-Age-of-AI.pdf))

5. **Regulation arrived this month.** The EU Cyber Resilience Act's reporting
   obligations took effect on 11 September 2026, with full obligations and the
   open-source steward regime in December 2027; readiness guidance centres on
   documented secure-development and vulnerability-handling processes. In the
   US, the CISA attestation form under OMB M-26-05 has vendors attest to
   trusted source supply chains, data provenance for internal and third-party
   code, and automated checks. In safety-critical sectors, standards already
   accept formal verification as compliance evidence, and an AI-generated test
   without traceability is not citable evidence at all.
   ([Goodwin on CRA](https://www.goodwinlaw.com/en/insights/publications/2026/09/alerts-lifesciences-technology-preparing-for-eu-cyber-resilience-act),
   [EC CRA reporting](https://digital-strategy.ec.europa.eu/en/policies/cra-reporting),
   [CISA form](https://www.cisa.gov/resources-tools/resources/secure-software-development-attestation-form),
   [Jama on safety-critical AI code](https://www.jamasoftware.com/blog/ai-generated-code-risks/),
   [TrustInSoft](https://www.trust-in-soft.com/resources/blogs/formal-verification-your-key-to-regulatory-compliance-iso-26262-do-178c))

6. **Standards converged on attestations, and left the verification slot
   empty.** SLSA v1.2 (November 2025) added a Source track: L2 source
   provenance, L3 continuously enforced controls, L4 two-party review with code
   review attestations, all as in-toto statements whose provenance "may
   include vulnerability or test results". GitHub artifact attestations are
   default-on for public repositories. gittuf, an OpenSSF incubating project,
   stores policy and reference-authorization attestations in `refs/gittuf/`.
   The vocabulary for verifiable claims about a source revision now exists.
   No one issues a *verification result* predicate for source.
   ([SLSA source requirements](https://slsa.dev/spec/v1.2/source-requirements),
   [GitHub attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations),
   [gittuf](https://github.com/gittuf/gittuf))

7. **AI authorship provenance is a live, unsolved debate.** VS Code 1.117
   stamped `Co-authored-by: Copilot` on commits where AI was disabled. Proposals
   now circulate for an `Assisted-by:` trailer, AI authorship inside SLSA
   provenance, and keyless signing bound to workflow identity. A CISO-facing
   piece calls commit identity "a security control, not a metadata detail" and
   cites 41% of code as AI-generated or assisted.
   ([zircote](https://zircote.com/blog/2026/07/recording-ai-authorship-in-provenance/),
   [NHI Management Group](https://nhimg.org/articles/code-provenance-is-the-missing-control-for-ai-generated-commits/))

8. **Capital is flowing to verification, on the generation side.** Axiom
   raised $200M at $1.6B (March 2026) to generate Lean-verified outputs, still
   pre-commercial. Theorem raised $6M to verify AI-written code post hoc with
   Rocq and Lean for labs and EDA firms, and found a bug in Anthropic's
   codebase that tests missed. Qodo raised $70M for AI review and test
   generation branded as verification. AI code review itself is crowded and
   concentrated: Cursor took 44% of disclosed dev-tool capital in the year to
   July 2026.
   ([Axiom](https://siliconangle.com/2026/03/12/verifiable-ai-startup-axiom-raises-200m-prove-ai-generated-code-safe-use/),
   [Theorem](https://venturebeat.com/security/theorem-wants-to-stop-ai-written-bugs-before-they-ship-and-just-raised-usd6m),
   [Qodo](https://siliconangle.com/2026/03/30/ai-generated-code-verification-startup-qodo-raises-70m/),
   [New Market Pitch](https://newmarketpitch.com/blogs/news/ai-dev-tools-funding-analysis))

9. **AI safety now names this problem.** Scalable oversight literature states
   that line-by-line human verification of agent output is becoming
   intractable. A NeurIPS 2026 workshop, "Who Verifies the Agents?", lists
   formal verification of agent-generated artifacts with Dafny, Rocq and Lean
   as a core topic. OpenAI's GPT-5.6 system card reports a greater tendency to
   act beyond user intent in agentic coding. Verification of agent output is a
   recognised safety subproblem, not only a DevSecOps feature.
   ([workshop](https://verify-agents-workshop.github.io/),
   [GPT-5.6 system card](https://deploymentsafety.openai.com/gpt-5-6),
   [scalable oversight](https://aisecurityandsafety.org/en/guides/scalable-oversight/))

10. **Auditors ask for the artifact.** SOC 2 and ISO 42001 guidance for 2026
    frames the question as "if an agent took an action, can you show the
    approval artifact and reconstruct the chain". Forrester's AEGIS framework
    puts GRC at the foundation of agent governance.
    ([Blaxel](https://blaxel.ai/blog/soc-2-compliance-ai-guide),
    [Conifers](https://www.conifers.ai/blog/the-enterprise-ai-soc-a-cisos-guide-from-pilot-to-production-in-2026))

## The need of the hour

Three pressures converge on the same object, the commit:

- **Attackers** forge identities and rewrite tags at the source layer.
- **Regulators and auditors** want provenance and evidence of checks, from this
  month onward.
- **Agents** produce more change than humans can read, so the question moves
  from "did a human read it" to "what was verified, by what, and who vouched".

The crowded, funded layer is *judgment*: an LLM reads the PR and opines. The
unmet layer is *evidence*: a verifiable, portable, policy-checkable record that
a specific revision was checked against a specification by named tools, that
records who or what authored it, and who approved it, bound to the commit,
surviving forge migration, checkable offline, and usable as compliance evidence.
That is a git-native verification tool, and the standards now give it a
vocabulary (in-toto, SLSA Source, Sigstore) without anyone occupying it.

## Segments

| Segment | Pain today | Pays? | Alternatives they have | Fit |
|---|---|---|---|---|
| Open-source maintainers | Slop floods; cannot trust authors understand their PRs | No | GitHub gating, contributor policies | Adoption and credibility channel. Their ask is "prove the checks ran and disclose the agent before I read it", not anonymity |
| Platform and security teams at agent-heavy engineering orgs | Agent commits with no evidence trail; SOC 2, SLSA and SSDF questions; source-layer attacks | Yes, compliance budget | GitHub rulesets, artifact attestations (build, not source semantics), gittuf (who may change what, not whether it was verified), scanners | **Strongest.** Verification attestations plus policy is exactly the gap |
| Safety-critical and regulated (automotive, medical, aerospace, fintech) | Cannot admit AI code without traceable verification evidence | High | TrustInSoft, Parasoft, Vector, AdaCore, all pre-agent and not git-native | Strong on the certificate tier; long cycles; needs a domain partner |
| AI labs and agent vendors | Must show agent output is safe to merge autonomously | High | In-house, Theorem | Partner: attestations emitted by agent runs |
| Federal software vendors | SSDF self-attestation with evidence | Medium | Document-based compliance | Later, once evidence export exists |

## Competitive map

| Layer | Who | What they produce | What they do not |
|---|---|---|---|
| AI code review | Cursor Bugbot, CodeRabbit, Graphite, Copilot review, Qodo | Opinions on a PR | Evidence, portability, policy |
| Verified generation | Axiom, Code Metal | Code plus proof at generation time | Anything about code you already have |
| Post-hoc formal verification | Theorem | Proofs as a service for labs | Portable certificates in the repo, policy |
| Build attestations | Sigstore, GitHub artifact attestations, SLSA Build, in-toto | Signed provenance for artifacts | Source-revision semantics |
| Source policy | gittuf | Who may change which refs and paths, signed | Whether the change was verified |
| Review in git | git-appraise, attest | Review verdicts in notes | Tool evidence, certificates, strong trust |

The empty cell: **verification evidence for source revisions, certificate-backed
where possible, policy-gated, forge-agnostic.**

## Prior art for anonymous credentialed attestation

Checked separately, because it decides whether the ZK approval predicate is
novel or already served.

| Work | What it does | Gap relative to an anonymous approval on a commit |
|---|---|---|
| Speranza (Merrill, Newman, Torres-Arias, Sollins, 2023) | Privacy-preserving signer identity for package signing: identity co-commitments plus zero-knowledge proofs, so verifiers learn "an authorised maintainer signed" without learning who | Proof of concept; about packages, not commits or review; no policy layer |
| Semaphore, World ID | Anonymous group-membership signalling with millions of users | Blockchain-oriented; no credential semantics such as "qualified reviewer for this repo" |
| zkLogin, ZK Email, ExPrESSO | Prove membership of an organisation from an OIDC token or DKIM-signed email without revealing identity | An alternative credential source to MDOC; 2026 analysis shows security rests on parsing and issuer-policy assumptions outside the proof |
| zkTLS: Reclaim, TLSNotary, github-zktls | Prove facts from an authenticated GitHub session, such as contribution history, with minimal disclosure | Trusted-notary or alpha-stage; proves data shown by a site, not a qualification issued by a trusted party |
| BBS+ credentials, DAA and EPID in TPM and SGX | Mature anonymous-credential primitives | Not applied to code review; Longfellow is the same family for ECDSA-signed credentials |
| Anonymous GitHub | Anonymised repositories for double-blind academic review | A trusted intermediary, not cryptography |
| gittuf | Signed reference-authorisation attestations in git | Approvers are identified by design |

Nothing combines an anonymous credentialed approval, bound to a specific
commit, verifiable offline, and counted by a merge policy. The Veridict
predicate remains novel. The ecosystem now offers alternative credential
sources, notably zkJWT-style proofs of organisation membership, that could
replace the MDOC issuer for enterprise deployments.

Sources: [Speranza](https://arxiv.org/abs/2305.06463),
[Semaphore](https://github.com/orgs/semaphore-protocol/repositories),
[zkLogin analysis 2026](https://eprint.iacr.org/2026/227),
[ZK Email](https://zk.email/),
[Reclaim attestor-core](https://github.com/reclaimprotocol/attestor-core),
[github-zktls](https://github.com/teleport-computer/github-zktls),
[BBS+ credentials](https://eprint.iacr.org/2025/824),
[Anonymous GitHub](https://anonymous.4open.science/).

## Where the existing Veridict pieces land

- **CI-sourced gate, crosshair, wasm verifier, browser proving:** reusable
  engineering. The wasm verifier is the template for "a certificate anyone can
  check anywhere".
- **Anonymous ZK approval:** a genuine differentiator for open source and a
  credential-privacy story, but not the buyer's first ask. Keep it as one
  attestation type; do not lead with it.
- **Spec-driven synthesis:** a demo, and the labs' business. Do not compete.

## Recommended wedge

**Verification attestations for AI-written changes.** A CLI and CI step that
turns the checks a repository already runs (types, tests, contracts, property
tests, model checkers, proof assistants) into signed or certificate-backed
in-toto attestations on the commit, stored in git; a policy file stating what
an agent-authored change must carry before merge; `verify` that answers offline
from a clone; and an evidence export that maps onto SLSA Source L3 and L4,
CRA documentation and SSDF attestation.

- **Initial customer:** platform or security team, 50 to 2,000 engineers,
  heavy agent usage, a compliance clock (SOC 2 renewal, CRA, SSDF, SLSA
  Source), GitHub plus at least one other forge.
- **Secondary:** open-source maintainers on a free tier, for credibility and
  for the slop problem, where the pitch is "checks and disclosure before a
  human reads it".
- **MVP surface:** attest from CI for Python (mypy, pytest, crosshair) plus SMT
  certificates checked by an independent checker; an agent-authorship
  predicate bound to workload identity; policy such as "agent-authored change
  under `src/` requires contract checks plus one human approval"; offline
  verify; a GitHub check and a GitLab merge-request status from the same core.
- **Business model hypothesis:** open-source core under a permissive licence;
  paid hosted policy dashboard, evidence export for auditors, and support.
- **What would falsify it:** platform teams say GitHub rulesets plus artifact
  attestations are enough; auditors reject commit-level evidence; GitHub or
  the agent vendors ship native agent provenance and verification records. The
  hedge against the last is forge independence and certificates, which a
  single forge cannot offer.

## Alternatives considered

- **Slop gate for maintainers.** Free, proof-of-work before a PR is read:
  checks passed, agent disclosed, optionally an anonymous credential. Highest
  adoption, no revenue. Use as top of funnel, not as the business.
- **Certificate tier for safety-critical.** Lean, Dafny or SMT certificates in
  git as DO-178C and ISO 26262 evidence. Highest willingness to pay, slowest to
  close, needs a partner in the domain. A second act.
- **Agent provenance only.** `Assisted-by` trailers plus signing. Narrow and
  likely to be absorbed by GitHub and the IDEs within a year.

## Validation plan, before building past the MVP

1. **Ten conversations in three weeks:** four platform or security leads at
   agent-heavy companies, three maintainers hit by slop, two audit or
   compliance practitioners (a SOC 2 auditor, a CRA consultant), one
   safety-critical engineer.
2. **Questions that matter:** How do you know today which commits an agent
   wrote? What did your last auditor ask for about AI-generated code? What
   happens if you move off GitHub? Would you pay for an evidence export? What
   check would have to pass before you let an agent merge without reading?
3. **Signals of fit:** someone asks for the evidence export unprompted; someone
   wants it on GitLab or a bare remote; someone has a SLSA Source, CRA or SSDF
   deadline this year; a maintainer would require it for external PRs.
4. **Cheap test:** a landing page, "Prove your AI-written code was verified.
   In git.", with a waitlist and one question about forge and compliance
   driver.
5. **Design partners:** two organisations run the MVP on one repository each
   for a month.

## Implications for the constitution and roadmap

If the wedge holds, the mission shifts from "forge-agnostic anonymous review"
to "verification evidence for AI-written changes, in git", and the roadmap
reorders: attestation record and attest-from-CI first, policy and offline
verify second, agent-authorship predicate third, second forge fourth, evidence
export and SLSA Source mapping fifth, anonymous approval as an attestation type
sixth, Rust via Kani seventh. This note does not make that change; the
replanning step does, after the wedge decision.
