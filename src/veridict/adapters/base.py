from __future__ import annotations

import platform
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def now_rfc3339() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class CheckResult:
    checker: str
    version: str
    result: str  # pass | fail | skipped
    paths: list[str]
    command: str
    summary: str
    started_at: str
    finished_at: str
    counterexamples: list[dict[str, str]] = field(default_factory=list)
    tier: str = "signed"

    def to_predicate(self) -> dict[str, Any]:
        evidence: dict[str, Any] = {"summary": self.summary}
        if self.counterexamples:
            evidence["counterexamples"] = self.counterexamples
        return {
            "checker": {"name": self.checker, "version": self.version},
            "tier": self.tier,
            "result": self.result,
            "scope": {"paths": self.paths},
            "command": self.command,
            "environment": {"python": platform.python_version()},
            "evidence": evidence,
            "startedAt": self.started_at,
            "finishedAt": self.finished_at,
        }
