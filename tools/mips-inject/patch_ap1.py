#!/usr/bin/env python3
"""Build a reversible AP1 compiler/ABI probe patch.

The original AP1 startup/runtime remains intact.  The probe:
1. extends AP1 through the statically unused gap up to VA 0x80723000;
2. appends one independently compiled behavior-preserving audio wrapper;
3. replaces the first two instructions of ApplySurroundModeIndex with
   a local absolute jump to the appended wrapper.

This file only patches the extracted AP1 module.  The Sunplus container is
rebuilt separately by tools/sunplus_container.py.
"""

from __future__ import annotations

import argparse
import pathlib

AP1_BASE = 0x8067B800
ORIGINAL_AP1_SIZE = 0xA70A0

HOOK_VA = 0x80702D0C
HOOK_OFF = HOOK_VA - AP1_BASE

INJECT_VA = 0x80723000
INJECT_OFF = INJECT_VA - AP1_BASE

NEXT_CONFIRMED_MODULE_BASE = 0x8073F000

ORIGINAL_WRAPPER = bytes.fromhex(
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

# MIPS32 LE: j 0x80723000 ; nop
TRAMPOLINE = bytes.fromhex("008c1c0800000000")

EXPECTED_INJECT_SIZE = 44


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("ap1", type=pathlib.Path)
    p.add_argument("replacement", type=pathlib.Path)
    p.add_argument("output", type=pathlib.Path)
    args = p.parse_args()

    ap1 = bytearray(args.ap1.read_bytes())
    replacement = args.replacement.read_bytes()

    if len(ap1) != ORIGINAL_AP1_SIZE:
        raise SystemExit(
            f"unexpected AP1 size 0x{len(ap1):x}; "
            f"expected 0x{ORIGINAL_AP1_SIZE:x}"
        )
    if len(replacement) != EXPECTED_INJECT_SIZE:
        raise SystemExit(
            f"replacement must be exactly {EXPECTED_INJECT_SIZE} bytes; "
            f"got {len(replacement)}"
        )

    found = bytes(ap1[HOOK_OFF : HOOK_OFF + len(ORIGINAL_WRAPPER)])
    if found != ORIGINAL_WRAPPER:
        raise SystemExit(
            f"original wrapper mismatch at AP1+0x{HOOK_OFF:x}; refusing patch"
        )

    if len(ap1) > INJECT_OFF:
        raise SystemExit("injection address overlaps the original AP1 image")

    ap1.extend(b"\x00" * (INJECT_OFF - len(ap1)))
    ap1.extend(replacement)
    ap1[HOOK_OFF : HOOK_OFF + len(TRAMPOLINE)] = TRAMPOLINE

    runtime_end = AP1_BASE + len(ap1)
    if runtime_end >= NEXT_CONFIRMED_MODULE_BASE:
        raise SystemExit(
            f"extended AP1 reaches 0x{runtime_end:08x}, "
            "overlapping the next confirmed module"
        )

    args.output.write_bytes(ap1)

    print(
        f"hook: AP1+0x{HOOK_OFF:x} / VA 0x{HOOK_VA:08x} "
        f"-> 0x{INJECT_VA:08x}"
    )
    print(
        f"AP1 size: 0x{ORIGINAL_AP1_SIZE:x} -> 0x{len(ap1):x}; "
        f"runtime end 0x{runtime_end:08x}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
