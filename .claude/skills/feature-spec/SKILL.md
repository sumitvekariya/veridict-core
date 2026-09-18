---
name: feature-spec
description: Starts the next roadmap phase. Finds the first incomplete phase in specs/roadmap.md, creates a branch off main, interviews the user about scope, decisions and context, then writes a dated spec directory under specs/ containing requirements.md, plan.md and validation.md. Trigger on "feature spec", "next phase", "start the next feature", or /feature-spec.
---

# Feature Spec

## Workflow

### 1. Find the next phase

Read `specs/roadmap.md`. The next phase is the first section whose items are
all `[ ]`. Note its number and name.

### 2. Create the branch

Branch from `main`. The hackathon system lives in a different repository, so
there is nothing here to protect from feature work.

```
git checkout main
git checkout -b phase-N-<kebab-name>
```

### 3. Interview the user before writing any file

Use `AskUserQuestion` with exactly three questions in one call:

| Header | Question focus |
|---|---|
| **Scope** | What the phase produces and what it explicitly leaves out: formats, endpoints, commands, data shapes |
| **Decisions** | Implementation choices with real alternatives: storage, encoding, dependency, compatibility with the shipped system |
| **Context** | Trust boundaries touched, wire-format constraints, existing code to follow, open questions |

Do not write any file until all three are answered.

### 4. Read the guidance files

Always: `specs/mission.md`, `specs/tech-stack.md`.
When the phase touches proving, credentials or the transcript:
`docs/mdoc-format-notes.md` and the matching section of `docs/V2-PLAN.md`.
When it touches the gate: `templates/veridict-spec-gate.yml` and
`issuer/spec_gate.py`.

### 5. Create the spec directory

Name: `specs/YYYY-MM-DD-<feature-name>/` using today's date.

#### `requirements.md`
- **Scope**: what is and is not included; a table for any format, record or
  endpoint the phase defines
- **Decisions**: each choice, the alternative rejected, and why
- **Context**: trust boundaries, the files and patterns to follow, what the
  phase must not break in the deployed system

#### `plan.md`
- Numbered task groups, each independently implementable and testable
- Tests are part of the group that introduces the behaviour, not a final group
- Name the files each task creates or edits

#### `validation.md`
- **Automated**: the exact commands that must exit zero. `pytest` for the
  `veridict/` package and any service tests; `./scripts/validate_v2.sh` when
  proving or verification changed; the relevant `scripts/validate_*.py`
- **Manual**: the walkthrough, including the deployed flow on the demo
  repository when the phase changes anything a reviewer sees
- **Trust-boundary check**: no secret material beside untrusted code, no
  shared database credential, no forge-specific assumption inside the core
- **Definition of done**: roadmap items ticked, changelog updated, branch
  rebased onto `main`, nothing left in debug state

## Constraints

- Respect `specs/tech-stack.md`. No new dependency without the user's approval
  in the interview.
- Follow the patterns already in the codebase before inventing new ones.
- Keep the phase independently shippable. If the interview reveals it is two
  phases, say so and split the roadmap before writing the spec.
