# Working in this repository

Veridict is open-source infrastructure for verification evidence on AI-written
code: attestations bound to commits, stored in git, demanded by policy,
verifiable from any clone. Read `specs/mission.md` first.

## Spec-driven workflow

This repository follows the spec-driven loop from the DeepLearning.AI and
JetBrains course. The constitution lives in `specs/`:

- `specs/mission.md`: purpose, audience, principles.
- `specs/tech-stack.md`: what we build with, and the recorded gaps.
- `specs/roadmap.md`: small phases with checkboxes.

Every phase goes through the same loop:

1. **Spec.** Run the `feature-spec` skill. It finds the next phase, creates a
   branch off `main`, interviews the maintainer, then writes
   `specs/YYYY-MM-DD-<feature>/requirements.md`, `plan.md`, `validation.md`.
2. **Implement** the plan's task groups in a fresh context. Tests are part of
   each group, not an afterthought.
3. **Validate** against `validation.md`. Every automated command there must
   exit zero. Before merging, run a deep review from several perspectives.
4. **Finish.** Tick the roadmap items, run the `changelog` skill, commit,
   merge into `main`, delete the branch.

Replan between phases: change the constitution first, then propagate to specs
and code. Research that informs a decision goes in `backlog/` as a dated note.

## Branches

- `main`: the integration branch of this repository.
- The hackathon system and its deployment live in `Zkred/veridict`; this repository holds only the core.
- `phase-N-<name>` or `mvp`: one per phase, branched from `main`.

## Commands

```bash
pytest                                  # core package and adapters

python3 .claude/skills/changelog/scripts/changelog.py
```

## Guardrails

- Never execute untrusted repository code in the same process as signing
  material. Checkers run in the reviewed repository's CI.
- Nothing secret is written to git notes or evidence refs.
- Anything that touches a forge API is an adapter, never the core.
- Fail closed: unknown checker, tier, predicate or identity means not met.
- Do not add a dependency without approval in the phase interview.
- Commit messages are short and imperative. No co-author trailers.
- Do not push without being asked.

## Agent portability

Skills live in `.claude/skills/` in the Agent Skills format and are plain
Markdown; any agent can read them. `CLAUDE.md` only imports this file.
