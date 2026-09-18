# Funding options for a git-native verification tool, as of 2026-09-18

**Context:** can the work be funded through AI-safety grants and incubators?
Status below was checked on 2026-09-18. Two framings are fundable, and a third
is not right now:

- **AI-safety framing:** scalable oversight infrastructure for agent-written
  code. Humans cannot read what agents produce; verification evidence bound to
  the commit, checked by policy, is how oversight scales. Funders: ARIA,
  Seldon, Catalyze, Coefficient Giving, Anthropic Fellows, EA Funds.
- **Open-source and supply-chain security framing:** maintainers drowning in
  agent PRs, forged CI identities, provenance for the Cyber Resilience Act and
  SSDF. Funders: GitHub Secure Open Source Fund, Alpha-Omega and OpenSSF,
  Anthropic Defender Advantage Fund, OpenAI cybersecurity grants.
- **Privacy framing** for the anonymous ZK approval: the natural funders
  (NLnet NGI Zero, Sovereign Tech Agency) closed their 2026 calls. One more
  reason the ZK predicate stays deferred.

## Programmes

| Programme | What it gives | Who can apply | Status today | Fit | How to pitch |
|---|---|---|---|---|---|
| **ARIA Safeguarded AI, Cybersecurity Track 1** | Share of a £59m programme; 8-week sprints, red-team stress tests, deployment support | International; academia, industry, non-profits, teams | **Open, rolling; next cut-off 31 Oct 2026** | High | Blue-team building "security-critical software components whose key security properties are backed by machine-checked proofs" using AI. Pitch the verifier and policy engine as that component, verified itself, plus the evidence format as the deployment vehicle. Needs formal-methods and security depth on the team |
| **Seldon Lab** | Up to $500k per startup, 3 months in San Francisco, customer intros | Technical founders, international, solo allowed, full-time in SF | Batch 2 ran Jan to Apr 2026; **watch for Batch 3** | High | Their request for startups names formal verification and supply chain oversight explicitly |
| **Catalyze Impact** | Incubation, co-founder matching, funding network; for-profit and non-profit | Founders | Multiple programmes per year from 2026; **check current window** | High | AI safety and security organisation building; pilot incubated 11 orgs including AI-control tooling |
| **Coefficient Giving, Technical AI Safety RFP** | About $40m pool; individuals up to about $187k, orgs more; API credits to multi-year projects | Individuals, academics, new orgs, worldwide | Rolling per aggregators; site returned 403 today, confirm directly | Medium | Research framing only: does attestation-gated merging constrain misaligned coding agents? Open-source tooling as output |
| **EA Funds, Transformative AI Fund** | $1k to $500k, application under an hour | People, projects, new orgs | **Open** | Medium | Early-stage oversight infrastructure; fast small grant to fund the validation sprint |
| **Anthropic Fellows Program** | Funding, compute, mentorship for four months; areas include scalable oversight, AI control, AI security | Individuals | Rounds began May and July 2026; **November 2026 round announced** | Medium-High for the person | The oversight research question above, run on real agent traffic |
| **Anthropic Defender Advantage Fund** | $35m in Claude credits for organisations working with open-source maintainers on security | Organisations; pilot grants first, via the Linux Foundation | Announced Aug 2026, **phased, no open form yet** | Medium | Credits, not runway. Fits the maintainer slop-gate and "defences against attack categories" |
| **OpenAI Cybersecurity Grant Program** | $10k increments, credits or funding; defensive tooling preferred | Individuals and orgs | Page returned 403 today; programme refocused Feb 2026 toward deployment | Low-Medium | Small; defensive verification tooling |
| **GitHub Secure Open Source Fund** | $10k plus Azure credits, 3-week security programme, GitHub Security Lab office hours, cohort of maintainers | Maintainers of an adopted, licensed, governed open-source project | **Rolling** | Medium now, High later | Once the open-source core has users. The cohort itself is a design-partner pool. Focus areas: "security in the AI era", "securing the AI software supply chain" |
| **Alpha-Omega and OpenSSF** | $12.5m announced Mar 2026 from Anthropic, AWS, GitHub, Google, DeepMind, Microsoft, OpenAI for open-source security | Projects and foundations | Ongoing | Medium | Route in through OpenSSF: contribute the verification predicate to in-toto and SLSA Source; gittuf is already an OpenSSF incubating project |
| **Y Combinator** | $500k, four batches a year | Companies | Ongoing; 2026 RFS lists dev tools for AI agents and compliance-heavy verticals | Medium-High as the company route | Apply with two design partners and the evidence-export story. Theorem, the closest analogue, was a YC company |
| **NCIIPC Startup India AI Grand Challenge** | ₹88 lakh per problem statement | Indian startups | **Runs to 30 Sep 2026** | Medium if a statement matches | Check the problem statements this week for software supply chain or AI-generated code security |
| **IndiaAI Mission** | Startup financing, compute at about ₹65 per GPU-hour, global acceleration cohort | Indian AI startups | Ongoing | Low-Medium | Later, for compute and market access |
| **Apart Lab Studio and Fellowship** | 8-week research programme after a hackathon, then a 4 to 6 month fellowship; publication-oriented | Selected hackathon teams | Studio announced 17 Sep 2026 | Medium | Existing relationship from the hackathon. Research track for the oversight question, not the company |
| **Survival and Flourishing Fund** | $20m to $40m a year across rounds | Organisations, usually non-profit or fiscally sponsored | 2026 deadline passed 8 Jul; annual | Low-Medium | 2027, with a fiscal sponsor |
| **Schmidt Sciences, Trustworthy AI and Multi-Agent Safety** | $1m to $5m and up to $1m | Research institutions | 2026 deadlines passed (17 May, 8 Aug); annual | Low without a university partner | 2027 |
| **UK AI Security Institute** | Alignment Project up to £1m; Challenge Fund up to £200k | Academic and non-profit | **All closed; "unlikely to run a similar programme in 2026"** | None now | 2027 |
| **NLnet NGI Zero Commons** | €5k to €50k first grants for open-source internet tech | Open-source projects, individuals | **Final call closed 1 Jun 2026** | Was high | Watch for successor programmes |
| **Sovereign Tech Agency** | Investment in widely used open-source infrastructure; fellowship | Maintainers of adopted infrastructure | 2026 fellowship and standards calls closed | Low now | After adoption |
| **DARPA** | I2O office-wide BAA open to Nov 2026; PROVERS on proof-friendly software | Mostly US performers | Open | Low for a solo non-US founder | Partner with a US institution if ever |

## Recommended sequence

**This month.** Check the NCIIPC problem statements before 30 September. Apply
to the EA Funds Transformative AI Fund for a small grant that covers the
ten-interview validation sprint. Confirm the Anthropic Fellows November round
deadline and decide whether the oversight research question is worth four
months of personal time.

**By 31 October.** Decide on ARIA Track 1. It is the best-aligned open call in
the world for this idea, and it is a team call: security plus formal methods
plus proof engineering plus AI workflows. Solo is a weak application; one
formal-methods collaborator changes that.

**Watch continuously.** Seldon Lab Batch 3 and Catalyze Impact's next cohort.
Both name this problem in their own words. Apply the moment either opens.

**After the open-source core ships.** GitHub Secure Open Source Fund, rolling,
and OpenSSF engagement toward Alpha-Omega. Contribute the verification
predicate upstream to in-toto and SLSA Source; that is both a standards move
and a funding door.

**Company route.** YC or Seldon once two design partners run the tool.

## Caveats

- AI-safety funders pay for research and public goods, not go-to-market. A
  company with an open-source core can fund the core and the research
  questions this way, and must fund sales some other way.
- Credits are not runway. Anthropic and OpenAI programmes mostly give credits.
- The anonymity work has the weakest funding story this year. Its natural
  funders are closed, and safety funders do not prioritise reviewer privacy.

## Sources

- ARIA Safeguarded AI funding: https://aria.org.uk/opportunity-spaces/mathematics-for-safe-ai/safeguarded-ai/funding and the cybersecurity solicitation https://aria.org.uk/media/1padxpaf/safeguarded-ai_cybersecurity_solicitation.pdf
- Seldon Lab RFS: https://seldonlab.com/rfs and https://seldonlab.com/blog/announcing-the-seldon-summer-2025-batch
- Catalyze Impact: https://www.catalyze-impact.org/apply
- Coefficient Giving technical AI safety RFP: https://coefficientgiving.org/funds/navigating-transformative-ai/request-for-proposals-technical-ai-safety-research/
- EA Funds: https://funds.effectivealtruism.org/
- Anthropic Fellows: https://alignment.anthropic.com/2025/anthropic-fellows-program-2026/
- Anthropic Defender Advantage Fund coverage: https://www.opensourceforu.com/2026/08/anthropic-pledges-us35m-to-secure-open-source-software-with-ai/
- OpenAI Cybersecurity Grant Program: https://openai.com/index/openai-cybersecurity-grant-program/
- GitHub Secure Open Source Fund: https://github.com/open-source/github-secure-open-source-fund
- Alpha-Omega $12.5m: https://alpha-omega.dev/blog/linux-foundation-announces-12-5-million-in-grant-funding-from-leading-organizations-to-advance-open-source-security/
- Y Combinator RFS: https://www.ycombinator.com/rfs
- NCIIPC AI Grand Challenge: https://ai-grand-challenge.in/
- IndiaAI startup financing: https://indiaai.gov.in/hub/indiaai-startup-financing
- Apart Lab Studio: https://apartresearch.com/news/announcing-apart-lab-studio
- SFF 2026: https://survivalandflourishing.fund/2026/application
- Schmidt Sciences (via Granted AI): https://grantedai.com/news/schmidt-sciences-trustworthy-ai-grants-5-million-2026
- UK AISI grants: https://www.aisi.gov.uk/grants and https://alignmentproject.aisi.gov.uk/
- NLnet NGI Zero Commons Fund: https://nlnet.nl/commonsfund/
- Sovereign Tech Agency programmes: https://www.sovereign.tech/programs
- DARPA programmes (via Granted AI): https://grantedai.com/blog/every-darpa-ai-program-2026
