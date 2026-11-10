"""Shared repository-only snapshot, paired dispatch and accounting contracts."""
from __future__ import annotations
import hashlib
import fcntl
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
sys.dont_write_bytecode = True
import tarfile

ROLES = ("baseline", "candidate")
_SNAPSHOT_COMMITS = {}


def manifest(root):
    """Content and modes, including untracked files; callers supply a frozen tree."""
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            content = os.readlink(path).encode()
            mode = 0o120000
        elif path.is_file():
            content = path.read_bytes()
            mode = 0o755 if path.stat().st_mode & 0o111 else 0o644
        else:
            continue
        result[path.relative_to(root).as_posix()] = {"sha256": hashlib.sha256(content).hexdigest(), "mode": mode}
    return result


def identity(root, ref, repo):
    # A branch may move after capture; report the commit resolved for this snapshot.
    sha = _SNAPSHOT_COMMITS[root.resolve()]
    files = manifest(root)
    digest = hashlib.sha256(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {"ref": ref, "sha": sha, "content_sha256": digest, "files": files}


def snapshot_ref(repo, ref, dest, paths):
    sha = subprocess.run(["git", "rev-parse", "--verify", ("HEAD" if ref == "WORKTREE" else ref) + "^{commit}"],
                         cwd=repo, check=True, capture_output=True, text=True).stdout.strip()
    dest.mkdir(parents=True)
    if ref == "WORKTREE":
        proc = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", *paths],
                              cwd=repo, check=True, capture_output=True)
        for relative in sorted(set(os.fsdecode(p) for p in proc.stdout.split(b"\0") if p)):
            source = repo / relative
            if not source.exists() and not source.is_symlink():
                continue
            target = dest / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.is_symlink():
                resolved = source.resolve()
                if not resolved.is_relative_to(repo.resolve()):
                    raise ValueError(f"snapshot symlink escapes source: {relative}")
                target.symlink_to(os.readlink(source))
            elif source.is_file():
                shutil.copy2(source, target)
    else:
        proc = subprocess.run(["git", "archive", "--format=tar", sha, *paths], cwd=repo, check=True, capture_output=True)
        with tarfile.open(fileobj=io.BytesIO(proc.stdout)) as archive:
            links = []
            for member in archive:
                name = Path(member.name)
                if name.is_absolute() or ".." in name.parts:
                    raise ValueError("archive path escapes snapshot")
                target = dest / name
                if member.issym():
                    links.append((target, member.linkname))
                elif member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                elif member.isfile():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with archive.extractfile(member) as source:
                        target.write_bytes(source.read())
                    target.chmod(member.mode & 0o777)
                else:
                    raise ValueError("unsupported archive member")
            # Install links last: extraction can never follow a candidate-supplied link.
            for target, link in links:
                target.parent.mkdir(parents=True, exist_ok=True)
                if not (target.parent / link).resolve().is_relative_to(dest.resolve()):
                    raise ValueError("archive symlink escapes snapshot")
                target.symlink_to(link)
    for path in dest.rglob("*"):
        if path.is_symlink() and (not path.resolve().is_relative_to(dest.resolve()) or not path.exists()):
            raise ValueError(f"snapshot contains an external or unavailable symlink: {path.relative_to(dest)}")
    _SNAPSHOT_COMMITS[dest.resolve()] = sha
    return dest


def freeze_tasks(tasks, dest):
    """Freeze the selected fixtures, shared setup helpers, and golden graders before dispatch."""
    roots = {}
    frozen = []
    for task in tasks:
        source = task["dir"].parent
        if source not in roots:
            target = dest / str(len(roots))
            shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            roots[source] = target
        target = roots[source] / task["dir"].name
        item = {**task, "dir": target}
        if "seed_file" in item:
            item["seed_file"] = target / item["seed_file"].name
        frozen.append(item)
    return frozen


def pair_scored(trials):
    groups = {}
    for role in ROLES:
        for trial in trials[role]:
            if trial.get("superseded"):
                continue
            groups.setdefault((trial["task"], trial["repeat"]), {}).setdefault(role, []).append(trial)
    good = {key for key, group in groups.items()
            if all(len(group.get(role, [])) == 1 and group[role][0].get("status", "ok") == "ok"
                   and not group[role][0].get("provider_error") for role in ROLES)}
    return ({role: [t for t in trials[role] if not t.get("superseded") and (t["task"], t["repeat"]) in good] for role in ROLES},
            len(groups) - len(good))


def changed_paths(refs):
    a, b = (refs[role]["files"] for role in ROLES)
    return sorted(path for path in a.keys() | b.keys() if a.get(path) != b.get(path))


def guard_inputs(dispatch, roots):
    """Detect changes to frozen fixtures or role inputs, retaining trial accounting."""
    expected = [manifest(root) for root in roots]
    def guarded(*args):
        if any(manifest(root) != before for root, before in zip(roots, expected)):
            raise ValueError("frozen evaluation input changed before dispatch")
        trial = dispatch(*args)
        if any(manifest(root) != before for root, before in zip(roots, expected)):
            trial = {**trial, "status": "input_changed", "passed": False,
                     "note": "frozen evaluation input changed during trial"}
        return trial
    return guarded


def run_campaign(tasks, repeats, max_calls, max_tokens, dispatch, progress, *, resume=False, campaign_identity=None):
    """One writer per checkpoint, including across explicit resume invocations."""
    progress.parent.mkdir(parents=True, exist_ok=True)
    with progress.with_suffix(".lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("campaign checkpoint already has an active writer") from exc
        return _run_campaign(tasks, repeats, max_calls, max_tokens, dispatch, progress,
                             resume=resume, campaign_identity=campaign_identity)


def _run_campaign(tasks, repeats, max_calls, max_tokens, dispatch, progress, *, resume=False, campaign_identity=None):
    """Limits are checked between trials; unknown consumption stops further dispatch."""
    if repeats < 1 or max_calls < 1 or max_tokens < 1:
        raise ValueError("repeats and spend ceilings must be positive")
    trials, calls, tokens, aborted = [], 0, 0, None
    active = None
    if resume:
        checkpoint = json.loads(progress.read_text())
        if checkpoint.get("schema") != "tabilet.eval-checkpoint/v1":
            raise ValueError("unsupported checkpoint schema")
        if not campaign_identity or checkpoint.get("identity") != campaign_identity:
            raise ValueError("resume input identity mismatch")
        if checkpoint.get("limits") != {"calls": max_calls, "tokens": max_tokens}:
            raise ValueError("resume requires the original cumulative spending limits")
        if checkpoint.get("active_trial") or any(not t.get("tokens_known") or
                type(t.get("calls_used", t.get("turns"))) is not int for t in checkpoint["trials"]):
            raise ValueError("resume blocked: unresolved unknown consumption")
        trials = checkpoint["trials"]
        calls = sum(t.get("calls_used", t.get("turns")) for t in trials)
        tokens = sum(t["tokens"] for t in trials)
        # Only failed infrastructure attempts may be retried. Preserve them and their spend.
        for trial in trials:
            if trial.get("status", "ok") not in ("ok", "skipped"):
                trial["superseded"] = True
    def save():
        payload = {"schema": "tabilet.eval-checkpoint/v1", "identity": campaign_identity,
                   "limits": {"calls": max_calls, "tokens": max_tokens}, "trials": trials, "calls_used_lower_bound": calls, "tokens_used_lower_bound": tokens,
                   "aborted": aborted, "active_trial": active, "dispatch_attempts": len(trials) + bool(active)}
        progress.parent.mkdir(parents=True, exist_ok=True)
        temporary = progress.with_suffix(".tmp")
        with temporary.open("w") as stream:
            stream.write(json.dumps(payload, indent=2) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(progress)
        descriptor = os.open(progress.parent, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    try:
        for repeat in range(1, repeats + 1):
            for task in tasks:
                for role in ROLES:
                    if any(t["task"] == task["name"] and t["repeat"] == repeat and t["role"] == role
                           and not t.get("superseded") and t.get("status", "ok") in ("ok", "skipped") for t in trials):
                        continue
                    peer_skipped = any(t["task"] == task["name"] and t["repeat"] == repeat
                                       and t.get("status") == "skipped" for t in trials)
                    if peer_skipped:
                        trials.append({"task": task["name"], "category": task["category"], "role": role,
                                       "repeat": repeat, "status": "skipped", "passed": False, "clean": None,
                                       "calls_used": 0, "turns": None, "tokens": 0, "tokens_known": True,
                                       "duration_sec": 0, "reasons": ["paired trial skipped"], "failed_checks": []})
                        save()
                        continue
                    if calls >= max_calls or tokens >= max_tokens:
                        aborted = f"ceiling reached ({calls} calls, {tokens} known tokens)"
                        return trials, calls, tokens, aborted
                    active = {"task": task["name"], "role": role, "repeat": repeat, "usage": "unknown", "calls_reserved": 1}
                    save()  # Durable dispatch intent; a killed process cannot look like an unspent trial.
                    remaining = max_calls - calls
                    try:
                        trial = dispatch(task, role, repeat, remaining)
                    except (Exception, KeyboardInterrupt, SystemExit) as exc:
                        trial = {"task": task["name"], "role": role, "repeat": repeat, "category": task["category"],
                                 "status": "infrastructure_error", "passed": False, "clean": None,
                                 "turns": None, "tokens": 0, "tokens_known": False,
                                 "failed_checks": [], "note": f"{type(exc).__name__}: {str(exc)[:500]}", "duration_sec": None}
                    trials.append(trial)
                    used = trial.get("calls_used", trial.get("turns"))
                    if type(used) is int:
                        calls += max(0, used)
                    tokens += trial.get("tokens") or 0
                    active = None
                    zero_skip = (trial.get("status") == "skipped" and used == 0
                                 and trial.get("tokens") == 0 and trial.get("tokens_known") is True)
                    if zero_skip:
                        pass
                    elif trial.get("status", "ok") != "ok" or trial.get("provider_error"):
                        aborted = f"unscored trial: {task['name']} ({role}, repeat {repeat}): {trial.get('note') or trial.get('status', 'provider failure')}"
                    elif not trial.get("tokens_known") or used is None:
                        aborted = f"unknown consumption: {task['name']} ({role}, repeat {repeat}); further dispatch stopped"
                    save()
                    if aborted:
                        return trials, calls, tokens, aborted
        return trials, calls, tokens, aborted
    finally:
        save()
