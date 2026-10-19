#!/usr/bin/env python3
"""Linux bootloader discovery and guarded UF2 copy for flash-wizard.sh."""

import argparse
import collections
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import time

LABELS = {"right": "GLV80RHBOOT", "left": "GLV80LHBOOT"}
FAMILIES = {0x9807B007, 0x9808B007}


def validate(path):
    data = Path(path).read_bytes()
    if not data or len(data) % 512:
        raise ValueError("Firmware must be a nonempty UF2 with 512-byte blocks.")
    groups = collections.defaultdict(list)
    for offset in range(0, len(data), 512):
        block = data[offset : offset + 512]
        m0, m1, flags, address, size, index, total, family = struct.unpack_from("<8I", block)
        end = struct.unpack_from("<I", block, 508)[0]
        if (m0, m1, end) != (0x0A324655, 0x9E5D5157, 0x0AB16F30):
            raise ValueError("Invalid UF2 block magic.")
        if not flags & 0x2000 or not 0 < size <= 476:
            raise ValueError("Invalid UF2 payload or missing family ID.")
        groups[family].append((index, total))
    if set(groups) != FAMILIES:
        raise ValueError("Expected a combined Glove80 UF2 containing BOTH half family IDs.")
    for blocks in groups.values():
        if {total for _, total in blocks} != {len(blocks)} or {
            index for index, _ in blocks
        } != set(range(len(blocks))):
            raise ValueError("Incomplete or duplicate UF2 blocks.")
    return data


def boot_drive(half):
    result = subprocess.run(
        ["lsblk", "--json", "--paths", "--output", "NAME,LABEL,MOUNTPOINTS"],
        check=True, capture_output=True, text=True,
    )

    def walk(devices):
        for device in devices:
            yield device
            yield from walk(device.get("children", []))

    matches = [d for d in walk(json.loads(result.stdout)["blockdevices"])
               if d.get("label") == LABELS[half]]
    if len(matches) > 1:
        raise ValueError(f"Multiple {LABELS[half]} drives found; disconnect the extra keyboard.")
    return matches[0] if matches else None


def mounted_path(device):
    paths = [p for p in device.get("mountpoints", []) if p and os.path.ismount(p)]
    if len(paths) > 1:
        raise ValueError("Bootloader has multiple mountpoints; leave only one mounted.")
    return paths[0] if paths else None


def prepare(half):
    print(f"Waiting up to 120 seconds for {LABELS[half]}…", file=sys.stderr)
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        device = boot_drive(half)
        if device:
            mount = mounted_path(device)
            if not mount:
                if not shutil.which("udisksctl"):
                    raise ValueError("Drive detected but unmounted. Mount it in your file manager, then rerun.")
                try:
                    subprocess.run(["udisksctl", "mount", "--block-device", device["name"]],
                                   check=True, stdout=sys.stderr)
                except subprocess.CalledProcessError:
                    # A desktop automounter may have won the race. Re-read the
                    # actual device state before treating the mount as failed.
                    current = boot_drive(half)
                    if not current or not mounted_path(current):
                        raise
                device = boot_drive(half)
                mount = mounted_path(device) if device else None
            if not mount:
                raise ValueError("Bootloader was detected but no mounted filesystem is available.")
            print(mount)
            return
        time.sleep(1)
    raise ValueError(
        f"{LABELS[half]} did not appear. Check the power-up chord and USB data cable. "
        "Run lsblk -o NAME,LABEL,MOUNTPOINTS to inspect drives. "
        "Do not create the missing /run/media directory yourself."
    )


def flash(half, firmware, expected_mount):
    data = validate(firmware)
    device = boot_drive(half)
    mount = mounted_path(device) if device else None
    if not mount or mount != expected_mount:
        raise ValueError("Bootloader mount changed or disappeared; refusing to copy. Rerun the wizard.")
    # Resolve the directory before opening the file. Never create a mountpoint:
    # an ordinary directory must not be mistaken for the keyboard.
    directory = os.open(mount, os.O_RDONLY | os.O_DIRECTORY)
    try:
        with open(os.open("glove80.uf2", os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
                          0o644, dir_fd=directory), "wb") as target:
            target.write(data)
            target.flush()
            os.fsync(target.fileno())
    finally:
        os.close(directory)
    print(f"Copied firmware to {LABELS[half]}. Waiting for the bootloader to disappear…")
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if not boot_drive(half):
            print("Bootloader disconnected. Check that the half restarts.")
            return
        time.sleep(1)
    raise ValueError("Copy completed, but bootloader is still present. Check the keyboard before continuing.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate").add_argument("firmware")
    commands.add_parser("prepare").add_argument("half", choices=LABELS)
    copy = commands.add_parser("flash")
    copy.add_argument("half", choices=LABELS)
    copy.add_argument("firmware")
    copy.add_argument("mountpoint")
    args = parser.parse_args()
    try:
        if args.command == "validate":
            data = validate(args.firmware)
            print(f"Validated combined left + right UF2 ({len(data):,} bytes).")
        elif args.command == "prepare":
            prepare(args.half)
        else:
            flash(args.half, args.firmware, args.mountpoint)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
