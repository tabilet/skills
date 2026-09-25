#!/usr/bin/env python3
"""Install canonical Tabilet skill bundles and a generated hash manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import shutil
import stat
import sys
import tempfile
import uuid


BUNDLE_NAMES = (
    "memory-bank-archive",
    "memory-bank-goal",
    "memory-bank-init",
    "memory-bank-next",
    "memory-bank-propose",
    "memory-bank-reconcile",
    "memory-bank-upgrade",
)
CONTROLLER_FILES = (
    "tackle-memory-bank-api-loop",
    "tabilet_audit.py",
    "tabilet_index.py",
    "tabilet_container.py",
    "tabilet_controller.py",
    "tabilet_planning.py",
    "tabilet_proposal.py",
    "tabilet_horizon.py",
    "tabilet_recovery.py",
    "tabilet_status.py",
    "tabilet_cli.py",
)
MANIFEST_NAME = "manifest.json"
MANIFEST_SCHEMA = "tabilet.skill-bundle-manifest/v1"


class InstallError(RuntimeError):
    """The canonical skills cannot be installed safely."""


def regular_files(root: pathlib.Path):
    for directory, names, files in os.walk(root, topdown=True, followlinks=False):
        base = pathlib.Path(directory)
        for name in list(names):
            path = base / name
            if path.is_symlink():
                raise InstallError(f"symbolic link in canonical bundle: {path}")
        for name in files:
            path = base / name
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode):
                raise InstallError(f"non-regular file in canonical bundle: {path}")
            yield path


def build_manifest(bundle_root: pathlib.Path) -> dict:
    entries = {}
    for name in BUNDLE_NAMES:
        bundle = bundle_root / name
        if bundle.is_symlink() or not bundle.is_dir():
            raise InstallError(f"canonical bundle is missing: {name}")
        for path in regular_files(bundle):
            relative = path.relative_to(bundle_root).as_posix()
            entries[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    required = {f"{name}/SKILL.md" for name in BUNDLE_NAMES}
    if not required.issubset(entries):
        missing = sorted(required - set(entries))
        raise InstallError(f"canonical skill entrypoints are missing: {', '.join(missing)}")
    return {
        "schema": MANIFEST_SCHEMA,
        "bundles": list(BUNDLE_NAMES),
        "files": dict(sorted(entries.items())),
    }


def default_destination() -> pathlib.Path:
    data_home = pathlib.Path(os.environ.get("XDG_DATA_HOME", "~/.local/share")).expanduser()
    if not data_home.is_absolute():
        raise InstallError("XDG_DATA_HOME must be an absolute path")
    return data_home / "tabilet" / "skill-bundles"


def default_controller_destination() -> pathlib.Path:
    return pathlib.Path("~/.local/lib/tabilet/controller").expanduser()


def default_bin_directory() -> pathlib.Path:
    return pathlib.Path("~/.local/bin").expanduser()


def install_skill_bundles(source_root: pathlib.Path, destination: pathlib.Path) -> pathlib.Path:
    """Atomically replace an installed bundle snapshot with all seven skills."""

    source = pathlib.Path(source_root).expanduser().resolve(strict=True)
    if not source.is_dir():
        raise InstallError("skill source is not a directory")
    requested = pathlib.Path(destination).expanduser()
    if requested.is_symlink():
        raise InstallError("skill bundle destination must not be a symbolic link")
    target = requested.resolve(strict=False)
    if target == source or target in source.parents or source in target.parents:
        raise InstallError("skill bundle destination must be outside the source skills tree")
    if target.exists() and (target.is_symlink() or not target.is_dir()):
        raise InstallError("skill bundle destination must be a real directory")

    parent = target.parent
    parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    staging = pathlib.Path(tempfile.mkdtemp(prefix=".tabilet-skills-", dir=parent))
    backup = parent / f".tabilet-skills-backup-{uuid.uuid4().hex}"
    moved_old = False
    try:
        staging.chmod(0o700)
        for name in BUNDLE_NAMES:
            source_bundle = source / name
            if source_bundle.is_symlink() or not source_bundle.is_dir():
                raise InstallError(f"canonical bundle is missing: {name}")
            target_bundle = staging / name
            for path in regular_files(source_bundle):
                output = target_bundle / path.relative_to(source_bundle)
                output.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
                shutil.copyfile(path, output, follow_symlinks=False)
                shutil.copystat(path, output, follow_symlinks=False)

        manifest = build_manifest(staging)
        manifest_path = staging / MANIFEST_NAME
        with manifest_path.open("x", encoding="utf-8", newline="\n") as output:
            json.dump(manifest, output, sort_keys=True, separators=(",", ":"))
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        manifest_path.chmod(0o644)

        if target.exists():
            os.replace(target, backup)
            moved_old = True
        os.replace(staging, target)
        if moved_old:
            shutil.rmtree(backup)
        return target
    except Exception:
        if moved_old and backup.exists() and not target.exists():
            os.replace(backup, target)
        raise
    finally:
        if staging.exists():
            shutil.rmtree(staging)
        if backup.exists() and target.exists():
            shutil.rmtree(backup)


def install_controller(source_root: pathlib.Path, destination: pathlib.Path) -> pathlib.Path:
    """Atomically install the controller and every adjacent runtime module."""

    source = pathlib.Path(source_root).expanduser().resolve(strict=True)
    if not source.is_dir():
        raise InstallError("controller source is not a directory")
    requested = pathlib.Path(destination).expanduser()
    if requested.is_symlink():
        raise InstallError("controller destination must not be a symbolic link")
    target = requested.resolve(strict=False)
    if target == source or target in source.parents or source in target.parents:
        raise InstallError("controller destination must be outside the source harness tree")
    if target.exists() and (target.is_symlink() or not target.is_dir()):
        raise InstallError("controller destination must be a real directory")
    for name in CONTROLLER_FILES:
        path = source / name
        if path.is_symlink() or not path.is_file():
            raise InstallError(f"controller runtime file is missing or linked: {name}")

    parent = target.parent
    parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    staging = pathlib.Path(tempfile.mkdtemp(prefix=".tabilet-controller-", dir=parent))
    backup = parent / f".tabilet-controller-backup-{uuid.uuid4().hex}"
    moved_old = False
    try:
        staging.chmod(0o755)
        for name in CONTROLLER_FILES:
            shutil.copyfile(source / name, staging / name, follow_symlinks=False)
            shutil.copystat(source / name, staging / name, follow_symlinks=False)
        if target.exists():
            os.replace(target, backup)
            moved_old = True
        os.replace(staging, target)
        if moved_old:
            shutil.rmtree(backup)
        return target
    except Exception:
        if moved_old and backup.exists() and not target.exists():
            os.replace(backup, target)
        raise
    finally:
        if staging.exists():
            shutil.rmtree(staging)
        if backup.exists() and target.exists():
            shutil.rmtree(backup)


def install_launcher(controller_dir: pathlib.Path, bin_dir: pathlib.Path) -> pathlib.Path:
    """Install a shim which locates its adjacent private controller tree."""

    library = pathlib.Path(controller_dir).expanduser().resolve(strict=True)
    if not library.is_dir():
        raise InstallError("installed controller directory is not a directory")
    requested = pathlib.Path(bin_dir).expanduser()
    if requested.is_symlink():
        raise InstallError("launcher directory must not be a symbolic link")
    directory = requested.resolve(strict=False)
    directory.mkdir(mode=0o755, parents=True, exist_ok=True)
    if directory.is_symlink() or not directory.is_dir():
        raise InstallError("launcher directory must be a real directory")
    target = directory / "tabilet"
    if target.is_symlink():
        raise InstallError("refusing to replace a symbolic-link tabilet launcher")
    script = (
        "#!/usr/bin/env python3\n"
        "import sys\n"
        f"sys.path.insert(0, {str(library)!r})\n"
        "from tabilet_cli import main\n"
        "raise SystemExit(main())\n"
    )
    descriptor, temporary = tempfile.mkstemp(prefix=".tabilet-launcher-", dir=directory, text=True)
    temp_path = pathlib.Path(temporary)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as output:
            output.write(script)
            output.flush()
            os.fsync(output.fileno())
        temp_path.chmod(0o755)
        os.replace(temp_path, target)
        return target
    finally:
        if temp_path.exists():
            temp_path.unlink()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=pathlib.Path,
        default=pathlib.Path(__file__).resolve().parents[1] / "skills",
        help="canonical skills/ directory in a repository checkout",
    )
    parser.add_argument("--destination", type=pathlib.Path)
    parser.add_argument(
        "--controller-source", type=pathlib.Path,
        default=pathlib.Path(__file__).resolve().parent,
        help="harness/ directory containing the optional API controller payload",
    )
    parser.add_argument("--controller-destination", type=pathlib.Path)
    parser.add_argument("--bin-dir", type=pathlib.Path)
    args = parser.parse_args(argv)
    try:
        destination = args.destination or default_destination()
        print(install_skill_bundles(args.source, destination))
        controller_destination = args.controller_destination or default_controller_destination()
        installed_controller = install_controller(args.controller_source, controller_destination)
        print(installed_controller)
        print(install_launcher(installed_controller, args.bin_dir or default_bin_directory()))
    except (InstallError, OSError) as exc:
        print(f"tabilet-install: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
