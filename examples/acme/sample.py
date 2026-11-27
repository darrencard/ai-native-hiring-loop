#!/usr/bin/env python3
"""Regenerate the committed Acme sample: ai-native-hiring-loop.html, its Markdown twin, kit.md and ledger.csv.

Inputs, all illustrative (Acme is an invented company; every candidate, interviewer, name and score is invented):
the loop design and the three score sheets bundled with the skill in skills/ai-native-hiring-loop/assets/example/acme/.
The same inputs give the same bytes, so a test can check the committed files.

This skill is outside the Landing Loop's bet record: it reads a team's hiring loop, not a bet, and writes no
landing/<bet>.json key.

Usage, from the repo root (Python 3.11 or later):
  python3 examples/acme/sample.py [--into DIR]
"""

from __future__ import annotations

import sys

if sys.version_info < (3, 11):  # noqa: UP036
    sys.exit("ai-native-hiring-loop needs Python 3.11 or later; try python3.12 (this is " + sys.version.split()[0] + ")")

import argparse  # noqa: E402
import contextlib  # noqa: E402
import io  # noqa: E402
import os  # noqa: E402
import shutil  # noqa: E402
import tempfile  # noqa: E402
from pathlib import Path  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skills" / "ai-native-hiring-loop" / "scripts"))

import run  # noqa: E402

STEM = "ai-native-hiring-loop"
OUTPUTS = {"packet.html": f"{STEM}.html", "packet.md": f"{STEM}.md", "kit.md": "kit.md", "ledger.csv": "ledger.csv"}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--into", help="output folder (default examples/acme)")
    args = p.parse_args(argv)
    into = Path(args.into).resolve() if args.into else ROOT / "examples" / "acme"
    os.chdir(ROOT)  # sources in the ledger are file names, so the output does not depend on where it ran
    with tempfile.TemporaryDirectory() as tmp:
        with contextlib.redirect_stdout(io.StringIO()):
            code = run.main(["demo", "--out", tmp])
        if code:
            print("sample: the demo did not pass its guardrails", file=sys.stderr)
            return code
        into.mkdir(parents=True, exist_ok=True)
        for src, dst in OUTPUTS.items():
            shutil.copy(Path(tmp) / src, into / dst)
    print(f"sample: wrote {', '.join(OUTPUTS.values())} to {into}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
