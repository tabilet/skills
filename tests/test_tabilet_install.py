from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True


def load_module(name, path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


installer = load_module("tabilet_install_test", ROOT / "harness/tabilet_install.py")


class TabiletInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)

    def test_installs_verified_bundles_controller_and_executable_cli(self):
        bundles = installer.install_skill_bundles(ROOT / "skills", self.root / "share/tabilet/skill-bundles")
        controller = installer.install_controller(ROOT / "harness", self.root / "lib/tabilet/controller")
        launcher = installer.install_launcher(controller, self.root / "bin")
        manifest = json.loads((bundles / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(list(installer.BUNDLE_NAMES), manifest["bundles"])
        self.assertEqual(set(installer.CONTROLLER_FILES), {path.name for path in controller.iterdir()})
        self.assertTrue(os.access(launcher, os.X_OK))
        result = subprocess.run(
            [str(launcher), "--help"], text=True, capture_output=True, check=False,
            env={**os.environ, "XDG_DATA_HOME": str(self.root / "share")},
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("chat", result.stdout)
        self.assertIn("resume", result.stdout)

    def test_refuses_a_symlinked_controller_destination(self):
        real = self.root / "real"
        real.mkdir()
        linked = self.root / "linked"
        linked.symlink_to(real, target_is_directory=True)
        with self.assertRaisesRegex(installer.InstallError, "symbolic link"):
            installer.install_controller(ROOT / "harness", linked)


if __name__ == "__main__":
    unittest.main()
