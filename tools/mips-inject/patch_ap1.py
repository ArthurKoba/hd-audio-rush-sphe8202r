#!/usr/bin/env python3
"""Build a reversible AP1 compiler/ABI probe patch.

This does NOT build a complete flash image. It replaces one already-understood
44-byte wrapper with an independently compiled function having the same
external contract.

The patch refuses to run unless the original bytes match exactly.
"""

from __future__ import annotations

import argparse
import pathlib

AP1_BASE = 0x8067B800
TARGET_VA = 0x80702D0C
TARGET_OFF = TARGET_VA - AP1_BASE

ORIGINAL = bytes.fromhex(
    "ff008430"
    "e8ffbd27"
    "21288000"
    "21300000"
    "1000bfaf"
    "47ff1b0c"
    "05000424"
    "1000bf8f"
    "00000000"
    "0800e003"
    "1800bd27"
)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("ap1", type=pathlib.Path)
    p.add_argument("replacement", type=pathlib.Path)
    p.add_argument("output", type=pathlib.Path)
    args = p.parse_args()

    ap1 = bytearray(args.ap1.read_bytes())
    replacement = args.replacement.read_bytes()

    if len(replacement) != len(ORIGINAL):
        raise SystemExit(
            f"replacement must be exactly {len(ORIGINAL)} bytes; "
            f"got {len(replacement)}"
        )

    found = bytes(ap1[TARGET_OFF:TARGET_OFF + len(ORIGINAL)])
    if found != ORIGINAL:
        raise SystemExit(
            f"original bytes mismatch at AP1+0x{TARGET_OFF:x}; refusing patch"
        )

    ap1[TARGET_OFF:TARGET_OFF + len(ORIGINAL)] = replacement
    args.output.write_bytes(ap1)

    print(f"patched AP1+0x{TARGET_OFF:x} / VA 0x{TARGET_VA:08x}")
    print(f"size preserved: {len(ap1)} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
