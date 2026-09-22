#!/usr/bin/env python3
"""
Sunplus SPHE82xx firmware container primitives recovered from STK 0.2.3.

STATUS: EXPERIMENTAL / STATICALLY RECOVERED.
Do not use output for hardware flashing until a no-change round trip has been
validated against the preserved target dump.

Recovered STK contracts:
- outer checksum at +0x20: wrapping 32-bit sum of little-endian 16-bit words
  over encoded bytes [0x50:encoded_extent]
- inner checksum at +0x40: same sum over decoded bytes [0x50:decoded_extent]
- transform operates in 0x80-byte blocks beginning at +0x40
- module payloads use raw DEFLATE (level 9, method 8, wbits -15,
  memLevel 8, strategy Z_FIXED)
- module slot 0x0C bypasses DEFLATE
- module offset table contains module_count cumulative 32-bit offsets,
  first entry zero, relative to payload_start = header_len + count*4
"""

from __future__ import annotations

import argparse
import dataclasses
import pathlib
import struct
import sys
import zlib
from typing import Iterable, Sequence

TRANSFORM_MARKER = 0xC0D6C0D7
PLAIN_MARKER = 0x65736572  # little-endian bytes: b"rese"
SPECIAL_RAW_SLOT = 0x0C

_MODE3_KEY = bytes([
    0xE5,0xE5,0xE5,0xE5,0xE1,0xE1,0xE1,0xE1,
    0xE5,0xE5,0xE5,0xE5,0xE1,0xE1,0xE1,0xE1,
    0xF5,0xF5,0xF5,0xF5,0xF1,0xF1,0xF1,0xF1,
    0xF5,0xF5,0xF5,0xF5,0xF1,0xF1,0xF1,0xF1,
    0xE5,0xE5,0xE5,0xE5,0xE1,0xE1,0xE1,0xE1,
    0xE5,0xE5,0xE5,0xE5,0xE1,0xE1,0xE1,0xE1,
    0xF5,0xF5,0xF5,0xF5,0xF1,0xF1,0xF1,0xF1,
    0xF5,0xF5,0xF5,0xF5,0xF1,0xF1,0xF1,0xF1,
    0xA5,0xA5,0xA5,0xA5,0xA1,0xA1,0xA1,0xA1,
    0xA5,0xA5,0xA5,0xA5,0xA1,0xA1,0xA1,0xA1,
    0xB5,0xB5,0xB5,0xB5,0xB1,0xB1,0xB1,0xB1,
    0xB5,0xB5,0xB5,0xB5,0xB1,0xB1,0xB1,0xB1,
    0xA5,0xA5,0xA5,0xA5,0xA1,0xA1,0xA1,0xA1,
    0xA5,0xA5,0xA5,0xA5,0xA1,0xA1,0xA1,0xA1,
    0xB5,0xB5,0xB5,0xB5,0xB1,0xB1,0xB1,0xB1,
    0xB5,0xB5,0xB5,0xB5,0xB1,0xB1,0xB1,0xB1,
])


class ContainerError(ValueError):
    pass


@dataclasses.dataclass(frozen=True)
class Layout:
    header_len: int
    module_count: int
    offsets: tuple[int, ...]
    payload_start: int


@dataclasses.dataclass(frozen=True)
class DecodedContainer:
    encoded_extent: int
    decoded_extent: int
    transform_mode: int
    decoded: bytes


def _u32le(buf: bytes | bytearray, off: int) -> int:
    if off < 0 or off + 4 > len(buf):
        raise ContainerError(f"u32 read outside buffer at 0x{off:x}")
    return struct.unpack_from("<I", buf, off)[0]


def _align_up(value: int, alignment: int) -> int:
    return (value + alignment - 1) // alignment * alignment


def sum16le(data: bytes | bytearray, start: int = 0, end: int | None = None) -> int:
    """STK CalculateContainerWordSum: ignore an odd trailing byte."""
    if end is None:
        end = len(data)
    end = min(end, len(data))
    total = 0
    for off in range(start, end - 1, 2):
        total = (total + (data[off] | (data[off + 1] << 8))) & 0xFFFFFFFF
    return total


def detect_transform_mode(encoded: bytes | bytearray) -> int:
    if len(encoded) <= 0x400:
        raise ContainerError("container is too short")
    if _u32le(encoded, 0x114) == TRANSFORM_MARKER:
        return 2
    if _u32le(encoded, 0x100) == TRANSFORM_MARKER:
        return 3
    if _u32le(encoded, 0x100) == PLAIN_MARKER:
        return 1
    raise ContainerError("unknown STK transform marker")


def _transform_mode2_block(block: bytearray) -> None:
    if len(block) != 0x80:
        raise ContainerError("mode-2 transform requires a 0x80-byte block")

    for i in range(0x80):
        block[i] ^= 0xA5

    # Swap the two 4-byte halves of each 8-byte group.
    for base in range(0, 0x80, 8):
        a = block[base:base + 4]
        block[base:base + 4] = block[base + 4:base + 8]
        block[base + 4:base + 8] = a

    # Swap the two 16-byte halves of each 32-byte group.
    for base in range(0, 0x80, 0x20):
        a = block[base:base + 0x10]
        block[base:base + 0x10] = block[base + 0x10:base + 0x20]
        block[base + 0x10:base + 0x20] = a


def _transform_mode3_block(block: bytearray) -> None:
    if len(block) != 0x80:
        raise ContainerError("mode-3 transform requires a 0x80-byte block")
    for i, key in enumerate(_MODE3_KEY):
        block[i] ^= key


def apply_transform(buf: bytearray, logical_len: int, mode: int) -> None:
    """
    Apply the STK transform in-place.

    Modes 2 and 3 are involutions, so the same operation encodes and decodes.
    Mode 1 is plain/no-op.
    """
    if mode == 1:
        return
    if mode not in (2, 3):
        raise ContainerError(f"unsupported transform mode {mode}")

    for off in range(0x40, logical_len, 0x80):
        need = off + 0x80
        if need > len(buf):
            buf.extend(b"\x00" * (need - len(buf)))
        block = bytearray(buf[off:need])
        if mode == 2:
            _transform_mode2_block(block)
        else:
            _transform_mode3_block(block)
        buf[off:need] = block


def _find_encoded_extent(raw: bytes) -> int:
    expected = _u32le(raw, 0x20)

    last = len(raw) - 1
    while last > 0x3FF and raw[last] == 0xFF:
        last -= 1

    extent = min(_align_up(last + 1, 0x400), len(raw))
    total = sum16le(raw, 0x50, extent)

    word_index = extent // 2
    while True:
        word_index -= 1
        if word_index <= 0x400:
            break
        if total == expected:
            return word_index * 2 + 2
        off = word_index * 2
        total = (total - (raw[off] | (raw[off + 1] << 8))) & 0xFFFFFFFF

    if total == expected:
        return word_index * 2 + 2

    # STK continues even when it does not find a shortened extent.
    return extent


def _find_decoded_extent(decoded: bytes, current_extent: int) -> int:
    expected = _u32le(decoded, 0x40)
    total = sum16le(decoded, 0x50, current_extent)

    words = current_extent // 2
    word_index = words
    lower_bound = words - 0x201

    while True:
        word_index -= 1
        if word_index <= lower_bound:
            break
        if total == expected:
            return word_index * 2 + 2
        off = word_index * 2
        total = (total - (decoded[off] | (decoded[off + 1] << 8))) & 0xFFFFFFFF

    if total == expected:
        return word_index * 2 + 2
    return words * 2


def decode_container(raw: bytes) -> DecodedContainer:
    encoded_extent = _find_encoded_extent(raw)
    work = bytearray(raw[:encoded_extent])
    mode = detect_transform_mode(work)
    apply_transform(work, encoded_extent, mode)
    decoded_extent = _find_decoded_extent(work, encoded_extent)
    return DecodedContainer(
        encoded_extent=encoded_extent,
        decoded_extent=decoded_extent,
        transform_mode=mode,
        decoded=bytes(work[:decoded_extent]),
    )


def raw_deflate(data: bytes) -> bytes:
    if not data:
        # Exact zero-length representation emitted by the recovered STK routine.
        return b"\x03" + b"\x00" * 9

    obj = zlib.compressobj(
        level=9,
        method=zlib.DEFLATED,
        wbits=-15,
        memLevel=8,
        strategy=zlib.Z_FIXED,
    )
    return obj.compress(data) + obj.flush(zlib.Z_FINISH)


def raw_inflate(data: bytes) -> bytes:
    obj = zlib.decompressobj(wbits=-15)
    out = obj.decompress(data)
    out += obj.flush()
    return out


def _valid_offset_table(decoded: bytes, header_len: int, count: int) -> tuple[int, ...] | None:
    if count < 1 or count > 32:
        return None
    table_end = header_len + count * 4
    if header_len < 0x50 or table_end > len(decoded):
        return None

    offsets = tuple(_u32le(decoded, header_len + i * 4) for i in range(count))
    if not offsets or offsets[0] != 0:
        return None
    if any(a > b for a, b in zip(offsets, offsets[1:])):
        return None
    if table_end + offsets[-1] > len(decoded):
        return None
    return offsets


def _candidate_layouts(decoded: bytes) -> Iterable[Layout]:
    """
    Recover the loader-embedded layout without hard-coding a target offset.

    This is deliberately stricter than a blind pattern scan:
    candidate LUI/addiu absolute addresses must point inside the decoded image,
    the following module-count immediate must yield a plausible table, and all
    ordinary module streams must successfully raw-inflate.
    """
    n = len(decoded)
    for off in range(0, n - 8, 4):
        word = _u32le(decoded, off)
        opcode = word >> 26
        if opcode != 0x0F:  # LUI
            continue
        rt = (word >> 16) & 0x1F
        hi = word & 0xFFFF

        for j in range(off + 4, min(off + 0x18, n - 4), 4):
            w2 = _u32le(decoded, j)
            if (w2 >> 26) != 0x09:  # ADDIU
                continue
            rs = (w2 >> 21) & 0x1F
            rt2 = (w2 >> 16) & 0x1F
            if rs != rt or rt2 != rt:
                continue

            lo = w2 & 0xFFFF
            if lo & 0x8000:
                lo -= 0x10000
            absolute = ((hi << 16) + lo) & 0xFFFFFFFF
            header_len = (absolute - 0x88000000) & 0xFFFFFFFF
            if not (0x50 <= header_len < n):
                continue

            for k in range(j + 4, min(j + 0x44, n - 4), 4):
                w3 = _u32le(decoded, k)
                if (w3 >> 26) != 0x09:  # ADDIU, matching STK's masked search
                    continue
                count = (w3 & 0xFF) >> 2
                offsets = _valid_offset_table(decoded, header_len, count)
                if offsets is None:
                    continue
                yield Layout(
                    header_len=header_len,
                    module_count=count,
                    offsets=offsets,
                    payload_start=header_len + count * 4,
                )


def validate_layout(decoded: bytes, decoded_extent: int, layout: Layout) -> bool:
    try:
        for i in range(layout.module_count):
            start = layout.payload_start + layout.offsets[i]
            end = decoded_extent
            if i + 1 < layout.module_count:
                end = layout.payload_start + layout.offsets[i + 1]
            if start > end or end > decoded_extent:
                return False
            if i == SPECIAL_RAW_SLOT:
                continue
            raw_inflate(decoded[start:end])
        return True
    except (zlib.error, ContainerError):
        return False


def find_layout(decoded: bytes, decoded_extent: int | None = None) -> Layout:
    if decoded_extent is None:
        decoded_extent = len(decoded)
    valid: list[Layout] = []
    seen: set[tuple[int, int]] = set()
    for layout in _candidate_layouts(decoded):
        key = (layout.header_len, layout.module_count)
        if key in seen:
            continue
        seen.add(key)
        if validate_layout(decoded, decoded_extent, layout):
            valid.append(layout)

    if len(valid) != 1:
        raise ContainerError(
            f"layout scan produced {len(valid)} validated candidates; "
            "do not guess the header/module layout"
        )
    return valid[0]


def extract_modules(decoded: bytes, decoded_extent: int, layout: Layout) -> list[bytes]:
    modules: list[bytes] = []
    for i in range(layout.module_count):
        start = layout.payload_start + layout.offsets[i]
        end = decoded_extent
        if i + 1 < layout.module_count:
            end = layout.payload_start + layout.offsets[i + 1]
        chunk = decoded[start:end]
        modules.append(chunk if i == SPECIAL_RAW_SLOT else raw_inflate(chunk))
    return modules


def build_container(
    decoded_original: bytes,
    layout: Layout,
    modules: Sequence[bytes],
    transform_mode: int,
) -> bytes:
    if len(modules) != layout.module_count:
        raise ContainerError(
            f"expected {layout.module_count} modules, got {len(modules)}"
        )

    header = bytearray(decoded_original[:layout.header_len])
    offsets: list[int] = [0]
    payload = bytearray()

    for i, module in enumerate(modules):
        packed = module if i == SPECIAL_RAW_SLOT else raw_deflate(module)
        payload.extend(packed)
        if i + 1 < layout.module_count:
            offsets.append(len(payload))

    decoded = bytearray(header)
    for off in offsets:
        decoded += struct.pack("<I", off)
    decoded += payload

    if len(decoded) & 1:
        decoded.append(0)

    if len(decoded) < 0x50:
        raise ContainerError("rebuilt decoded container is unexpectedly short")

    # Inner checksum is written before the block transform.
    struct.pack_into("<I", decoded, 0x40, sum16le(decoded, 0x50, len(decoded)))

    logical_len = len(decoded)
    decoded.extend(b"\x00" * 0x80)
    apply_transform(decoded, logical_len, transform_mode)

    aligned_20 = _align_up(logical_len, 0x20)
    aligned_400 = _align_up(aligned_20, 0x400)
    if len(decoded) < aligned_400:
        decoded.extend(b"\x00" * (aligned_400 - len(decoded)))

    # Bytes from aligned_20 onward are zero in STK. Bytes between the original
    # logical end and aligned_20 were part of the pre-zeroed transform tail.
    if aligned_400 > aligned_20:
        decoded[aligned_20:aligned_400] = b"\x00" * (aligned_400 - aligned_20)

    struct.pack_into("<I", decoded, 0x20, sum16le(decoded, 0x50, aligned_400))
    return bytes(decoded[:aligned_400])


def _cmd_inspect(path: pathlib.Path) -> int:
    raw = path.read_bytes()
    dc = decode_container(raw)
    layout = find_layout(dc.decoded, dc.decoded_extent)
    modules = extract_modules(dc.decoded, dc.decoded_extent, layout)

    print(f"input_size=0x{len(raw):x}")
    print(f"encoded_extent=0x{dc.encoded_extent:x}")
    print(f"decoded_extent=0x{dc.decoded_extent:x}")
    print(f"transform_mode={dc.transform_mode}")
    print(f"header_len=0x{layout.header_len:x}")
    print(f"module_count={layout.module_count}")
    print(f"payload_start=0x{layout.payload_start:x}")
    for i, module in enumerate(modules):
        print(f"module[{i:02d}] size=0x{len(module):x}")
    return 0


def _cmd_roundtrip(path: pathlib.Path, output: pathlib.Path | None) -> int:
    raw = path.read_bytes()
    dc = decode_container(raw)
    layout = find_layout(dc.decoded, dc.decoded_extent)
    modules = extract_modules(dc.decoded, dc.decoded_extent, layout)
    rebuilt = build_container(dc.decoded, layout, modules, dc.transform_mode)

    original_extent = raw[:len(rebuilt)]
    exact = rebuilt == original_extent
    print(f"rebuilt_size=0x{len(rebuilt):x}")
    print(f"byte_exact_to_same_extent={int(exact)}")
    if not exact:
        first = next((i for i, (a, b) in enumerate(zip(rebuilt, original_extent)) if a != b), None)
        if first is not None:
            print(f"first_difference=0x{first:x}")
        print("status=NOT_VALIDATED")
    else:
        print("status=ROUNDTRIP_EXACT")

    if output is not None:
        output.write_bytes(rebuilt)
    return 0 if exact else 2


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_inspect = sub.add_parser("inspect", help="decode and inspect a firmware image")
    p_inspect.add_argument("image", type=pathlib.Path)

    p_rt = sub.add_parser("roundtrip", help="rebuild without module changes")
    p_rt.add_argument("image", type=pathlib.Path)
    p_rt.add_argument("-o", "--output", type=pathlib.Path)

    args = parser.parse_args(argv)
    try:
        if args.cmd == "inspect":
            return _cmd_inspect(args.image)
        if args.cmd == "roundtrip":
            return _cmd_roundtrip(args.image, args.output)
    except (OSError, ContainerError, zlib.error) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    raise AssertionError(args.cmd)


if __name__ == "__main__":
    raise SystemExit(main())
