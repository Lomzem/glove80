"""Firmware selection must not silently flash an older configuration."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from test_flash_drive import uf2

REPO = Path(__file__).resolve().parents[1]


class DownloadFirmware(unittest.TestCase):
    def test_matching_build_required_before_replacing_local_firmware(self):
        for scenario in ("stale-build", "docs-only-change", "invalid-artifact"):
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                (root / "scripts").mkdir()
                (root / "config").mkdir()
                (root / "firmware").mkdir()
                for name in ("download-firmware.sh", "flash-drive.py"):
                    shutil.copy2(REPO / "scripts" / name, root / "scripts" / name)
                (root / "config/keymap").write_text("initial config")
                original = b"previously downloaded firmware"
                target = root / "firmware/glove80.uf2"
                target.write_bytes(original)
                artifact = root / "artifact.uf2"
                artifact.write_bytes(b"bad artifact" if scenario == "invalid-artifact" else uf2())

                def git(*args):
                    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()

                def commit():
                    git("add", "config", "README.md")
                    git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                        "commit", "-qm", "fixture")

                git("init", "-qb", "main")
                (root / "README.md").write_text("docs")
                commit()
                built_sha = git("rev-parse", "HEAD")
                if scenario == "stale-build":
                    (root / "config/keymap").write_text("new config not built yet")
                else:
                    (root / "README.md").write_text("updated docs")
                commit()

                fake_bin = root / "bin"
                fake_bin.mkdir()
                gh = fake_bin / "gh"
                gh.write_text(
                    f"#!{sys.executable}\n"
                    "import json,os,pathlib,shutil,sys\n"
                    "if sys.argv[1:3] == ['run','list']:\n"
                    " print(os.environ['BUILD_RUN'])\n"
                    "elif sys.argv[1:3] == ['run','download']:\n"
                    " dest=pathlib.Path(sys.argv[sys.argv.index('--dir')+1])/'glove80.uf2'\n"
                    " shutil.copyfile(os.environ['ARTIFACT'],dest)\n"
                    "else: sys.exit(2)\n"
                )
                gh.chmod(0o755)
                env = {**os.environ, "PATH": str(fake_bin) + os.pathsep + os.environ["PATH"],
                       "ARTIFACT": str(artifact), "BUILD_RUN": json.dumps([
                           {"databaseId": 123, "headSha": built_sha,
                            "url": "https://github.com/example/keyboard/actions/runs/123"}
                       ])}
                result = subprocess.run(["bash", "scripts/download-firmware.sh"],
                                        cwd=root, env=env, capture_output=True, text=True)
                if scenario == "docs-only-change":
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(target.read_bytes(), artifact.read_bytes())
                    self.assertEqual((root / "firmware/glove80-previous.uf2").read_bytes(), original)
                    self.assertIn(built_sha, (root / "firmware/glove80.build.txt").read_text())
                else:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(target.read_bytes(), original)
                    if scenario == "stale-build":
                        self.assertIn("Refusing to flash stale firmware", result.stderr)


if __name__ == "__main__":
    unittest.main()
