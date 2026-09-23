#!/usr/bin/env python3
"""
SPHE8202R / STK 0.2.3 rev-8203R container inspector/repacker.

Target evidence recovered from the actual rev-8203R executable and the
preserved P25D80SH image.  This tool is intentionally target-specific.

Important:
- the physical SPI image is 1 MiB;
- the firmware container occupies a prefix determined by the outer checksum;
- bytes after that container are preserved verbatim;
- rom12.bin is the decoded loader/header, not a normal compressed module;
- the loader table contains 27 payload offsets, while STK exposes the first
  17 ordinary module slots in its module UI;
- slot 0x0c is copied raw; other payloads are raw DEFLATE streams only;\n- STK encodes an empty ordinary module as the exact 10-byte sequence\n  `03 00 00 00 00 00 00 00 00 00`.

No output from this tool should be treated as hardware-validated until it has
been flashed under a proven recovery procedure.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import pathlib
import struct
import sys
import zlib
from typing import Iterable, Sequence

FLASH_SIZE = 0x100000
HEADER_LEN = 0x14260
TABLE_BYTES = 0x6C
TABLE_ENTRIES = TABLE_BYTES // 4
PAYLOAD_START = HEADER_LEN + TABLE_BYTES
STK_VISIBLE_COUNT = 17
SPECIAL_RAW_SLOT = 0x0C

VISIBLE_MODULES = (
    "dvd",
    "mpeg",
    "jpeg",
    "ap1",
    "cdrom",
    "iop",
    "iop_rst",
    "drv_other",
    "srvdsp",
    "ap2",
    "ap3",
    "free",
    "rom3",
    "mp4",
    "wma",
    "dvb",
    "dvd_ipod",
)

MODULE_NAMES = VISIBLE_MODULES + tuple(
    f"hidden_{i:02d}" for i in range(STK_VISIBLE_COUNT, TABLE_ENTRIES)
)
MODULE_INDEX = {name: i for i, name in enumerate(MODULE_NAMES)}

MODE3_KEY = bytes.fromhex(
    "a5a5a5a5a1a1a1a1a5a5a5a5a1a1a1a1"
    "b5b5b5b5b1b1b1b1b5b5b5b5b1b1b1b1"
    "a5a5a5a5a1a1a1a1a5a5a5a5a1a1a1a1"
    "b5b5b5b5b1b1b1b1b5b5b5b5b1b1b1b1"
    "e5e5e5e5e1e1e1e1e5e5e5e5e1e1e1e1"
    "f5f5f5f5f1f1f1f1f5f5f5f5f1f1f1f1"
    "e5e5e5e5e1e1e1e1e5e5e5e5e1e1e1e1"
    "f5f5f5f5f1f1f1f1f5f5f5f5f1f1f1f1"
)

MODE4_KEY = bytes.fromhex(
    "a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5"
    "a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1"
    "a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5"
    "a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1"
    "b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5"
    "b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1"
    "b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5"
    "b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1"
    "a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5"
    "a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1"
    "a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5"
    "a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1"
    "b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5"
    "b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1"
    "b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5"
    "b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1"
    "e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5"
    "e1e1e1e1e1e1e1e1e1e1e1e1e1e1e1e1"
    "e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5"
    "e1e1e1e1e1e1e1e1e1e1e1e1e1e1e1e1"
    "f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5"
    "f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1"
    "f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5"
    "f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1"
    "e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5"
    "e1e1e1e1e1e1e1e1e1e1e1e1e1e1e1e1"
    "e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5"
    "e1e1e1e1e1e1e1e1e1e1e1e1e1e1e1e1"
    "f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5"
    "f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1"
    "f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5"
    "f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1"
)


class ContainerError(RuntimeError):
    pass


@dataclasses.dataclass(frozen=True)
class ImageState:
    raw: bytes
    mode: int
    encoded_extent: int
    decoded: bytes
    logical_extent: int
    offsets: tuple[int, ...]
    segments: tuple[bytes, ...]


@dataclasses.dataclass(frozen=True)
class Unpacked:
    data: bytes
    size: int
    extra: bytes


def u32le(buf: bytes | bytearray, off: int) -> int:
    if off < 0 or off + 4 > len(buf):
        raise ContainerError(f"u32 outside buffer at 0x{off:x}")
    return struct.unpack_from("<I", buf, off)[0]


def put_u32le(buf: bytearray, off: int, value: int) -> None:
    struct.pack_into("<I", buf, off, value & 0xFFFFFFFF)


def align_up(value: int, alignment: int) -> int:
    return (value + alignment - 1) // alignment * alignment


def sum16le(buf: bytes | bytearray, start: int, end: int) -> int:
    end = min(end, len(buf))
    total = 0
    for off in range(start, end - 1, 2):
        total = (total + buf[off] + (buf[off + 1] << 8)) & 0xFFFFFFFF
    return total


def detect_mode(raw: bytes) -> int:
    if len(raw) <= 0x70 + 4:
        raise ContainerError("image too short")
    if u32le(raw, 0x68) == 0xA5A5A5A5:
        return 2
    marker = u32le(raw, 0x70)
    if marker == 0xF5F5F5F5:
        return 3
    if marker == 0xB1B1B1B1:
        return 4
    if marker == 0:
        return 1
    raise ContainerError(
        f"unsupported rev-8203R transform markers: +0x68=0x{u32le(raw,0x68):08x}, "
        f"+0x70=0x{marker:08x}"
    )


def transform_mode2(buf: bytearray, extent: int) -> None:
    # STK 8203R FUN_00401E8C.  The operation is involutive.
    for base in range(0x40, extent, 0x20):
        if base + 0x20 > len(buf):
            raise ContainerError("mode-2 transform overruns buffer")
        for i in range(0x20):
            buf[base + i] ^= 0xA5
        for sub in range(0, 0x20, 8):
            a = bytes(buf[base + sub : base + sub + 4])
            buf[base + sub : base + sub + 4] = buf[base + sub + 4 : base + sub + 8]
            buf[base + sub + 4 : base + sub + 8] = a
        a = bytes(buf[base : base + 0x10])
        buf[base : base + 0x10] = buf[base + 0x10 : base + 0x20]
        buf[base + 0x10 : base + 0x20] = a


def xor_transform(buf: bytearray, extent: int, key: bytes) -> None:
    prefix = bytes(buf[:0x28])
    block = len(key)
    for base in range(0, extent, block):
        limit = min(block, len(buf) - base)
        for i in range(limit):
            buf[base + i] ^= key[i]
    buf[:0x28] = prefix


def transform(buf: bytearray, extent: int, mode: int) -> None:
    if mode == 1:
        return
    if mode == 2:
        transform_mode2(buf, extent)
        return
    if mode == 3:
        xor_transform(buf, extent, MODE3_KEY)
        return
    if mode == 4:
        xor_transform(buf, extent, MODE4_KEY)
        return
    raise ContainerError(f"unsupported mode {mode}")


def find_encoded_extent(raw: bytes) -> int:
    expected = u32le(raw, 0x20)
    pos = len(raw) - 1
    while pos > 0x3FF and raw[pos] == 0xFF:
        pos -= 1
    rounded = min((pos & ~0x3FF) + 0x400, len(raw))

    total = sum16le(raw, 0x50, rounded)
    word = rounded // 2
    while True:
        word -= 1
        if word <= 0x400:
            break
        if total == expected:
            return word * 2 + 2
        off = word * 2
        total = (
            total - (raw[off] | (raw[off + 1] << 8))
        ) & 0xFFFFFFFF

    if total == expected:
        return word * 2 + 2
    return rounded


def find_logical_extent(decoded: bytes, encoded_extent: int) -> int:
    expected = u32le(decoded, 0x40)
    total = sum16le(decoded, 0x50, encoded_extent)
    words = encoded_extent // 2
    word = words
    lower = words - 0x201

    while True:
        word -= 1
        if word <= lower:
            break
        if total == expected:
            return word * 2 + 2
        off = word * 2
        total = (
            total - (decoded[off] | (decoded[off + 1] << 8))
        ) & 0xFFFFFFFF

    if total == expected:
        return word * 2 + 2
    return words * 2


def parse_offsets(decoded: bytes, logical_extent: int) -> tuple[int, ...]:
    if logical_extent < PAYLOAD_START:
        raise ContainerError("logical image ends before payload")
    offsets = tuple(
        u32le(decoded, HEADER_LEN + i * 4) for i in range(TABLE_ENTRIES)
    )
    if offsets[0] != 0:
        raise ContainerError("offset table does not begin with zero")
    if any(a > b for a, b in zip(offsets, offsets[1:])):
        raise ContainerError("offset table is not monotonic")
    if PAYLOAD_START + offsets[-1] > logical_extent:
        raise ContainerError("last offset is outside logical image")
    return offsets


def split_segments(
    decoded: bytes, logical_extent: int, offsets: Sequence[int]
) -> tuple[bytes, ...]:
    out: list[bytes] = []
    for i, start_rel in enumerate(offsets):
        end_rel = (
            offsets[i + 1]
            if i + 1 < len(offsets)
            else logical_extent - PAYLOAD_START
        )
        if end_rel < start_rel:
            raise ContainerError(f"negative segment {i}")
        out.append(
            bytes(decoded[PAYLOAD_START + start_rel : PAYLOAD_START + end_rel])
        )
    return tuple(out)


def open_image(raw: bytes) -> ImageState:
    mode = detect_mode(raw)
    encoded_extent = find_encoded_extent(raw)
    if encoded_extent > len(raw):
        raise ContainerError("encoded extent exceeds file")

    decoded_work = bytearray(raw[:encoded_extent])
    transform(decoded_work, encoded_extent, mode)
    decoded = bytes(decoded_work)

    logical_extent = find_logical_extent(decoded, encoded_extent)
    if sum16le(decoded, 0x50, logical_extent) != u32le(decoded, 0x40):
        raise ContainerError("decoded +0x40 checksum does not match")

    if decoded[0x18:0x20] != b"02R-D-02":
        raise ContainerError(
            f"unexpected target version field: {decoded[0x18:0x20]!r}"
        )

    offsets = parse_offsets(decoded, logical_extent)
    segments = split_segments(decoded, logical_extent, offsets)

    return ImageState(
        raw=raw,
        mode=mode,
        encoded_extent=encoded_extent,
        decoded=decoded,
        logical_extent=logical_extent,
        offsets=offsets,
        segments=segments,
    )


def unpack_packed_segment(segment: bytes) -> Unpacked:
    dec = zlib.decompressobj(wbits=-15)
    data = dec.decompress(segment)
    data += dec.flush()
    if not dec.eof:
        raise ContainerError("raw DEFLATE stream did not terminate")

    # The target inflater accepts Z_STREAM_END without requiring avail_in == 0.
    # Fixed-slot replacement may therefore leave opaque bytes after the new
    # stream. Preserve/report them instead of rejecting a target-valid slot.
    extra = dec.unused_data
    return Unpacked(data=data, size=len(data), extra=extra)


def unpack_slot(state: ImageState, index: int) -> Unpacked:
    seg = state.segments[index]
    if index == SPECIAL_RAW_SLOT:
        return Unpacked(
            data=seg,
            size=len(seg),
            extra=b"",
        )
    return unpack_packed_segment(seg)


def pack_packed_segment(data: bytes) -> bytes:
    if not data:
        # Exact special case in STK rev-8203R FUN_00402FEE.
        return b"\\x03\\x00" + b"\\x00" * 8

    obj = zlib.compressobj(
        level=9,
        method=zlib.DEFLATED,
        wbits=-15,
        memLevel=8,
        strategy=zlib.Z_FIXED,
    )
    return obj.compress(data) + obj.flush(zlib.Z_FINISH)


def build_decoded(
    state: ImageState, replacements: dict[int, bytes]
) -> tuple[bytes, tuple[int, ...]]:
    header = bytearray(state.decoded[:HEADER_LEN])
    segments = list(state.segments)

    for index, data in replacements.items():
        if index < 0 or index >= STK_VISIBLE_COUNT:
            raise ContainerError(f"replacement slot {index} is not exposed")
        if index == SPECIAL_RAW_SLOT:
            segments[index] = data
        else:
            segments[index] = pack_packed_segment(data)

    offsets: list[int] = []
    payload = bytearray()
    for seg in segments:
        offsets.append(len(payload))
        payload += seg

    table = bytearray()
    for off in offsets:
        table += struct.pack("<I", off)

    decoded = header + table + payload
    if len(decoded) & 1:
        decoded.append(0)

    put_u32le(decoded, 0x40, sum16le(decoded, 0x50, len(decoded)))
    return bytes(decoded), tuple(offsets)


def build_decoded_fixed_slots(
    state: ImageState, replacements: dict[int, bytes]
) -> tuple[bytes, tuple[int, ...]]:
    """Replace modules without moving any stock payload boundary."""
    decoded = bytearray(state.decoded[: state.logical_extent])

    for index, data in replacements.items():
        if index < 0 or index >= STK_VISIBLE_COUNT:
            raise ContainerError(f"replacement slot {index} is not exposed")

        stock_segment = state.segments[index]
        if index == SPECIAL_RAW_SLOT:
            if len(data) != len(stock_segment):
                raise ContainerError(
                    "fixed-slot special raw replacement must preserve length"
                )
            packed = data
        else:
            packed = pack_packed_segment(data)

        if len(packed) > len(stock_segment):
            raise ContainerError(
                f"slot {index} ({MODULE_NAMES[index]}) needs "
                f"0x{len(packed):x} bytes but stock slot is "
                f"0x{len(stock_segment):x}"
            )

        start = PAYLOAD_START + state.offsets[index]
        decoded[start : start + len(packed)] = packed
        # The rest of the physical slot deliberately remains stock. The
        # recovered target inflater ignores it after Z_STREAM_END.

    put_u32le(
        decoded,
        0x40,
        sum16le(decoded, 0x50, state.logical_extent),
    )
    return bytes(decoded), state.offsets


def encode_preserving_stock_suffix(
    state: ImageState, decoded: bytes
) -> tuple[bytes, int]:
    if state.mode != 4:
        raise ContainerError(
            "target-safe suffix-preserving repack is currently enabled only for mode 4"
        )

    logical_extent = len(decoded)
    encoded_extent = align_up(align_up(logical_extent, 0x20), 0x400)
    if encoded_extent > state.encoded_extent:
        raise ContainerError(
            f"repacked container needs 0x{encoded_extent:x} bytes, "
            f"exceeding stock extent 0x{state.encoded_extent:x}; "
            "refusing to overwrite the post-container flash region"
        )

    # Preserve all original physical bytes by default.  Only the new logical
    # prefix is re-encoded; bytes after it remain opaque stock padding/tail.
    full = bytearray(state.raw)
    for off in range(logical_extent):
        if off < 0x28:
            full[off] = decoded[off]
        else:
            full[off] = decoded[off] ^ MODE4_KEY[off & 0x1FF]

    # +0x20 is one of the untransformed first 0x28 bytes.
    put_u32le(full, 0x20, sum16le(full, 0x50, encoded_extent))
    return bytes(full), encoded_extent


def validate_repacked(
    raw: bytes,
    expected_modules: dict[int, bytes] | None = None,
) -> ImageState:
    state = open_image(raw)
    if expected_modules:
        for index, expected in expected_modules.items():
            actual = unpack_slot(state, index).data
            if actual != expected:
                raise ContainerError(
                    f"re-opened slot {index} ({MODULE_NAMES[index]}) differs"
                )
    return state


def parse_replacements(values: Iterable[str]) -> dict[int, pathlib.Path]:
    out: dict[int, pathlib.Path] = {}
    for item in values:
        if "=" not in item:
            raise ContainerError(
                f"replacement must be NAME=FILE, got {item!r}"
            )
        name, path = item.split("=", 1)
        name = name.removesuffix(".bin")
        if name == "rom12":
            raise ContainerError("rom12/header replacement is not supported yet")
        if name not in MODULE_INDEX or MODULE_INDEX[name] >= STK_VISIBLE_COUNT:
            raise ContainerError(f"unknown/excluded module {name!r}")
        out[MODULE_INDEX[name]] = pathlib.Path(path)
    return out



def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def command_extract(
    path: pathlib.Path,
    output_dir: pathlib.Path,
    include_hidden: bool,
) -> int:
    state = open_image(path.read_bytes())
    output_dir.mkdir(parents=True, exist_ok=True)

    # The decoded loader/header is kept separately because it is not one of
    # the compressed module-table payloads.
    rom12 = state.decoded[:HEADER_LEN]
    (output_dir / "rom12.bin").write_bytes(rom12)

    entries: list[dict[str, object]] = []
    max_count = TABLE_ENTRIES if include_hidden else STK_VISIBLE_COUNT

    for index in range(max_count):
        unpacked = unpack_slot(state, index).data
        name = MODULE_NAMES[index]
        filename = f"{name}.bin"
        (output_dir / filename).write_bytes(unpacked)
        entries.append(
            {
                "index": index,
                "name": name,
                "filename": filename,
                "offset": state.offsets[index],
                "packed_size": len(state.segments[index]),
                "unpacked_size": len(unpacked),
                "special_raw": index == SPECIAL_RAW_SLOT,
                "sha256": sha256_hex(unpacked),
            }
        )

    manifest = {
        "format": "sphe8202r-stk-rev8203r",
        "source_image": path.name,
        "physical_size": len(state.raw),
        "transform_mode": state.mode,
        "encoded_extent": state.encoded_extent,
        "logical_extent": state.logical_extent,
        "header_len": HEADER_LEN,
        "table_entries": TABLE_ENTRIES,
        "stk_visible_count": STK_VISIBLE_COUNT,
        "payload_start": PAYLOAD_START,
        "rom12": {
            "filename": "rom12.bin",
            "size": len(rom12),
            "sha256": sha256_hex(rom12),
        },
        "modules": entries,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(f"extracted_to={output_dir}")
    print(f"visible_modules={STK_VISIBLE_COUNT}")
    print(f"written_modules={max_count}")
    print(f"rom12_size=0x{len(rom12):x}")
    print("manifest=manifest.json")
    return 0


def command_build(
    base_image: pathlib.Path,
    modules_dir: pathlib.Path,
    output: pathlib.Path,
    include_hidden: bool,
) -> int:
    raw = base_image.read_bytes()
    state = open_image(raw)

    rom12_path = modules_dir / "rom12.bin"
    if rom12_path.exists():
        supplied_rom12 = rom12_path.read_bytes()
        stock_rom12 = state.decoded[:HEADER_LEN]
        if supplied_rom12 != stock_rom12:
            raise ContainerError(
                "rom12.bin differs from the base image; loader/header rebuild "
                "is intentionally unsupported"
            )

    limit = TABLE_ENTRIES if include_hidden else STK_VISIBLE_COUNT
    replacements: dict[int, bytes] = {}
    for index in range(limit):
        module_path = modules_dir / f"{MODULE_NAMES[index]}.bin"
        if not module_path.exists():
            continue
        candidate = module_path.read_bytes()
        current = unpack_slot(state, index).data
        if candidate != current:
            replacements[index] = candidate

    decoded, offsets = build_decoded(state, replacements)
    rebuilt, new_extent = encode_preserving_stock_suffix(state, decoded)

    expected = {
        i: unpack_slot(state, i).data for i in range(TABLE_ENTRIES)
    }
    expected.update(replacements)
    reopened = validate_repacked(rebuilt, expected)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(rebuilt)

    print(f"base_image={base_image}")
    print(f"modules_dir={modules_dir}")
    print(f"changed_modules={len(replacements)}")
    for index in sorted(replacements):
        print(
            f"changed slot[{index:02d}] {MODULE_NAMES[index]} "
            f"unpacked=0x{len(replacements[index]):x} "
            f"packed=0x{len(reopened.segments[index]):x} "
            f"offset=0x{offsets[index]:x}"
        )
    print(f"stock_encoded_extent=0x{state.encoded_extent:x}")
    print(f"new_encoded_extent=0x{new_extent:x}")
    print(f"physical_size=0x{len(rebuilt):x}")
    print(f"output={output}")
    print("all_27_payloads_reopen_exact=1")
    print("status=STATIC_REPACK_VALIDATED_REOPEN_ONLY")
    return 0


def command_inspect(path: pathlib.Path) -> int:
    state = open_image(path.read_bytes())
    print(f"physical_size=0x{len(state.raw):x}")
    print(f"transform_mode={state.mode}")
    print(f"encoded_extent=0x{state.encoded_extent:x}")
    print(f"logical_extent=0x{state.logical_extent:x}")
    print(f"header_len=0x{HEADER_LEN:x}")
    print(f"table_bytes=0x{TABLE_BYTES:x}")
    print(f"table_entries={TABLE_ENTRIES}")
    print(f"payload_start=0x{PAYLOAD_START:x}")
    print(
        f"rom12_header_size=0x{HEADER_LEN:x} "
        f"version={state.decoded[0x18:0x20].decode('ascii', 'replace')}"
    )

    for i, seg in enumerate(state.segments):
        name = MODULE_NAMES[i]
        if i == SPECIAL_RAW_SLOT:
            print(
                f"slot[{i:02d}] {name:12s} packed=0x{len(seg):x} "
                f"raw=0x{len(seg):x} special_raw=1"
            )
            continue
        u = unpack_packed_segment(seg)
        print(
            f"slot[{i:02d}] {name:12s} packed=0x{len(seg):x} "
            f"unpacked=0x{len(u.data):x} "
            f"crc32(calc)=0x{zlib.crc32(u.data) & 0xffffffff:08x} "
            f"extra={len(u.extra)}"
        )
    return 0


def command_roundtrip(path: pathlib.Path, output: pathlib.Path | None) -> int:
    raw = path.read_bytes()
    state = open_image(raw)
    expected = {
        i: unpack_slot(state, i).data for i in range(TABLE_ENTRIES)
    }
    decoded, _ = build_decoded(state, {})
    rebuilt, extent = encode_preserving_stock_suffix(state, decoded)

    exact = rebuilt == raw
    print(f"stock_encoded_extent=0x{state.encoded_extent:x}")
    print(f"rebuilt_encoded_extent=0x{extent:x}")
    print(f"byte_exact_full_flash={int(exact)}")

    if not exact:
        first = next(
            (i for i, (a, b) in enumerate(zip(raw, rebuilt)) if a != b),
            None,
        )
        print(
            "first_difference="
            + ("none" if first is None else f"0x{first:x}")
        )
        return_code = 2
    else:
        return_code = 0

    # Every payload must survive a complete encode/decode/extract pass.
    reopened = validate_repacked(rebuilt, expected)
    print(f"reopen_encoded_extent=0x{reopened.encoded_extent:x}")
    print(f"reopen_logical_extent=0x{reopened.logical_extent:x}")
    print("all_27_payloads_roundtrip_exact=1")

    if output is not None:
        output.write_bytes(rebuilt)
    return return_code


def command_repack(
    path: pathlib.Path,
    output: pathlib.Path,
    replacement_args: Sequence[str],
    fixed_slot: bool,
) -> int:
    raw = path.read_bytes()
    state = open_image(raw)
    repl_paths = parse_replacements(replacement_args)
    replacements = {index: p.read_bytes() for index, p in repl_paths.items()}

    expected = {
        i: unpack_slot(state, i).data for i in range(TABLE_ENTRIES)
    }
    expected.update(replacements)

    if fixed_slot:
        decoded, offsets = build_decoded_fixed_slots(state, replacements)
    else:
        decoded, offsets = build_decoded(state, replacements)
    rebuilt, new_extent = encode_preserving_stock_suffix(state, decoded)
    reopened = validate_repacked(rebuilt, expected)

    output.write_bytes(rebuilt)

    print(f"repack_mode={'fixed-slot' if fixed_slot else 'relocating'}")
    print(f"stock_encoded_extent=0x{state.encoded_extent:x}")
    print(f"new_encoded_extent=0x{new_extent:x}")
    print(f"new_logical_extent=0x{reopened.logical_extent:x}")
    print(f"physical_size_preserved=0x{len(rebuilt):x}")
    print(
        f"post_container_bytes_preserved_from=0x{new_extent:x}"
    )
    for index, path_obj in repl_paths.items():
        print(
            f"replaced slot[{index:02d}] {MODULE_NAMES[index]} "
            f"from {path_obj} -> unpacked=0x{len(replacements[index]):x} "
            f"packed=0x{len(reopened.segments[index]):x} "
            f"offset=0x{offsets[index]:x}"
        )
    print("all_27_payloads_reopen_exact=1")
    print("status=STATIC_REPACK_VALIDATED_REOPEN_ONLY")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)

    inspect_p = sub.add_parser("inspect")
    inspect_p.add_argument("image", type=pathlib.Path)

    extract_p = sub.add_parser("extract")
    extract_p.add_argument("image", type=pathlib.Path)
    extract_p.add_argument("output_dir", type=pathlib.Path)
    extract_p.add_argument(
        "--include-hidden",
        action="store_true",
        help="also extract the ten non-UI payload-table slots",
    )

    build_p = sub.add_parser("build")
    build_p.add_argument("base_image", type=pathlib.Path)
    build_p.add_argument("modules_dir", type=pathlib.Path)
    build_p.add_argument("-o", "--output", type=pathlib.Path, required=True)
    build_p.add_argument(
        "--include-hidden",
        action="store_true",
        help="allow hidden_NN.bin files to participate in rebuild",
    )

    rt_p = sub.add_parser("roundtrip")
    rt_p.add_argument("image", type=pathlib.Path)
    rt_p.add_argument("-o", "--output", type=pathlib.Path)

    repack_p = sub.add_parser("repack")
    repack_p.add_argument("image", type=pathlib.Path)
    repack_p.add_argument("-o", "--output", type=pathlib.Path, required=True)
    repack_p.add_argument(
        "--replace",
        action="append",
        default=[],
        metavar="NAME=FILE",
        help="replace one visible module; may be repeated",
    )
    repack_p.add_argument(
        "--fixed-slot",
        action="store_true",
        help=(
            "keep all stock payload offsets and logical extent unchanged; "
            "replacement streams must fit their existing slots"
        ),
    )

    args = p.parse_args(argv)
    try:
        if args.command == "inspect":
            return command_inspect(args.image)
        if args.command == "extract":
            return command_extract(
                args.image, args.output_dir, args.include_hidden
            )
        if args.command == "build":
            return command_build(
                args.base_image,
                args.modules_dir,
                args.output,
                args.include_hidden,
            )
        if args.command == "roundtrip":
            return command_roundtrip(args.image, args.output)
        if args.command == "repack":
            return command_repack(
                args.image,
                args.output,
                args.replace,
                args.fixed_slot,
            )
    except (OSError, ContainerError, zlib.error) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
