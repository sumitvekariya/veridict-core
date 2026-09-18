---
name: changelog
description: Maintains CHANGELOG.md in the project root from git history. Use when the user invokes /changelog, asks to update or generate the changelog, or before merging a phase branch. Creates the file from scratch if missing (all commits grouped by date); otherwise prepends only commits newer than the last recorded date.
---

# Changelog

## Workflow

1. From the project root run:

```bash
python3 .claude/skills/changelog/scripts/changelog.py
```

2. The script handles both cases:
   - No `CHANGELOG.md`: reads full history and writes every date.
   - Existing file: finds the newest `## YYYY-MM-DD` heading, fetches newer
     commits, prepends new sections.

3. Review the wording, then commit `CHANGELOG.md` with the merge.

## Format

```markdown
# Changelog

## 2026-09-18

- Add constitution and multi-language spec-check research note
```

One `# Changelog` title, date headings newest first, one bullet per commit.
The script is idempotent: re-running with nothing new leaves the file alone.
