#!/usr/bin/env python3
"""Command-line interface for the optional Tabilet API controller."""
from __future__ import annotations

import argparse
import pathlib


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tabilet", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    chat = commands.add_parser("chat", help="plan, approve, and execute one bounded horizon")
    chat.add_argument("project", type=pathlib.Path)
    chat.add_argument("--image", required=True, help="image already present in the local Docker daemon")
    chat.add_argument("--operation", choices=("init", "propose", "reconcile"))
    chat.add_argument("--request", help="planning request; omit to enter it interactively")
    _add_model_options(chat)

    status = commands.add_parser("status", help="read live project and horizon state")
    status.add_argument("project", type=pathlib.Path)

    resume = commands.add_parser("resume", help="reconcile and continue a confirmed horizon")
    resume.add_argument("project", type=pathlib.Path)
    resume.add_argument("--receipt", help="receipt UUID when more than one horizon is open")
    _add_model_options(resume)

    extend = commands.add_parser("extend-limit", help="confirm a higher cap for a paused horizon")
    extend.add_argument("project", type=pathlib.Path)
    extend.add_argument("--receipt", help="receipt UUID when more than one horizon is open")
    extend.add_argument(
        "--limit", required=True,
        choices=("max_rows", "max_provider_attempts", "max_turns_per_row", "max_commits", "max_runtime_seconds"),
    )
    extend.add_argument("--value", required=True, type=int)
    return parser


def _add_model_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--provider", choices=("openai", "anthropic"))
    parser.add_argument("--model")
    parser.add_argument("--api-base")
    parser.add_argument("--api-key")
    parser.add_argument("--max-turns", type=int, default=40)
    parser.add_argument("--max-tokens", type=int, default=16000)
    parser.add_argument("--api-timeout", type=int, default=120)
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument("--max-history-chars", type=int, default=500000)
    parser.add_argument("--temperature", type=float)
    parser.add_argument("--audit-db")
    parser.add_argument("--audit-capture", choices=("metadata", "relevant"))
    parser.add_argument("--allow-dangerous", action="store_true")


def _runner_args(core, options, project: pathlib.Path):
    argv = [str(project)]
    mapping = (
        ("provider", "--provider"), ("model", "--model"), ("api_base", "--api-base"),
        ("api_key", "--api-key"), ("max_turns", "--max-turns"),
        ("max_tokens", "--max-tokens"), ("api_timeout", "--api-timeout"),
        ("max_retries", "--max-retries"), ("max_history_chars", "--max-history-chars"),
        ("temperature", "--temperature"), ("audit_db", "--audit-db"),
        ("audit_capture", "--audit-capture"),
    )
    for name, flag in mapping:
        value = getattr(options, name, None)
        if value is not None:
            argv.extend((flag, str(value)))
    argv.extend(("--tool-timeout", "300", "--max-tool-output", "24000"))
    parsed = core.parse_args(argv)
    if not parsed.model:
        core.fail("Set LLM_MODEL or pass --model.", 2)
    # Controller shell commands always execute in Docker. Dangerous command
    # filtering is a separate explicit option and never inherited from runner env.
    parsed.allow_dangerous = bool(getattr(options, "allow_dangerous", False))
    return parsed


def _receipt_candidates(core, project: pathlib.Path, store, *, receipt_id=None):
    from tabilet_controller import load_status_module
    status = load_status_module()
    repo = pathlib.Path(project).expanduser().resolve(strict=True)
    receipts, errors = status._private_receipts(core, repo, store)
    if errors:
        core.fail("Cannot choose a horizon receipt safely: " + "; ".join(errors), 25)
    if receipt_id:
        matches = [item for item in receipts if item["receipt"].get("receipt_id") == receipt_id]
        if not matches:
            core.fail(f"No private receipt {receipt_id} belongs to {repo}.", 18)
        return matches
    active = [item for item in receipts if item["receipt"].get("state") != "completed"]
    if len(active) > 1:
        choices = ", ".join(item["receipt"].get("receipt_id", "unknown") for item in active)
        core.fail(f"More than one open horizon exists ({choices}); select one with --receipt.", 2)
    if active:
        return active
    completed = [item for item in receipts if item["receipt"].get("state") == "completed"]
    return completed[:1]


def _manual_evidence(receipt, input_fn=input):
    supplied = {}
    prior = receipt.get("closure", {}).get("milestones", {})
    for milestone in receipt.get("approved_horizon", []):
        identity = milestone.get("id")
        required = milestone.get("manual_evidence", [])
        if not required:
            continue
        answers = {
            item.get("criterion"): item.get("value")
            for item in prior.get(identity, {}).get("manual_evidence", [])
            if isinstance(item, dict) and item.get("source") == "user"
            and isinstance(item.get("criterion"), str) and isinstance(item.get("value"), str)
        }
        for criterion in required:
            if criterion in answers and answers[criterion].strip():
                continue
            answer = input_fn(f"Manual evidence for {identity}: {criterion}\n> ")
            if answer.strip():
                answers[criterion] = answer
        if answers:
            supplied[identity] = answers
    return supplied


def main(argv=None) -> int:
    options = _parser().parse_args(argv)
    from tabilet_controller import (
        chat_session, extend_horizon_limit, load_proposal_module,
        load_runner_core, resume_horizon, status_project,
    )

    core = load_runner_core()
    project = options.project.expanduser().resolve()
    if options.command == "status":
        status_project(core, project)
        return 0

    if options.command == "chat":
        operation = options.operation
        if operation is None:
            output = print
            output("Choose the planning contract: init, propose, or reconcile.")
            operation = input("Operation: ").strip().lower()
            if operation not in {"init", "propose", "reconcile"}:
                core.fail("Choose exactly init, propose, or reconcile.", 2)
        request = options.request
        if request is None:
            request = input("What should this planning horizon deliver?\n> ")
        args = _runner_args(core, options, project)
        result = chat_session(core, args, project, operation, request, options.image)
        if result.get("state") == "completed" or result.get("status") in {"cancelled", "rejected"}:
            return 0
        return 17

    store = load_proposal_module().ReceiptStore()
    candidates = _receipt_candidates(core, project, store, receipt_id=options.receipt)
    if not candidates:
        print(f"No horizon receipt exists for {project}.")
        return 0
    selected = candidates[0]
    receipt = selected["receipt"]
    path = pathlib.Path(selected["path"])
    if options.command == "extend-limit":
        result = extend_horizon_limit(
            core, project, path, options.limit, options.value, receipt_store=store,
        )
        print(f"Limit extension status: {result.get('status')}.")
        return 0 if result.get("status") in {"running", "unchanged"} else 17

    args = _runner_args(core, options, project)
    evidence = _manual_evidence(receipt)
    result = resume_horizon(
        core, args, project, path, receipt_store=store,
        manual_evidence=evidence,
    )
    return 0 if result.get("state") == "completed" else 17


if __name__ == "__main__":
    raise SystemExit(main())
