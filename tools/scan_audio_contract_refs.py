#!/usr/bin/env python3
"""Scan raw MIPS modules for recovered Audio Rush contract constants.

The scanner intentionally keeps enum namespaces.  A numeric value may have
multiple valid meanings (for example 0x8000), so the output reports collisions
instead of applying one global name to every matching immediate.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import struct
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


ENUM_RE = re.compile(r"enum\s+(?P<enum>[A-Za-z_][A-Za-z0-9_]*)\s*\{(?P<body>.*?)\};", re.S)
MEMBER_RE = re.compile(
    r"^\s*(?P<name>SPHE_[A-Z0-9_]+)\s*=\s*(?P<value>0x[0-9A-Fa-f]+|[0-9]+)\s*,?",
    re.M,
)
DEFINE_RE = re.compile(
    r"^\s*#define\s+(?P<name>SPHE_(?:ADDR|STATE)_[A-Z0-9_]+)\s+"
    r"(?P<value>0x[0-9A-Fa-f]+|[0-9]+)U?\b",
    re.M,
)

MEMORY_OPCODES = frozenset((0x20, 0x21, 0x23, 0x24, 0x25, 0x28, 0x29, 0x2B))


@dataclass(frozen=True)
class Symbol:
    enum: str
    name: str
    value: int


@dataclass(frozen=True)
class Module:
    name: str
    base: int
    path: Path


def load_contract(path: Path) -> dict[int, list[Symbol]]:
    text = path.read_text(encoding="utf-8")
    by_value: dict[int, list[Symbol]] = defaultdict(list)
    for match in ENUM_RE.finditer(text):
        enum_name = match.group("enum")
        for member in MEMBER_RE.finditer(match.group("body")):
            value = int(member.group("value"), 0)
            by_value[value].append(Symbol(enum_name, member.group("name"), value))

    for match in DEFINE_RE.finditer(text):
        value = int(match.group("value"), 0)
        by_value[value].append(Symbol("define", match.group("name"), value))

    return dict(by_value)


def load_modules(repo_root: Path) -> list[Module]:
    rows: list[Module] = []
    with (repo_root / "analysis" / "modules.csv").open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["isa"] != "MIPS32_LE" or not row["image_base"]:
                continue
            path = repo_root / "firmware" / "modules" / row["module"]
            if path.exists():
                rows.append(Module(row["module"], int(row["image_base"], 0), path))
    return rows


def sign16(value: int) -> int:
    return value - 0x10000 if value & 0x8000 else value


def scan_module(module: Module, known: set[int]) -> dict[int, list[int]]:
    data = module.path.read_bytes()
    words = [
        struct.unpack_from("<I", data, offset)[0]
        for offset in range(0, len(data) - 3, 4)
    ]
    hits: dict[int, list[int]] = defaultdict(list)

    for index, word in enumerate(words):
        pc = module.base + index * 4
        opcode = word >> 26
        rs = (word >> 21) & 0x1F
        rt = (word >> 16) & 0x1F
        imm = word & 0xFFFF
        candidates: set[int] = set()

        # Common immediate-bearing forms.  Preserve the raw 16-bit constant;
        # enum typing later decides the semantic namespace.
        if opcode in (0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E):
            candidates.add(imm)

        # LUI can materialize a complete aligned constant by itself.
        if opcode == 0x0F:
            candidates.add((imm << 16) & 0xFFFFFFFF)

            # Recover the common LUI + ORI/ADDIU constant materialization.
            for lookahead in range(index + 1, min(index + 4, len(words))):
                next_word = words[lookahead]
                next_opcode = next_word >> 26
                next_rs = (next_word >> 21) & 0x1F
                next_rt = (next_word >> 16) & 0x1F
                next_imm = next_word & 0xFFFF

                # Recover absolute data references such as
                # LUI base,0x8000 + LBU/LW/SB/SW ...,offset(base).
                if next_rs == rt and next_opcode in MEMORY_OPCODES:
                    value = (imm << 16) + sign16(next_imm)
                    candidates.add(value & 0xFFFFFFFF)
                    continue

                if next_rt != rt or next_rs != rt:
                    continue
                if next_opcode == 0x0D:  # ORI
                    value = (imm << 16) | next_imm
                    candidates.add(value & 0xFFFFFFFF)
                    break
                if next_opcode == 0x09:  # ADDIU
                    value = (imm << 16) + sign16(next_imm)
                    candidates.add(value & 0xFFFFFFFF)
                    break

        for value in candidates:
            if value in known:
                hits[value].append(pc)

    return dict(hits)


def render_markdown(
    symbols: dict[int, list[Symbol]],
    scans: dict[str, dict[int, list[int]]],
    include_small: bool,
) -> str:
    lines: list[str] = []

    collisions = {
        value: entries for value, entries in symbols.items()
        if len(entries) > 1 and (include_small or value >= 0x20)
    }
    if collisions:
        lines.append("# Context collisions")
        lines.append("")
        for value, entries in sorted(collisions.items()):
            names = ", ".join(f"{x.enum}.{x.name}" for x in entries)
            lines.append(f"- `0x{value:X}`: {names}")
        lines.append("")

    lines.append("# Module references")
    lines.append("")
    for module_name, values in scans.items():
        filtered = {
            value: pcs for value, pcs in values.items()
            if include_small or value >= 0x20
        }
        if not filtered:
            continue
        lines.append(f"## {module_name}")
        lines.append("")
        for value, pcs in sorted(filtered.items()):
            names = " / ".join(x.name for x in symbols[value])
            shown = ", ".join(f"`0x{pc:08X}`" for pc in pcs[:12])
            extra = f" (+{len(pcs) - 12})" if len(pcs) > 12 else ""
            lines.append(
                f"- `0x{value:X}` — {names}: **{len(pcs)}** refs — {shown}{extra}"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument("--include-small", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = args.repo_root.resolve()
    symbols = load_contract(root / "tools" / "mips-inject" / "sphe_audio_contract.h")
    modules = load_modules(root)
    scans = {
        module.name: scan_module(module, set(symbols))
        for module in modules
    }

    if args.json:
        payload = {
            "collisions": {
                f"0x{value:X}": [
                    {"enum": item.enum, "name": item.name}
                    for item in entries
                ]
                for value, entries in symbols.items()
                if len(entries) > 1
            },
            "modules": {
                module: {
                    f"0x{value:X}": {
                        "symbols": [item.name for item in symbols[value]],
                        "addresses": [f"0x{pc:08X}" for pc in pcs],
                    }
                    for value, pcs in values.items()
                }
                for module, values in scans.items()
            },
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(render_markdown(symbols, scans, args.include_small))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
