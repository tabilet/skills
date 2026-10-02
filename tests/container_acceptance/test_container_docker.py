from __future__ import annotations

import importlib.machinery
import importlib.util
import os
import pathlib
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True


def load_module(name: str, path: pathlib.Path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


core = load_module("container_docker_test_runner", ROOT / "harness/tackle-memory-bank-api-loop")
container = load_module("container_docker_test_executor", ROOT / "harness/tabilet_container.py")
DOCKER_IMAGE = os.environ.get("TABILET_TEST_DOCKER_IMAGE", "python:3.9-bookworm")


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


def docker_available() -> bool:
    if not shutil.which("docker") or not sys.platform.startswith("linux"):
        return False
    if any(os.environ.get(name) for name in (
        "DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH", "DOCKER_CONFIG"
    )):
        return False
    try:
        docker, endpoint = container.local_docker_endpoint()
        proc = container._run_docker(
            [docker, "--host", endpoint, "image", "inspect", "--format={{.Id}}", DOCKER_IMAGE],
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired, container.SandboxUnavailable):
        return False
    return proc.returncode == 0


if os.environ.get("TABILET_REQUIRE_DOCKER") == "1" and not docker_available():
    raise RuntimeError("TABILET_REQUIRE_DOCKER=1 but local Docker or TABILET_TEST_DOCKER_IMAGE is unavailable")


@unittest.skipUnless(docker_available(), "local Docker daemon or test image is unavailable")
class LocalDockerAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = make_git_repo(pathlib.Path(self.temp.name) / "repo")
        self.mountinfo = pathlib.Path(self.temp.name) / "mountinfo"
        self.mountinfo.write_text("", encoding="utf-8")
        self.executor = container.prepare_executor(core, self.root, DOCKER_IMAGE, self.mountinfo)

    def run_command(self, command: str, timeout: int = 10):
        return self.executor(self.root, command, timeout, 4096, False, {"OPENAI_API_KEY": "must-not-enter"})

    def test_isolation_writable_project_and_readonly_git(self):
        command = (
            "printf 'written' > controller-output; "
            "if (printf bad >> .git/config) 2>/dev/null; then exit 91; fi; "
            "if (printf hook > .git/hooks/pre-commit) 2>/dev/null; then exit 93; fi; "
            "test ! -e /var/run/docker.sock && "
            "test \"$HOME\" = /tmp && "
            "test -z \"${OPENAI_API_KEY+x}\" && "
            "test \"$(python -c 'import socket; s=socket.socket(); s.settimeout(1); "
            "print(s.connect_ex((\"1.1.1.1\",53)))')\" != 0"
        )
        result = self.run_command(command)
        self.assertEqual(0, result["exit_code"], result["stderr"])
        self.assertEqual("written", (self.root / "controller-output").read_text(encoding="utf-8"))
        self.assertNotIn("bad", (self.root / ".git/config").read_text(encoding="utf-8"))

    def test_run_pins_the_local_image_and_mounts_only_project_and_readonly_git(self):
        process = mock.Mock()
        process.communicate.return_value = ("", "")
        process.returncode = 0
        with mock.patch.object(self.executor, "_spawn_cleanup_watchdog", return_value=None), \
                mock.patch.object(container.subprocess, "Popen", return_value=process) as launch, \
                mock.patch.object(self.executor, "_cleanup"):
            result = self.executor(self.root, "true", 1000, 4096, False, {})
        self.assertEqual(0, result["exit_code"])
        process.communicate.assert_called_once_with(timeout=300)
        command = launch.call_args.args[0]
        self.assertIn("--pull=never", command)
        self.assertIn("--network", command)
        self.assertEqual("none", command[command.index("--network") + 1])
        self.assertEqual(self.executor.image, command[command.index("--entrypoint") + 2])
        mount_values = [command[index + 1] for index, value in enumerate(command[:-1]) if value == "--mount"]
        self.assertEqual(2, len(mount_values))
        self.assertIn(f"source={self.root},target=/workspace", mount_values[0])
        self.assertIn(f"source={self.root / '.git'},target=/workspace/.git,readonly", mount_values[1])
        self.assertNotIn(str(pathlib.Path.home()), " ".join(mount_values))
        self.assertEqual("4", command[command.index("--cpus") + 1])
        self.assertEqual("8g", command[command.index("--memory") + 1])
        self.assertEqual("512", command[command.index("--pids-limit") + 1])

    def test_timeout_removes_container(self):
        known = "tabilet-timeoutacceptance"
        with mock.patch.object(container.uuid, "uuid4", return_value=type("UUID", (), {"hex": known.removeprefix("tabilet-")})()):
            result = self.run_command("sleep 20", timeout=1)
        self.assertEqual(124, result["exit_code"])
        listing = subprocess.run(
            ["docker", "--host", self.executor.endpoint, "ps", "-a", "--filter", f"name=^{known}$", "-q"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10,
        )
        self.assertEqual(0, listing.returncode, listing.stderr)
        self.assertEqual("", listing.stdout.strip())

    def test_keyboard_interrupt_stops_the_container(self):
        process = mock.Mock()
        process.pid = 987654321
        process.returncode = 0
        process.communicate.side_effect = [KeyboardInterrupt(), ("", "")]
        with mock.patch.object(self.executor, "_spawn_cleanup_watchdog", return_value=None), \
                mock.patch.object(container.subprocess, "Popen", return_value=process), \
                mock.patch.object(self.executor, "_cleanup") as cleanup:
            with self.assertRaises(KeyboardInterrupt):
                self.run_command("sleep 20")
        self.assertGreaterEqual(cleanup.call_count, 1)

    def test_parent_crash_removes_the_running_container(self):
        name = "tabilet-parent-crash-acceptance"
        script = r'''import importlib.machinery, importlib.util, pathlib, sys
root = pathlib.Path(sys.argv[1])
repo = pathlib.Path(sys.argv[2])
image = sys.argv[3]
name = sys.argv[4]
def load(label, path):
    loader = importlib.machinery.SourceFileLoader(label, str(path))
    spec = importlib.util.spec_from_loader(label, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module
core = load("container_crash_core", root / "harness/tackle-memory-bank-api-loop")
container = load("container_crash_executor", root / "harness/tabilet_container.py")
container.uuid.uuid4 = lambda: type("FixedUUID", (), {"hex": name.removeprefix("tabilet-")})()
executor = container.prepare_executor(core, repo, image)
executor(repo, "sleep 60", 300, 1024, False)
'''
        process = subprocess.Popen(
            [sys.executable, "-c", script, str(ROOT), str(self.root), DOCKER_IMAGE, name],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            deadline = time.monotonic() + 10
            present = False
            while time.monotonic() < deadline:
                listing = subprocess.run(
                    ["docker", "--host", self.executor.endpoint, "ps", "-a", "--filter", f"name=^{name}$", "-q"],
                    stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, timeout=5,
                )
                self.assertEqual(0, listing.returncode, listing.stderr)
                if listing.stdout.strip():
                    present = True
                    break
                if process.poll() is not None:
                    break
                time.sleep(0.1)
            self.assertTrue(present, "worker did not start the test container")
            process.send_signal(signal.SIGKILL)
            process.wait(timeout=5)

            deadline = time.monotonic() + 12
            while time.monotonic() < deadline:
                listing = subprocess.run(
                    ["docker", "--host", self.executor.endpoint, "ps", "-a", "--filter", f"name=^{name}$", "-q"],
                    stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, timeout=5,
                )
                self.assertEqual(0, listing.returncode, listing.stderr)
                if not listing.stdout.strip():
                    return
                time.sleep(0.1)
            self.fail("cleanup monitor left the interrupted command container running")
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
            subprocess.run(
                ["docker", "--host", self.executor.endpoint, "rm", "-f", name],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=10, check=False,
            )


if __name__ == "__main__":
    unittest.main()
