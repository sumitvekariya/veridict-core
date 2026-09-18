"""Policy file: what a change must carry before it is acceptable."""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

POLICY_PATH = ".veridict/policy.toml"
TIERS = ("signed", "rerun", "certificate")
TIER_RANK = {name: i for i, name in enumerate(TIERS)}


class PolicyError(ValueError):
    pass


@dataclass
class Requirement:
    checker: str
    results: tuple[str, ...] = ("pass",)
    tier: str = "signed"


@dataclass
class Rule:
    name: str
    paths: list[str]
    authors: list[str]
    require: list[Requirement]


@dataclass
class Identity:
    issuer: str
    identity: str


@dataclass
class Policy:
    version: int
    keys: set[str] = field(default_factory=set)
    identities: list[Identity] = field(default_factory=list)
    allow_tree_match: bool = False
    unknown_author: str = "agent"
    rules: list[Rule] = field(default_factory=list)

    def applicable_rules(self, paths: list[str], author_class: str) -> list[Rule]:
        return [
            r for r in self.rules
            if author_class in r.authors and any(path_matches(p, f) for p in r.paths for f in paths)
        ]

    def rules_for_path(self, path: str) -> list[Rule]:
        return [r for r in self.rules if any(path_matches(p, path) for p in r.paths)]


def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    out = ""
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if pattern.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
            continue
        if pattern.startswith("**", i):
            out += ".*"
            i += 2
            continue
        if c == "*":
            out += "[^/]*"
        elif c == "?":
            out += "[^/]"
        else:
            out += re.escape(c)
        i += 1
    return re.compile("^" + out + "$")


def path_matches(pattern: str, path: str) -> bool:
    return bool(_glob_to_regex(pattern).match(path))


def _as_list(value: Any, what: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise PolicyError(f"{what} must be a list of strings")
    return list(value)


def parse(data: dict[str, Any]) -> Policy:
    if data.get("version") != 1:
        raise PolicyError("policy version must be 1")
    trust = data.get("trust", {})
    keys = set(_as_list(trust.get("keys", []), "trust.keys"))
    identities = []
    for ident in trust.get("identities", []):
        if not isinstance(ident, dict) or "issuer" not in ident or "identity" not in ident:
            raise PolicyError("each trust.identities entry needs issuer and identity")
        identities.append(Identity(str(ident["issuer"]), str(ident["identity"])))
    options = data.get("options", {})
    unknown_author = str(options.get("unknown_author", "agent"))
    if unknown_author not in ("human", "assisted", "agent"):
        raise PolicyError("options.unknown_author must be human, assisted or agent")
    rules: list[Rule] = []
    for i, raw in enumerate(data.get("rule", []), 1):
        if not isinstance(raw, dict):
            raise PolicyError(f"rule {i} must be a table")
        reqs: list[Requirement] = []
        for req in raw.get("require", []):
            if not isinstance(req, dict) or "checker" not in req:
                raise PolicyError(f"rule {i}: each requirement needs a checker")
            results = req.get("result", ["pass"])
            if isinstance(results, str):
                results = [results]
            tier = str(req.get("tier", "signed"))
            if tier not in TIERS:
                raise PolicyError(f"rule {i}: unknown tier {tier!r}")
            reqs.append(Requirement(str(req["checker"]), tuple(_as_list(results, f"rule {i} result")), tier))
        rules.append(Rule(
            name=str(raw.get("name", f"rule {i}")),
            paths=_as_list(raw.get("paths", ["**"]), f"rule {i} paths"),
            authors=_as_list(raw.get("authors", ["human", "assisted", "agent"]), f"rule {i} authors"),
            require=reqs,
        ))
    return Policy(1, keys, identities, bool(options.get("allow_tree_match", False)), unknown_author, rules)


def load(path: Path) -> Policy:
    try:
        data = tomllib.loads(path.read_text())
    except FileNotFoundError:
        raise PolicyError(f"policy file not found: {path}")
    except tomllib.TOMLDecodeError as exc:
        raise PolicyError(f"policy is not valid TOML: {exc}")
    return parse(data)


def tier_satisfies(actual: str, required: str) -> bool:
    return TIER_RANK.get(actual, -1) >= TIER_RANK.get(required, 0)
