#!/usr/bin/env python3
"""Optional approval alerts; standard library only, never an approval service."""
from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import unicodedata
import urllib.error
import urllib.request


TIMEOUT = 10
MAX_INPUT = 8192
MAX_RESPONSE = 16384


class NotificationError(Exception):
    def __init__(self, message: str, outcome: str = "failed"):
        super().__init__(message)
        self.outcome = outcome


def address(value: str) -> str:
    """One bare address, with a case-normalized domain and no header syntax."""
    if not isinstance(value, str) or len(value) > 254 or value.count("@") != 1:
        raise NotificationError("Expected one bare email address.")
    local, domain = value.split("@")
    if (not re.fullmatch(r"[A-Za-z0-9.!#$%&'+/=?^_`{|}~-]{1,64}", local)
            or local.startswith(".") or local.endswith(".") or ".." in local
            or len(domain) > 253
            or not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?"
                                r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)+", domain)
            or any(len(part) > 63 for part in domain.split("."))):
        raise NotificationError("Expected one bare email address.")
    return local + "@" + domain.lower()


def account_paths() -> tuple[Path, Path]:
    def base(name: str, default: str) -> Path:
        value = os.environ.get(name)
        if value and Path(value).is_absolute():
            return Path(value)
        try:
            return Path.home() / default
        except (OSError, RuntimeError):
            raise NotificationError("Email account directories could not be resolved.") from None
    config = base("XDG_CONFIG_HOME", ".config")
    state = base("XDG_STATE_HOME", ".local/state")
    return config / "tabilet/email.json", state / "tabilet/email-notifications"


def outside_project(path: Path, project_root: Path) -> None:
    try:
        resolved = path.resolve()
        project = project_root.resolve()
    except (OSError, RuntimeError):
        raise NotificationError("Email configuration or state path could not be resolved.") from None
    try:
        resolved.relative_to(project)
    except ValueError:
        return
    raise NotificationError("Email configuration and state must stay outside the project.")


def load_profile(recipient: str, project_root: Path) -> tuple[dict, str, Path]:
    config, state = account_paths()
    outside_project(config, project_root)
    outside_project(state, project_root)
    try:
        if not config.is_file() or config.stat().st_size > MAX_INPUT:
            raise NotificationError("Email configuration is missing or invalid.")
        if os.name == "posix" and config.stat().st_mode & 0o077:
            raise NotificationError("Email configuration must be private (chmod 600).")
        profile = json.loads(config.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError, RecursionError):
        raise NotificationError("Email configuration is missing or invalid.") from None
    if (not isinstance(profile, dict)
            or set(profile) != {"account_id", "from", "allowed_recipients", "token_env"}
            or not isinstance(profile["account_id"], str)
            or not re.fullmatch(r"[a-fA-F0-9]{32}", profile["account_id"])):
        raise NotificationError("Email configuration has invalid fields.")
    profile["from"] = address(profile["from"])
    allowed = profile["allowed_recipients"]
    if not isinstance(allowed, list) or not allowed:
        raise NotificationError("Configure permitted email recipients first.")
    if recipient not in {address(item) for item in allowed}:
        raise NotificationError("Email recipient is not permitted by the account configuration.")
    name = profile["token_env"]
    if not isinstance(name, str) or not re.fullmatch(r"[A-Z_][A-Z0-9_]*", name):
        raise NotificationError("Configure the sender token environment variable name.")
    token = os.environ.get(name, "")
    if not token or len(token) > 4096 or not re.fullmatch(r"[\x21-\x7e]+", token):
        raise NotificationError("Sender token is missing or invalid; configure it outside the project.")
    return profile, token, state


def validate_event(event: dict) -> dict:
    required = {"event", "run_id", "request_id", "project", "milestone", "reason"}
    if (not isinstance(event, dict) or not required <= set(event)
            or set(event) - required - {"session_id"}
            or event["event"] != "approval_required"):
        raise NotificationError("Expected a structured approval_required event.")
    for key, limit in (("run_id", 128), ("project", 120), ("milestone", 80),
                       ("reason", 500), ("session_id", 128)):
        if key not in event:
            continue
        value = event[key]
        if (not isinstance(value, str) or not value.strip() or len(value) > limit
                or any(unicodedata.category(char) in {"Cc", "Zl", "Zp"}
                       or char in "\u061c\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069"
                       for char in value)):
            raise NotificationError("Approval alert fields must be bounded single-line text.")
        try:
            value.encode("utf-8")
        except UnicodeError:
            raise NotificationError("Approval alert text must be valid UTF-8.") from None
    if not isinstance(event["request_id"], str) or not re.fullmatch(r"[a-f0-9]{64}", event["request_id"]):
        raise NotificationError("Approval request_id must be the complete proposal SHA256.")
    return event


def message(event: dict, recipient: str, sender: str, token: str) -> dict:
    subject = "Tabilet: approval required — " + event["project"] + " / " + event["milestone"]
    body = (f"Project: {event['project']}\nMilestone/task: {event['milestone']}\n"
            f"Reason: {event['reason']}\n")
    if "session_id" in event:
        body += f"Session: {event['session_id']}\n"
    body += "Review the exact proposal and respond in your existing agent session.\n"
    def redact(text: str) -> str:
        text = text.replace(token, "[redacted]")
        return re.sub(r"(?i)\b(?:bearer\s+\S+|(?:password|secret|token|api[_ -]?key)\s*[:=]\s*\S+)",
                      "[redacted]", text)
    return {"to": recipient, "from": sender, "subject": redact(subject), "text": redact(body)}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def deliver(profile: dict, token: str, payload: dict) -> str:
    url = "https://api.cloudflare.com/client/v4/accounts/" + profile["account_id"] + "/email/sending/send"
    encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=encoded, method="POST", headers={
        "Authorization": "Bearer " + token, "Content-Type": "application/json",
    })
    try:
        # Default HTTPS certificate verification remains enabled. Never forward
        # the Authorization header through an HTTP redirect.
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=TIMEOUT) as response:
            raw = response.read(MAX_RESPONSE + 1)
            if not 200 <= response.status < 300 or len(raw) > MAX_RESPONSE:
                raise NotificationError("Cloudflare delivery response could not be verified.", "unknown")
    except urllib.error.HTTPError as error:
        status = error.code
        if error.fp is not None:
            error.close()
        outcome = "failed" if 300 <= status < 500 and status != 408 else "unknown"
        raise NotificationError(f"Cloudflare rejected the alert or could not confirm delivery (HTTP {status}).", outcome) from None
    except (OSError, urllib.error.URLError, ValueError, http.client.HTTPException):
        raise NotificationError("Email delivery is uncertain; inspect provider logs before retrying.", "unknown") from None
    try:
        result = json.loads(raw.decode("utf-8"))
        if not isinstance(result, dict) or result.get("success") is not True:
            raise NotificationError("Cloudflare did not accept the approval alert.")
        groups = result.get("result")
        if not isinstance(groups, dict):
            raise ValueError
        for field in ("delivered", "queued", "permanent_bounces", "suppressed_recipients"):
            if field in groups and (not isinstance(groups[field], list)
                                    or any(not isinstance(item, str) for item in groups[field])):
                raise ValueError
            if field in groups:
                try:
                    groups[field] = [address(item) for item in groups[field]]
                except NotificationError:
                    raise ValueError from None
        recipient = payload["to"]
        if recipient in groups.get("permanent_bounces", []) or recipient in groups.get("suppressed_recipients", []):
            raise NotificationError("Cloudflare bounced or suppressed the approval alert.")
        if recipient in groups.get("delivered", []):
            return "accepted"
        if recipient in groups.get("queued", []):
            return "queued"
        raise ValueError
    except (ValueError, UnicodeError, TypeError, RecursionError):
        raise NotificationError("Email delivery response is uncertain; inspect provider logs before retrying.", "unknown") from None


def read_json_input(limit: int, outcome: str = "failed"):
    """Bound bytes and decode explicitly, independently of terminal settings."""
    try:
        stream = getattr(sys.stdin, "buffer", sys.stdin)
        raw = stream.read(limit + 1)
        if isinstance(raw, str):
            raw = raw.encode("utf-8")
        if len(raw) > limit:
            raise NotificationError("Approval alert input is too large.", outcome)
        return json.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError, RecursionError):
        raise NotificationError("Approval alert input must be valid UTF-8 JSON.", outcome) from None


def delivery_worker() -> int:
    """Private subprocess entrypoint; secrets arrive only over inherited pipes."""
    try:
        job = read_json_input(MAX_INPUT + MAX_RESPONSE, "unknown")
        if not isinstance(job, dict) or set(job) != {"profile", "token", "payload"}:
            raise NotificationError("Email delivery worker input is invalid.", "unknown")
        outcome = deliver(job["profile"], job["token"], job["payload"])
        print(json.dumps({"delivery": outcome}))
        return 0
    except NotificationError as error:
        # The parent supplies the public diagnostic, never provider/secret text.
        print(json.dumps({"delivery": error.outcome}))
        return 2
    except (OSError, ValueError, TypeError, KeyError, RecursionError, http.client.HTTPException):
        print(json.dumps({"delivery": "unknown"}))
        return 2


def deliver_bounded(profile: dict, token: str, payload: dict) -> str:
    """One supervised network attempt, including DNS and slow response reads."""
    job = json.dumps({"profile": profile, "token": token, "payload": payload}).encode("utf-8")
    deadline = time.monotonic() + TIMEOUT
    with subprocess.Popen([sys.executable, "-I", str(Path(__file__).resolve()), "--delivery-worker"],
                          stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL) as worker:
        try:
            raw, _ = worker.communicate(job, timeout=max(0, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            worker.kill()
            worker.communicate()
            raise NotificationError("Email delivery deadline reached; inspect provider logs before retrying.", "unknown") from None
        except BaseException:
            # Interruptions must not leave a credentialed network worker behind.
            worker.kill()
            worker.communicate()
            raise
        try:
            if len(raw) > MAX_INPUT:
                raise ValueError
            result = json.loads(raw.decode("utf-8"))
            if not isinstance(result, dict) or set(result) != {"delivery"}:
                raise ValueError
            outcome = result["delivery"]
            if worker.returncode == 0 and outcome in {"accepted", "queued"}:
                return outcome
            if worker.returncode == 2 and outcome == "failed":
                raise NotificationError("Cloudflare did not accept the approval alert.")
        except (UnicodeError, ValueError, TypeError, RecursionError):
            pass
    raise NotificationError("Email delivery is uncertain; inspect provider logs before retrying.", "unknown")


def sync_directory(directory: Path) -> None:
    if os.name == "posix":
        fd = os.open(directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def write_record(path: Path, record: dict) -> None:
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".email-", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(record, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        sync_directory(path.parent)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def send(event: dict, recipient: str, project_root: Path) -> dict:
    event = validate_event(event)
    recipient = address(recipient)
    profile, token, root = load_profile(recipient, project_root)
    identity = json.dumps([event["run_id"], event["request_id"], recipient], separators=(",", ":"))
    key = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    root.chmod(0o700)
    outside_project(root, project_root)
    path = root / (key + ".json")
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        try:
            if path.is_symlink() or path.stat().st_size > MAX_INPUT:
                raise ValueError
            cached = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(cached, dict) and cached.get("outcome") in {"accepted", "queued"}:
                return {"status": "duplicate", "delivery": cached["outcome"]}
            if isinstance(cached, dict) and cached.get("outcome") == "failed":
                raise NotificationError("This approval alert was already attempted and failed; it will not retry automatically.")
        except (OSError, ValueError, UnicodeError, RecursionError):
            pass
        raise NotificationError("This approval alert was already attempted; inspect provider logs before retrying.", "unknown") from None
    record = {"outcome": "unknown"}
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(record, stream)
        stream.flush()
        os.fsync(stream.fileno())
    sync_directory(root)
    try:
        outcome = deliver_bounded(profile, token, message(event, recipient, profile["from"], token))
    except NotificationError as error:
        write_record(path, {"outcome": error.outcome})
        raise
    # If persistence fails after the POST, the original unknown reservation
    # remains. The next invocation never silently replays that request.
    write_record(path, {"outcome": outcome})
    return {"status": "sent", "delivery": outcome}


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv == ["--delivery-worker"]:
        return delivery_worker()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("check", "send"))
    parser.add_argument("--to", required=True)
    parser.add_argument("--project-root", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        recipient = address(args.to)
        if args.operation == "check":
            load_profile(recipient, args.project_root)
            result = {"status": "ready", "network_checked": False}
        else:
            event = read_json_input(MAX_INPUT)
            result = send(event, recipient, args.project_root)
        print(json.dumps(result))
        return 0
    except NotificationError as error:
        print(json.dumps({"status": "unavailable", "delivery": error.outcome, "error": str(error)}))
        return 2
    except OSError:
        print(json.dumps({"status": "unavailable", "delivery": "unknown", "error": "Email state could not be persisted; inspect provider logs before retrying."}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
