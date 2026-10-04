#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Verify two independent JieLi flash reads are identical."
    )
    ap.add_argument("read1", type=Path)
    ap.add_argument("read2", type=Path)
    args = ap.parse_args()

    for p in (args.read1, args.read2):
        if not p.is_file():
            print(f"missing file: {p}", file=sys.stderr)
            return 2

    s1 = args.read1.stat().st_size
    s2 = args.read2.stat().st_size
    h1 = sha256(args.read1)
    h2 = sha256(args.read2)

    print(f"read1 size={s1} sha256={h1}")
    print(f"read2 size={s2} sha256={h2}")

    if s1 != s2:
        print("FAIL: sizes differ")
        return 1
    if h1 != h2:
        print("FAIL: SHA-256 differs")
        return 1

    print("OK: reads are byte-identical by size and SHA-256")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
