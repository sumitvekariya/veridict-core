"""veridict command line."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import AUTHORSHIP_PREDICATE, VERIFICATION_PREDICATE, __version__
from .adapters import python_checks
from .attest import KeySigner, Signer, attest_authorship, attest_results
from .authorship import authorship_predicate, class_from_trailers, detect_agent_env, install_hook
from .gitrepo import GitError, Repo
from .keys import default_key_path, generate, load_private
from .notes import read_entries
from .policy import POLICY_PATH, PolicyError, load as load_policy
from .statement import parse_statement
from .verify import verify_range

EXIT_OK, EXIT_UNMET, EXIT_ERROR = 0, 1, 2


class CliError(Exception):
    pass


def _repo(args: argparse.Namespace) -> Repo:
    try:
        return Repo.discover(Path(args.repo) if args.repo else None)
    except GitError as exc:
        raise CliError(f"not a git repository: {exc}") from exc


def _signer(args: argparse.Namespace) -> Signer:
    if args.sign == "sigstore":
        from . import sigstore_backend

        try:
            return sigstore_backend.SigstoreSigner(identity_token=args.identity_token, staging=args.staging)
        except sigstore_backend.SigstoreUnavailable as exc:
            raise CliError(str(exc)) from exc
    path = Path(args.key) if args.key else default_key_path()
    if not path.exists():
        raise CliError(f"no signing key at {path}; run `veridict keygen` or pass --key")
    return KeySigner(load_private(path))


def _add_signing_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--sign", choices=["key", "sigstore"], default="key")
    p.add_argument("--key", help="Ed25519 private key PEM (default: ~/.config/veridict/key.pem)")
    p.add_argument("--identity-token", help="OIDC token for Sigstore; default: ambient credential")
    p.add_argument("--staging", action="store_true", help="use Sigstore staging infrastructure")
    p.add_argument("--rev", default="HEAD")


def cmd_keygen(args: argparse.Namespace) -> int:
    kid, path = generate(Path(args.out) if args.out else None)
    print(f"keyid {kid}\nprivate {path}\npublic {path.with_suffix('.pub')}")
    print(f"add to {POLICY_PATH}:  keys = [\"{kid}\"]")
    return EXIT_OK


def cmd_attest(args: argparse.Namespace) -> int:
    repo = _repo(args)
    if args.adapter != "python":
        raise CliError(f"unknown adapter {args.adapter}")
    which = tuple(args.only.split(",")) if args.only else python_checks.CHECKERS
    results = python_checks.run_all(repo, args.paths or None, which, timeout=args.timeout)
    signer = _signer(args)
    lines = attest_results(repo, args.rev, results, signer)
    for r in results:
        print(f"{r.checker:<10} {r.result:<8} {r.summary}")
    print(f"{len(lines)} attestation(s) appended to {repo.rev_parse(args.rev)[:12]} signed by {signer.name}")
    if args.json:
        print(json.dumps([r.to_predicate() for r in results], indent=2))
    return EXIT_OK if all(r.result != "fail" for r in results) or not args.fail_on_fail else EXIT_UNMET


def cmd_authorship(args: argparse.Namespace) -> int:
    repo = _repo(args)
    if args.infer:
        inferred = class_from_trailers(repo.trailers(args.rev))
        if not inferred:
            print("no authorship trailer on the commit; nothing attested")
            return EXIT_OK
        predicate = authorship_predicate(inferred[0], agent=inferred[1], source="ci-inference", strength="weak")
    else:
        author_class = args.author_class
        agent = args.agent or (detect_agent_env() if author_class != "human" else None)
        predicate = authorship_predicate(author_class, agent=agent, model=args.model, session=args.session,
                                         source=args.source, strength=args.strength)
    attest_authorship(repo, args.rev, predicate, _signer(args))
    print(f"authorship {predicate['authorClass']} ({predicate['source']}, {predicate['strength']}) attested")
    return EXIT_OK


def cmd_verify(args: argparse.Namespace) -> int:
    repo = _repo(args)
    policy_path = Path(args.policy) if args.policy else repo.root / POLICY_PATH
    try:
        policy = load_policy(policy_path)
    except PolicyError as exc:
        raise CliError(str(exc)) from exc
    report = verify_range(repo, args.spec, policy)
    print(report.to_json() if args.json else report.render())
    return EXIT_OK if report.ok else EXIT_UNMET


def _describe(statement: dict[str, Any]) -> str:
    p = statement["predicate"]
    if statement["predicateType"] == VERIFICATION_PREDICATE:
        return f"verification {p.get('checker', {}).get('name')}={p.get('result')} tier={p.get('tier')}"
    if statement["predicateType"] == AUTHORSHIP_PREDICATE:
        return f"authorship {p.get('authorClass')} ({p.get('source')}, {p.get('strength')})"
    return statement["predicateType"]


def cmd_show(args: argparse.Namespace) -> int:
    repo = _repo(args)
    commit = repo.rev_parse(args.rev)
    parsed = read_entries(repo, commit)
    print(f"{commit} : {len(parsed.entries)} attestation(s)")
    for i, entry in enumerate(parsed.entries, 1):
        try:
            if entry.kind == "dsse":
                statement = parse_statement(entry.envelope.payload)
                signer = entry.signer.get("keyid", "?")
            else:
                import base64

                statement = parse_statement(base64.b64decode(entry.bundle["dsseEnvelope"]["payload"]))
                signer = "sigstore"
            print(f"  {i}. [{entry.kind}] {_describe(statement)}  signer={signer}")
        except (ValueError, KeyError) as exc:
            print(f"  {i}. [{entry.kind}] unreadable: {exc}")
    for w in parsed.warnings:
        print(f"  warning: {w}")
    return EXIT_OK


def cmd_export(args: argparse.Namespace) -> int:
    repo = _repo(args)
    commit = repo.rev_parse(args.rev)
    print(json.dumps([json.loads(line) for line in repo.notes_read(commit)], indent=2))
    return EXIT_OK


def cmd_push(args: argparse.Namespace) -> int:
    repo = _repo(args)
    try:
        repo.push_notes(args.remote)
    except GitError as exc:
        raise CliError(str(exc)) from exc
    print(f"notes pushed to {args.remote}")
    return EXIT_OK


def cmd_fetch(args: argparse.Namespace) -> int:
    repo = _repo(args)
    found = repo.fetch_notes(args.remote)
    print(f"notes fetched from {args.remote}" if found else f"{args.remote} has no veridict notes yet")
    return EXIT_OK


def cmd_hook(args: argparse.Namespace) -> int:
    repo = _repo(args)
    try:
        path = install_hook(repo, force=args.force, allow_shared=args.shared)
    except (FileExistsError, PermissionError) as exc:
        raise CliError(str(exc)) from exc
    print(f"installed {path}")
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="veridict", description="Verification evidence for AI-written code, stored in git.")
    parser.add_argument("--version", action="version", version=f"veridict {__version__}")
    parser.add_argument("--repo", help="path inside the repository (default: cwd)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("keygen", help="create an Ed25519 signing key"); p.add_argument("--out"); p.set_defaults(func=cmd_keygen)

    p = sub.add_parser("attest", help="run checkers and record signed verdicts on a commit")
    p.add_argument("--adapter", default="python"); p.add_argument("--paths", nargs="*")
    p.add_argument("--only", help="comma-separated subset of mypy,pytest,crosshair")
    p.add_argument("--timeout", type=int, default=python_checks.DEFAULT_TIMEOUT)
    p.add_argument("--json", action="store_true"); p.add_argument("--fail-on-fail", action="store_true", help="exit 1 when any checker fails")
    _add_signing_args(p); p.set_defaults(func=cmd_attest)

    p = sub.add_parser("authorship", help="record who or what authored a commit")
    p.add_argument("--class", dest="author_class", choices=["human", "assisted", "agent"], default="assisted")
    p.add_argument("--agent"); p.add_argument("--model"); p.add_argument("--session")
    p.add_argument("--source", choices=["hook", "trailer", "ci-inference"], default="hook")
    p.add_argument("--strength", choices=["strong", "weak"], default="strong")
    p.add_argument("--infer", action="store_true", help="derive a weak attestation from commit trailers")
    _add_signing_args(p); p.set_defaults(func=cmd_authorship)

    p = sub.add_parser("verify", help="evaluate the policy for a revision or range")
    p.add_argument("spec"); p.add_argument("--policy"); p.add_argument("--json", action="store_true"); p.set_defaults(func=cmd_verify)

    p = sub.add_parser("show", help="list attestations on a revision"); p.add_argument("rev", nargs="?", default="HEAD"); p.set_defaults(func=cmd_show)
    p = sub.add_parser("export", help="dump note lines for a revision as JSON"); p.add_argument("rev", nargs="?", default="HEAD"); p.set_defaults(func=cmd_export)
    p = sub.add_parser("push", help="push the notes ref"); p.add_argument("remote", nargs="?", default="origin"); p.set_defaults(func=cmd_push)
    p = sub.add_parser("fetch", help="fetch and merge the notes ref"); p.add_argument("remote", nargs="?", default="origin"); p.set_defaults(func=cmd_fetch)
    p = sub.add_parser("hook", help="manage git hooks"); p.add_argument("action", choices=["install"]); p.add_argument("--force", action="store_true", help="replace a foreign hook")
    p.add_argument("--shared", action="store_true", help="install into core.hooksPath for every repository")
    p.set_defaults(func=cmd_hook)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except CliError as exc:
        print(f"veridict: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except GitError as exc:
        print(f"veridict: git: {exc}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
