#!/usr/bin/env python3
"""Build a reversible in-place AP1 compiler/ABI probe patch.

The original 44-byte ApplySurroundModeIndex wrapper is replaced by an
independently compiled 44-byte implementation with the same external contract.
AP1 size, loader range and all other bytes remain unchanged.
"""

from __future__ import annotations

import argparse
import pathlib

AP1_BASE = 0x8067B800
ORIGINAL_AP1_SIZE = 0xA70A0

HOOK_VA = 0x80702D0C
HOOK_OFF = HOOK_VA - AP1_BASE

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

EXPECTED_REPLACEMENT_SIZE = len(ORIGINAL_WRAPPER)


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
    if len(replacement) != EXPECTED_REPLACEMENT_SIZE:
        raise SystemExit(
            f"replacement must be exactly {EXPECTED_REPLACEMENT_SIZE} bytes; "
            f"got {len(replacement)}"
        )

    found = bytes(ap1[HOOK_OFF : HOOK_OFF + len(ORIGINAL_WRAPPER)])
    if found != ORIGINAL_WRAPPER:
        raise SystemExit(
            f"original wrapper mismatch at AP1+0x{HOOK_OFF:x}; refusing patch"
        )

    ap1[HOOK_OFF : HOOK_OFF + len(ORIGINAL_WRAPPER)] = replacement

    if len(ap1) != ORIGINAL_AP1_SIZE:
        raise SystemExit("internal error: in-place patch changed AP1 size")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(ap1)

    print(
        f"replaced AP1+0x{HOOK_OFF:x} / VA 0x{HOOK_VA:08x} "
        f"with {len(replacement)} compiled bytes"
    )
    print(f"AP1 size preserved: 0x{len(ap1):x}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
