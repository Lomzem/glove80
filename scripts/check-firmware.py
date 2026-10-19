#!/usr/bin/env python3
"""Validate staged firmware inputs and publish the resulting local UF2."""

from pathlib import Path
import os
import re
import shutil
import subprocess
import sys
import tempfile


def git(*args):
    return subprocess.check_output(["git", *args])


def firmware_input(path):
    return path.startswith("config/") or path in {
        "layout/glove80.json", "scripts/build.sh", "scripts/flash-drive.py",
        "scripts/check-firmware.py", "lefthook/firmware.yml",
    }


def main():
    root = Path(os.fsdecode(git("rev-parse", "--show-toplevel")).strip())
    os.chdir(root)
    paths = [os.fsdecode(p) for p in git(
        "diff", "--cached", "--name-only", "--no-renames", "-z"
    ).split(b"\0") if p]
    changed = [p for p in paths if firmware_input(p)]
    if not changed:
        print("[firmware] SKIP: no staged firmware inputs changed.")
        return 0
    print("[firmware] Staged inputs: " + ", ".join(changed), flush=True)
    whitespace = subprocess.run(["git", "diff", "--cached", "--check", "--", *changed])
    if whitespace.returncode:
        print("[firmware] FAIL: fix the staged whitespace errors above and stage the corrections.")
        return 1
    if "layout/glove80.json" in changed and "config/glove80.keymap" not in changed:
        print("[firmware] NOTE: only the editor snapshot changed; firmware uses config/glove80.keymap.")

    log = root / "build/firmware-pre-commit.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    print(f"[firmware] Building the Git index with Nix. Full log: {log}", flush=True)
    try:
        with tempfile.TemporaryDirectory(prefix="glove80-staged-") as folder:
            snapshot = Path(folder)
            # checkout-index respects GIT_INDEX_FILE, including git commit -a
            # and --only. It leaves the working tree and index untouched.
            subprocess.run(["git", "checkout-index", "--all", f"--prefix={snapshot}/"], check=True)
            with log.open("w") as output:
                result = subprocess.run(["bash", "scripts/build.sh"], cwd=snapshot,
                                        stdout=output, stderr=subprocess.STDOUT)
                if result.returncode == 0:
                    result = subprocess.run(
                        [sys.executable, "scripts/flash-drive.py", "validate", "firmware/glove80.uf2"],
                        cwd=snapshot, stdout=output, stderr=subprocess.STDOUT,
                    )
            if result.returncode:
                print(f"[firmware] FAIL: staged build exited {result.returncode}. Commit blocked.")
                lines = log.read_text(errors="replace").splitlines()
                errors = [i for i, line in enumerate(lines) if re.search(
                    r"error:|fatal error|FAILED:|syntax error|aborting|is required|Traceback", line,
                    flags=re.IGNORECASE,
                )]
                excerpt = set(range(max(0, len(lines) - 20), len(lines)))
                for i in errors[-8:]:
                    excerpt.update(range(max(0, i - 1), min(len(lines), i + 3)))
                print("\n".join(lines[i] for i in sorted(excerpt)))
                print(f"[firmware] Full log: {log}")
                print("[firmware] Fix the reported inputs, git add the fixes, and retry git commit.")
                print("[firmware] For Nix setup, see README.md: Build locally. Existing firmware is preserved.")
                return 1
            destination = root / "firmware"
            destination.mkdir(exist_ok=True)
            built = snapshot / "firmware/glove80.uf2"
            current = destination / "glove80.uf2"
            if current.exists() and current.read_bytes() != built.read_bytes():
                shutil.copy2(current, destination / "glove80-previous.uf2")
            # Replace atomically on this filesystem, after the staged build
            # and UF2 validation have both passed.
            with tempfile.NamedTemporaryFile(dir=destination, prefix=".commit-", delete=False) as out:
                staged = Path(out.name)
            try:
                shutil.copyfile(built, staged)
                staged.replace(current)
            finally:
                staged.unlink(missing_ok=True)
            (destination / "glove80.build.txt").unlink(missing_ok=True)
    except (OSError, subprocess.SubprocessError) as error:
        print(f"[firmware] FAIL: {error}", file=sys.stderr)
        print(f"[firmware] Commit blocked. Check {log} and retry after fixing the inputs.", file=sys.stderr)
        return 1
    print(f"[firmware] PASS: staged firmware built and validated. UF2: {current}")
    if any(p.startswith("config/") and p != "config/glove80.keymap" for p in changed):
        print("[firmware] Firmware/configuration inputs changed: flash both halves; see README reset guidance.")
    else:
        print("[firmware] Keymap-only update: run ./scripts/flash-wizard.sh, choose left, skip reset.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
