"""The commit check builds the index and preserves working files on failure."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from test_flash_drive import uf2

REPO = Path(__file__).resolve().parents[1]


class FirmwareHook(unittest.TestCase):
    def test_docs_skip_partial_staging_and_build_failure(self):
        for scenario in ("docs", "partial", "failure", "invalid-artifact"):
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                (root / "scripts").mkdir()
                (root / "config").mkdir()
                (root / "firmware").mkdir()
                for name in ("check-firmware.py", "flash-drive.py"):
                    shutil.copy2(REPO / "scripts" / name, root / "scripts" / name)
                builder = root / "scripts/build.sh"
                builder.write_text("mkdir -p firmware\ncp config/input firmware/glove80.uf2\n")
                (root / "config/input").write_bytes(uf2())
                (root / "README.md").write_text("original docs\n")

                def git(*args):
                    return subprocess.check_output(["git", *args], cwd=root)

                git("init", "-q")
                git("add", "scripts", "config", "README.md")
                git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                    "-c", "core.hooksPath=/dev/null", "commit", "-qm", "fixture")
                previous = b"previous firmware"
                (root / "firmware/glove80.uf2").write_bytes(previous)
                staged = bytearray(uf2())
                staged[32] = 42  # Distinguish staged and unstaged compiler inputs.
                if scenario == "docs":
                    (root / "README.md").write_text("changed docs\n")
                    git("add", "README.md")
                    builder.write_text("echo 'build should not run' >&2\nexit 9\n")
                else:
                    (root / "config/input").write_bytes(staged)
                    if scenario == "failure":
                        builder.write_text("echo 'fixture compiler failure' >&2\nexit 7\n")
                        git("add", "scripts/build.sh")
                    if scenario == "invalid-artifact":
                        (root / "config/input").write_bytes(b"invalid artifact")
                    git("add", "config/input")
                    if scenario == "partial":
                        (root / "config/input").write_bytes(b"unstaged broken input")
                before_index = git("write-tree")
                before_working = (root / "config/input").read_bytes()
                result = subprocess.run([sys.executable, "scripts/check-firmware.py"],
                                        cwd=root, capture_output=True, text=True)
                self.assertEqual(git("write-tree"), before_index)
                self.assertEqual((root / "config/input").read_bytes(), before_working)
                artifact = (root / "firmware/glove80.uf2").read_bytes()
                if scenario == "partial":
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertEqual(artifact, bytes(staged))
                    self.assertIn("PASS", result.stdout)
                elif scenario == "docs":
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(artifact, previous)
                    self.assertIn("SKIP", result.stdout)
                else:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(artifact, previous)
                    self.assertIn("Commit blocked", result.stdout)
                    if scenario == "failure":
                        self.assertIn("fixture compiler failure", result.stdout)
                        self.assertIn("firmware-pre-commit.log", result.stdout)


if __name__ == "__main__":
    unittest.main()
