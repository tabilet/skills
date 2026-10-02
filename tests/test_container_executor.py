from __future__ import annotations

import importlib.machinery
import importlib.util
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True


def load_module(name: str, path: pathlib.Path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


core = load_module("container_test_runner", ROOT / "harness/tackle-memory-bank-api-loop")
container = load_module("container_test_executor", ROOT / "harness/tabilet_container.py")


def git(*args: str, cwd: pathlib.Path):
    return subprocess.run(
        ["git", *args], cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, check=False,
    )


def make_git_repo(root: pathlib.Path) -> pathlib.Path:
    root.mkdir(parents=True)
    (root / "file.txt").write_text("initial\n", encoding="utf-8")
    git("init", "-q", cwd=root)
    git("-c", "user.name=Container test", "-c", "user.email=container@example.test",
        "add", "-A", cwd=root)
    committed = git("-c", "user.name=Container test", "-c", "user.email=container@example.test",
                    "commit", "-qm", "initial", cwd=root)
    if committed.returncode:
        raise AssertionError(committed.stderr)
    return root


def executable(path: pathlib.Path, content: str) -> pathlib.Path:
    path.write_text("#!/bin/sh\n" + content + "\n", encoding="utf-8")
    path.chmod(0o755)
    return path


class HostGitSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = make_git_repo(pathlib.Path(self.temp.name) / "repo")
        self.marker = pathlib.Path(self.temp.name) / "ran-command"

    def test_hooks_fsmonitor_external_diff_and_signing_config_cannot_launch(self):
        hooks = self.root / ".git/hooks"
        executable(hooks / "pre-commit", f"touch {self.marker}")
        executable(hooks / "post-commit", f"touch {self.marker}")
        evil = executable(pathlib.Path(self.temp.name) / "evil", f"touch {self.marker}; exit 0")
        for key, value in (
            ("core.hooksPath", str(hooks)),
            ("core.fsmonitor", str(evil)),
            ("diff.external", str(evil)),
            ("commit.gpgsign", "true"),
            ("gpg.program", str(evil)),
        ):
            self.assertEqual(0, git("config", "--local", key, value, cwd=self.root).returncode)
        (self.root / "file.txt").write_text("changed\n", encoding="utf-8")

        self.assertEqual(0, core.git_local(["status", "--short"], self.root).returncode)
        self.assertEqual(0, core.git_local(["diff"], self.root).returncode)
        self.assertEqual(0, core.git_local(["add", "--", "file.txt"], self.root).returncode)
        committed = core.git_local(["commit", "-m", "safe"], self.root)
        self.assertEqual(0, committed.returncode, committed.stderr)
        self.assertFalse(self.marker.exists())

    def test_explicit_host_signing_and_global_config_injection_are_rejected(self):
        with self.assertRaises(core.UnsafeGitConfiguration):
            core.git_local(["commit", "-S", "-m", "unsafe"], self.root)
        with self.assertRaises(core.UnsafeGitConfiguration):
            core.git_local(["-c", "core.hooksPath=/tmp", "status"], self.root)

    def test_clean_filter_in_repository_config_is_rejected_before_staging(self):
        evil = executable(pathlib.Path(self.temp.name) / "clean", f"touch {self.marker}; cat")
        git("config", "--local", "filter.evil.clean", str(evil), cwd=self.root)
        (self.root / ".gitattributes").write_text("*.txt filter=evil\n", encoding="utf-8")
        (self.root / "file.txt").write_text("changed\n", encoding="utf-8")

        with self.assertRaises(core.UnsafeGitConfiguration):
            core.git_local(["add", "--", "."], self.root)
        self.assertFalse(self.marker.exists())

    def test_process_filter_from_info_attributes_is_rejected_before_staging(self):
        evil = executable(pathlib.Path(self.temp.name) / "process", f"touch {self.marker}; cat")
        git("config", "--local", "filter.evil.process", str(evil), cwd=self.root)
        info_attributes = self.root / ".git/info/attributes"
        info_attributes.write_text("file.txt filter=evil\n", encoding="utf-8")
        (self.root / "file.txt").write_text("changed\n", encoding="utf-8")

        with self.assertRaises(core.UnsafeGitConfiguration):
            core.git_local(["add", "--", "file.txt"], self.root)
        self.assertFalse(self.marker.exists())

    def test_active_filter_in_worktree_config_is_rejected(self):
        evil = executable(pathlib.Path(self.temp.name) / "worktree-clean", f"touch {self.marker}; cat")
        git("config", "--local", "extensions.worktreeConfig", "true", cwd=self.root)
        git("config", "--worktree", "filter.evil.clean", str(evil), cwd=self.root)
        (self.root / ".gitattributes").write_text("*.txt filter=evil\n", encoding="utf-8")
        (self.root / "file.txt").write_text("changed\n", encoding="utf-8")

        with self.assertRaises(core.UnsafeGitConfiguration):
            core.git_local(["add", "--", "file.txt"], self.root)
        self.assertFalse(self.marker.exists())

    def test_status_preflights_clean_filter_before_git_can_run_it(self):
        evil = executable(pathlib.Path(self.temp.name) / "status-clean", f"touch {self.marker}; cat")
        git("config", "--local", "filter.evil.clean", str(evil), cwd=self.root)
        (self.root / ".gitattributes").write_text("*.txt filter=evil\n", encoding="utf-8")
        (self.root / "file.txt").write_text("changed\n", encoding="utf-8")

        with self.assertRaises(core.UnsafeGitConfiguration):
            core.git_local(["status", "--short"], self.root)
        self.assertFalse(self.marker.exists())

    def test_builtin_text_normalization_remains_enabled(self):
        (self.root / ".gitattributes").write_text("*.txt text eol=lf\n", encoding="utf-8")
        (self.root / "file.txt").write_bytes(b"first\r\nsecond\r\n")
        staged = core.git_local(["add", "--", "file.txt"], self.root)
        self.assertEqual(0, staged.returncode, staged.stderr)
        blob = core.git_local(["show", ":file.txt"], self.root)
        self.assertEqual(b"first\nsecond\n", blob.stdout.encode("utf-8"))


class RepositoryTopologyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = pathlib.Path(self.temp.name)
        self.mountinfo = self.base / "mountinfo"
        self.mountinfo.write_text("", encoding="utf-8")

    def test_standard_in_tree_repository_is_accepted(self):
        repo = make_git_repo(self.base / "repo")
        self.assertEqual(repo.resolve(), container.validate_repository(core, repo, self.mountinfo))

    def test_linked_worktree_and_external_gitdir_are_rejected(self):
        source = make_git_repo(self.base / "source")
        worktree = self.base / "linked"
        added = git("worktree", "add", "-q", "-b", "linked-branch", str(worktree), cwd=source)
        self.assertEqual(0, added.returncode, added.stderr)
        with self.assertRaisesRegex(container.SandboxUnavailable, "linked worktrees"):
            container.validate_repository(core, worktree, self.mountinfo)

        external = self.base / "external-git-dir"
        external_repo = self.base / "external-repo"
        external_repo.mkdir()
        initialized = git("init", "-q", f"--separate-git-dir={external}", cwd=external_repo)
        self.assertEqual(0, initialized.returncode, initialized.stderr)
        with self.assertRaisesRegex(container.SandboxUnavailable, "linked worktrees"):
            container.validate_repository(core, external_repo, self.mountinfo)

        symlink_target = self.base / "symlink-target"
        symlink_target.mkdir()
        symlink_repo = self.base / "symlink-repo"
        symlink_repo.mkdir()
        (symlink_repo / ".git").symlink_to(symlink_target, target_is_directory=True)
        with self.assertRaisesRegex(container.SandboxUnavailable, "symlinked .git"):
            container.validate_repository(core, symlink_repo, self.mountinfo)

    def test_nested_git_repository_and_nested_mount_are_rejected(self):
        repo = make_git_repo(self.base / "nested")
        nested = repo / "vendor/project"
        nested.mkdir(parents=True)
        (nested / ".git").mkdir()
        with self.assertRaisesRegex(container.SandboxUnavailable, "nested Git"):
            container.validate_repository(core, repo, self.mountinfo)

        (nested / ".git").rmdir()
        mount_dir = repo / "vendor"
        mount_dir.mkdir(exist_ok=True)
        escaped = str(mount_dir).replace(" ", r"\040")
        self.mountinfo.write_text(f"36 25 0:32 / {escaped} rw - tmpfs tmpfs rw\n", encoding="utf-8")
        with self.assertRaisesRegex(container.SandboxUnavailable, "nested host mounts"):
            container.validate_repository(core, repo, self.mountinfo)

    def test_submodule_gitlink_is_rejected(self):
        repo = make_git_repo(self.base / "submodule-parent")
        child = make_git_repo(self.base / "child")
        (repo / "submodule").mkdir()
        git("-c", "protocol.file.allow=always", "submodule", "add", "-q", str(child), "submodule/child", cwd=repo)
        with self.assertRaisesRegex(container.SandboxUnavailable, "submodule"):
            container.validate_repository(core, repo, self.mountinfo)


class DockerPreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = make_git_repo(pathlib.Path(self.temp.name) / "repo")
        self.mountinfo = pathlib.Path(self.temp.name) / "mountinfo"
        self.mountinfo.write_text("", encoding="utf-8")

    def test_remote_context_is_rejected(self):
        completed = subprocess.CompletedProcess([], 0, "tcp://remote.example:2376\n", "")
        with mock.patch.object(container, "_run_docker", return_value=completed):
            with self.assertRaisesRegex(container.SandboxUnavailable, "not a local Unix-socket"):
                container.local_docker_endpoint()

    def test_daemon_override_is_rejected_before_context_inspection(self):
        with mock.patch.dict(os.environ, {"DOCKER_HOST": "tcp://remote.example:2376"}):
            with mock.patch.object(container, "_run_docker") as run_docker:
                with self.assertRaisesRegex(container.SandboxUnavailable, "daemon overrides"):
                    container.local_docker_endpoint()
        run_docker.assert_not_called()

    def test_missing_local_image_does_not_pull_or_build(self):
        with mock.patch.dict(os.environ, {name: "" for name in (
            "DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH"
        )}):
            with mock.patch.object(container, "local_docker_endpoint", return_value=("docker", "unix:///tmp/docker.sock")):
                with mock.patch.object(container, "_run_docker", return_value=subprocess.CompletedProcess([], 1, "", "not found")) as run_docker:
                    with self.assertRaisesRegex(container.SandboxUnavailable, "docker --host.*pull missing:tag.*will not pull or build"):
                        container.DockerExecutor(core, self.root, "missing:tag", self.mountinfo)
        commands = [call.args[0] for call in run_docker.call_args_list]
        self.assertEqual(1, len(commands))
        self.assertIn("image", commands[0])
        self.assertNotIn("pull", commands[0])
        self.assertNotIn("build", commands[0])


class ControllerFailureMappingTests(unittest.TestCase):
    def test_setup_failure_is_exit_17_before_provider_dispatch(self):
        controller_module = load_module("container_test_controller", ROOT / "harness/tabilet_controller.py")
        with mock.patch.dict(sys.modules, {"tabilet_container": container}):
            with mock.patch.object(container, "prepare_executor", side_effect=container.SandboxUnavailable("no image")):
                with self.assertRaises(SystemExit) as stopped:
                    controller_module.prepare_docker_executor(core, pathlib.Path("/project"), "missing")
        self.assertEqual(17, stopped.exception.code)

    def test_missing_command_is_exit_17_and_pauses(self):
        controller_module = load_module("container_test_controller_missing", ROOT / "harness/tabilet_controller.py")
        args = object()

        def dispatch(_args, repo, _run, _summary, _row, executor, **_kwargs):
            return executor(repo, "missing-tool", 1, 100, False, {})

        def missing(*_args, **_kwargs):
            return {"exit_code": 127, "stdout": "", "stderr": "missing-tool: not found", "truncated": False}

        with mock.patch.object(core, "one_agent_run", side_effect=dispatch):
            with self.assertRaises(SystemExit) as stopped:
                controller_module.run_controller_agent(core, args, pathlib.Path("/project"), 1, [], None,
                                                       missing, "run the selected task")
        self.assertEqual(17, stopped.exception.code)


if __name__ == "__main__":
    unittest.main()
