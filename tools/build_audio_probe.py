#!/usr/bin/env python3
"""Build the behavior-preserving SPHE8202R compiler/ABI probe firmware.

This script performs only local build/repack operations:
  C -> MIPS32-LE object -> 44-byte in-place AP1 replacement -> container repack.

It never talks to hardware and never flashes a device.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
from typing import Sequence

ROOT = pathlib.Path(__file__).resolve().parents[1]
INJECT_DIR = ROOT / "tools" / "mips-inject"
CONTAINER_TOOL = ROOT / "tools" / "sunplus_container.py"

STOCK_FLASH_SHA256 = (
    "67d8301f043ecc4d725ec09e38f3c53dd7e71ec26192775811a6a05dd13b545e"
)
STOCK_AP1_SHA256 = (
    "3ccee96ffeb5a8668f055ce97b59fe65084d4f28d47286ee63dd21c4bd96047b"
)


class BuildError(RuntimeError):
    pass


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require_hash(path: pathlib.Path, expected: str, label: str) -> None:
    actual = sha256_file(path)
    if actual != expected:
        raise BuildError(
            f"{label} SHA-256 mismatch: expected {expected}, got {actual}"
        )


def tool(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise BuildError(f"required tool not found in PATH: {name}")
    return path


def run(cmd: Sequence[str], *, cwd: pathlib.Path | None = None) -> None:
    print("+", " ".join(str(x) for x in cmd))
    subprocess.run(
        list(cmd),
        cwd=cwd,
        check=True,
        timeout=30,
    )


def capture_version(cmd: Sequence[str]) -> str:
    try:
        p = subprocess.run(
            list(cmd),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=10,
        )
        return p.stdout.splitlines()[0] if p.stdout else ""
    except Exception:
        return ""


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--stock",
        type=pathlib.Path,
        default=ROOT / "firmware" / "P25D80SH@SOP8.BIN",
    )
    p.add_argument(
        "--ap1",
        type=pathlib.Path,
        default=ROOT / "firmware" / "modules" / "ap1.bin",
    )
    p.add_argument(
        "--out-dir",
        type=pathlib.Path,
        default=ROOT / "build" / "compiler-probe",
    )
    args = p.parse_args(argv)

    stock = args.stock.resolve()
    ap1 = args.ap1.resolve()
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    require_hash(stock, STOCK_FLASH_SHA256, "stock flash")
    require_hash(ap1, STOCK_AP1_SHA256, "stock AP1")

    clang = tool("clang")
    lld = tool("ld.lld")
    objcopy = tool("llvm-objcopy")

    obj = out / "surround_probe.o"
    elf = out / "surround_probe.elf"
    raw = out / "surround_probe.bin"
    patched_ap1 = out / "ap1.compiler-probe.bin"
    image = out / "P25D80SH.compiler-probe.bin"

    run(
        [
            clang,
            "--target=mipsel-none-elf",
            "-march=mips32",
            "-mabi=32",
            "-msoft-float",
            "-ffreestanding",
            "-fno-builtin",
            "-fno-pic",
            "-mno-abicalls",
            "-G0",
            "-fno-stack-protector",
            "-fno-unwind-tables",
            "-fno-asynchronous-unwind-tables",
            "-O2",
            "-fomit-frame-pointer",
            "-ffunction-sections",
            "-fdata-sections",
            "-c",
            str(INJECT_DIR / "surround_probe.c"),
            "-o",
            str(obj),
        ]
    )

    run(
        [
            lld,
            "-m",
            "elf32ltsmip",
            "-T",
            str(INJECT_DIR / "surround_probe.ld"),
            str(obj),
            "-o",
            str(elf),
        ]
    )

    run(
        [
            objcopy,
            "-O",
            "binary",
            "--only-section=.text",
            str(elf),
            str(raw),
        ]
    )

    if raw.stat().st_size != 44:
        raise BuildError(
            f"compiled wrapper is {raw.stat().st_size} bytes, expected 44"
        )

    run(
        [
            sys.executable,
            str(INJECT_DIR / "patch_ap1.py"),
            str(ap1),
            str(raw),
            str(patched_ap1),
        ]
    )

    if patched_ap1.stat().st_size != ap1.stat().st_size:
        raise BuildError("in-place AP1 probe unexpectedly changed module size")

    run(
        [
            sys.executable,
            str(CONTAINER_TOOL),
            "repack",
            str(stock),
            "-o",
            str(image),
            "--replace",
            f"ap1={patched_ap1}",
        ]
    )

    # Re-open through the same independent parser.  The repack command already
    # validates all payloads; inspect adds a separate command-level parse gate.
    run(
        [
            sys.executable,
            str(CONTAINER_TOOL),
            "inspect",
            str(image),
        ]
    )

    info = {
        "status": "static-build-only",
        "stock_flash_sha256": sha256_file(stock),
        "stock_ap1_sha256": sha256_file(ap1),
        "compiled_wrapper_sha256": sha256_file(raw),
        "patched_ap1_sha256": sha256_file(patched_ap1),
        "candidate_flash_sha256": sha256_file(image),
        "patched_ap1_size": patched_ap1.stat().st_size,
        "candidate_flash_size": image.stat().st_size,
        "clang": capture_version([clang, "--version"]),
        "ld_lld": capture_version([lld, "--version"]),
        "llvm_objcopy": capture_version([objcopy, "--version"]),
        "hardware_validated": False,
    }
    (out / "build-info.json").write_text(
        json.dumps(info, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print()
    print("Build complete (static validation only)")
    print(f"candidate: {image}")
    print(f"sha256: {info['candidate_flash_sha256']}")
    print("hardware_validated=false")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (BuildError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
