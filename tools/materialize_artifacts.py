#!/usr/bin/env python3
"""Materialize immutable firmware artifacts stored as base64 parts and verify SHA-256."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "firmware" / "artifacts.json"

def materialize(entry: dict, output_root: Path) -> Path:
    output = output_root / entry["output"]
    output.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    total = 0

    with output.open("wb") as dst:
        for part_name in entry["parts"]:
            part_path = ROOT / part_name
            encoded = "".join(part_path.read_text(encoding="ascii").split())
            chunk = base64.b64decode(encoded, validate=True)
            dst.write(chunk)
            digest.update(chunk)
            total += len(chunk)

    expected_size = int(entry["size"])
    expected_hash = entry["sha256"].lower()
    actual_hash = digest.hexdigest()

    if total != expected_size:
        raise RuntimeError(f"{entry['name']}: size mismatch: {total} != {expected_size}")
    if actual_hash != expected_hash:
        raise RuntimeError(f"{entry['name']}: sha256 mismatch: {actual_hash} != {expected_hash}")

    return output

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "build" / "materialized",
        help="output root; repository-relative artifact paths are appended",
    )
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for entry in manifest["artifacts"]:
        path = materialize(entry, args.output)
        print(f"OK {entry['name']} -> {path}")

    empty_dir = args.output / "firmware" / "extracted"
    empty_dir.mkdir(parents=True, exist_ok=True)
    for name in manifest.get("empty_modules", []):
        (empty_dir / name).write_bytes(b"")

    print(f"OK {len(manifest['artifacts'])} artifacts verified")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
