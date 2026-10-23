"""Patched ZMK firmware moves the pointer at constant speed, diagonals included.

Builds tests/pointer-motion in the native_posix_64 simulator with Nix and
checks the HID reports for each phase of its scripted key presses.
"""

import math
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]

# Positions in tests/pointer-motion/native_posix_64.keymap.
MOVE = {0: (0, -1), 1: (-1, 0), 2: (0, 1), 3: (1, 0)}
MODE = {4: "slow", 5: "warp"}
SCROLL = {6: (0, 1), 7: (1, 0)}
# Shorter transition phases contain too few ticks to measure a rate.
SUSTAINED_MS = 500
# Reports in the startup window after a press from rest.
STARTUP_REPORTS = 8

LINE = re.compile(r"^\[(\d+):(\d+):(\d+)\.(\d+),(\d+)\] .*?: (.*)$")
KEY = re.compile(r"position: (\d+), pressed: (true|false)")
REPORT = re.compile(r"Mouse (movement|scroll) set to (-?\d+)/(-?\d+)")


def parse(log):
    """Return key events and nonzero HID reports as (milliseconds, ...) tuples."""
    keys, reports = [], []
    for line in log.splitlines():
        match = LINE.match(line)
        if not match:
            continue
        h, m, s, ms, _ = map(int, match.groups()[:5])
        time = ((h * 60 + m) * 60 + s) * 1000 + ms
        if "kscan_process_msgq" in line and (key := KEY.search(line)):
            keys.append((time, int(key[1]), key[2] == "true"))
        elif report := REPORT.search(match[6]):
            x, y = int(report[2]), int(report[3])
            if x or y:
                reports.append((time, report[1], x, y))
    return keys, reports


def phases(keys, reports):
    """Split the run at key events, summing reports while each key set was held."""
    result = []
    held = set()
    for (start, position, pressed), end in zip(keys, [t for t, *_ in keys[1:]] + [math.inf]):
        (held.add if pressed else held.discard)(position)
        totals = {"movement": [0, 0], "scroll": [0, 0]}
        for time, kind, x, y in reports:
            if start < time <= end:
                totals[kind][0] += x
                totals[kind][1] += y
        duration = None if end == math.inf else end - start
        result.append((frozenset(held), duration, totals))
    return result


def net(held, vectors):
    return tuple(sum(vectors[p][i] for p in held if p in vectors) for i in (0, 1))


def mode(held):
    return next((MODE[p] for p in held if p in MODE), "fast")


class PointerMotion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which("nix-build"):
            raise unittest.SkipTest("nix-build is required; see README.md: Build locally.")
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / "result"
            subprocess.run(["nix-build", str(REPO / "tests/pointer-motion"), "--out-link", str(out)],
                           check=True, stdout=subprocess.DEVNULL)
            log = (out / "zmk.log").read_text()
        cls.keys, cls.reports = parse(log)
        cls.phases = phases(cls.keys, cls.reports)

    def rate(self, totals, duration):
        return [value / duration for value in totals]

    def speed(self, reports):
        return math.hypot(sum(r[2] for r in reports), sum(r[3] for r in reports))

    def straight_rate(self, speed_mode):
        rates = [math.hypot(*self.rate(t["movement"], d)) for held, d, t in self.phases
                 if d and d >= SUSTAINED_MS and mode(held) == speed_mode and 0 in net(held, MOVE)
                 and net(held, MOVE) != (0, 0)]
        self.assertTrue(rates, speed_mode)
        return sum(rates) / len(rates)

    def test_moves_at_straight_speed_in_every_direction_and_mode(self):
        checked = set()
        for held, duration, totals in self.phases:
            direction = net(held, MOVE)
            if not duration or duration < SUSTAINED_MS or direction == (0, 0):
                continue
            speed_mode = mode(held)
            label = f"{speed_mode} keys {sorted(held)}"
            with self.subTest(label):
                x, y = self.rate(totals["movement"], duration)
                straight = self.straight_rate(speed_mode)
                self.assertAlmostEqual(math.hypot(x, y) / straight, 1, delta=0.05)
                unit = math.hypot(*direction)
                self.assertAlmostEqual(x / straight, direction[0] / unit, delta=0.05)
                self.assertAlmostEqual(y / straight, direction[1] / unit, delta=0.05)
            checked.add((speed_mode, direction))
        # Fixture coverage: diagonals in each mode, opposed keys, and releases.
        self.assertTrue({("fast", (1, -1)), ("fast", (-1, -1)), ("fast", (0, -1)),
                         ("slow", (1, 1)), ("warp", (1, 1))} <= checked, checked)
        self.assertTrue(any({1, 3} <= held for held, *_ in self.phases))

    def test_moves_at_steady_speed_from_first_tick(self):
        checked = set()
        for (start, *_), before, (held, duration, _) in zip(
                self.keys, [frozenset()] + [p[0] for p in self.phases], self.phases):
            if net(before, MOVE) != (0, 0) or net(held, MOVE) == (0, 0) or not duration \
                    or duration < SUSTAINED_MS or mode(held) == "slow":
                # Slow mode moves too few whole units per report to measure.
                continue
            moves = [r for r in self.reports
                     if r[1] == "movement" and start < r[0] <= start + duration]
            with self.subTest(f"{mode(held)} keys {sorted(held)}"):
                # Time from the press to the window's last report includes any start delay.
                split = moves[STARTUP_REPORTS - 1][0]
                startup = self.speed(moves[:STARTUP_REPORTS]) / (split - start)
                steady = self.speed(moves[STARTUP_REPORTS:]) / (start + duration - split)
                self.assertAlmostEqual(startup / steady, 1, delta=0.1)
            checked.add(mode(held))
        self.assertEqual(checked, {"fast", "warp"})

    def test_stops_when_net_movement_is_zero(self):
        idle = [(held, t["movement"]) for held, _, t in self.phases if net(held, MOVE) == (0, 0)]
        self.assertTrue(idle)
        for held, movement in idle:
            self.assertEqual(movement, [0, 0], sorted(held))

    def test_scroll_diagonals_are_not_normalized(self):
        rates = {net(held, SCROLL): self.rate(t["scroll"], d)
                 for held, d, t in self.phases
                 if d and d >= SUSTAINED_MS and net(held, SCROLL) != (0, 0)}
        straight = rates[(0, 1)][1]
        self.assertGreater(straight, 0)
        x, y = rates[(1, 1)]
        self.assertAlmostEqual(x / straight, 1, delta=0.1)
        self.assertAlmostEqual(y / straight, 1, delta=0.1)


if __name__ == "__main__":
    unittest.main()
