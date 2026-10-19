"""Safety contracts at the flashing helper's command-line boundary."""

import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

HELPER = Path(__file__).resolve().parents[1] / "scripts/flash-drive.py"


def uf2(families=(0x9807B007, 0x9808B007)):
    blocks = []
    for family in families:
        block = bytearray(512)
        struct.pack_into("<8I", block, 0, 0x0A324655, 0x9E5D5157,
                         0x2000, 0x26000, 256, 0, 1, family)
        struct.pack_into("<I", block, 508, 0x0AB16F30)
        blocks.append(block)
    return b"".join(blocks)


class FlashSafety(unittest.TestCase):
    def test_invalid_or_incomplete_firmware_is_rejected(self):
        cases = [(uf2(), True), (b"not firmware", False),
                 (uf2((0x9807B007,)), False),
                 (uf2((0xADA52840, 0x9808B007)), False),
                 (uf2()[:-1], False), (uf2() + uf2(), False)]
        with tempfile.TemporaryDirectory() as folder:
            firmware = Path(folder) / "firmware.uf2"
            for data, valid in cases:
                with self.subTest(size=len(data), valid=valid):
                    firmware.write_bytes(data)
                    result = subprocess.run([sys.executable, str(HELPER), "validate", str(firmware)],
                                            capture_output=True, text=True)
                    self.assertEqual(result.returncode == 0, valid, result.stderr)

    def test_flash_never_writes_to_missing_or_ordinary_mount_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            firmware = root / "firmware.uf2"
            firmware.write_bytes(uf2())
            fake_lsblk = root / "lsblk"
            mount = root / "GLV80RHBOOT"
            # Supply OS device observations at the real subprocess boundary.
            # Even a matching label is insufficient without a real mounted FS.
            for label, exists in [(None, False), ("OTHER", True), ("GLV80RHBOOT", True)]:
                with self.subTest(label=label, exists=exists):
                    if exists:
                        mount.mkdir(exist_ok=True)
                    payload = json.dumps({"blockdevices": [
                        {"name": "/dev/fake", "label": label, "mountpoints": [str(mount)]}
                    ]})
                    fake_lsblk.write_text("#!/bin/sh\nprintf '%s\\n' '" + payload + "'\n")
                    fake_lsblk.chmod(0o755)
                    env = {**os.environ, "PATH": str(root) + os.pathsep + os.environ["PATH"]}
                    result = subprocess.run(
                        [sys.executable, str(HELPER), "flash", "right", str(firmware), str(mount)],
                        env=env, capture_output=True, text=True,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("refusing to copy", result.stderr)
                    self.assertFalse((mount / "glove80.uf2").exists())
                    self.assertEqual(mount.exists(), exists)


if __name__ == "__main__":
    unittest.main()
