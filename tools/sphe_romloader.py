#!/usr/bin/env python3
"""
Headless UART client for the Sunplus SPHE82xx ROM/RAM loader path recovered
from STK 0.2.3 rev-8203R.

Current hardware-facing commands are intentionally read-only:
  - handshake: verify the Boot ROM 'A' echo
  - read-flash: bootstrap the stock RAM loader and dump SPI flash

The tool extracts the RAM-loader bytes from the preserved STK executable/ZIP
at runtime.  The vendor loader blob is not duplicated in this repository.

Evidence/validation level:
  - host protocol and register scripts: implementation-recovered from STK
  - target default profile: candidate (8202 non-share, 16-bit, 115200)
  - hardware execution: not yet proven on this board

Requires pyserial for hardware access:
  python3 -m pip install pyserial
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import io
import pathlib
import struct
import sys
import time
import zipfile
from typing import Iterable, Sequence

STK_REV8203R_MEMBER = "STK Sunplus Tool Kit 0.2.3 (rev 8203R) English.exe"
STK_REV8203R_SHA256 = (
    "e58d7d6f6f9cff67cbcf7f2b1191afbf0ffc2de4ca63c4dbda30c486c82dbc89"
)

SYSTEM_CONFIGS = {
    0: "8200-and-8210",
    1: "8202-share",
    2: "8202-non-share",
    3: "8202-e",
    4: "7300",
    5: "82xx-216-spi",
    6: "82xx-256-spi",
    7: "8202l-128-spi",
}
SYSTEM_CONFIG_BY_NAME = {v: k for k, v in SYSTEM_CONFIGS.items()}

BAUD_SELECTORS = {
    57600: 0x74,
    115200: 0x3A,
    230400: 0x1D,
}

# STK resident RAM-loader images selected by system_config.
# Values are virtual addresses inside the verified rev-8203R STK executable.
LOADER_IMAGES = {
    # Exact rev-8203R selector mapping recovered from the upload action:
    # system 6 -> 82XX_256_SPI blob
    # system 7 -> 8202L_128_SPI blob
    # selector 8 is a legacy/internal path not exposed by the visible UI.
    6: (0x004E71E0, 0x1D88),
    7: (0x004E23E0, 0x2578),
    8: (0x004E0000, 0x23C8),
}
# Visible system configurations 0..5, including the target profile 2,
# use the common loader image.
DEFAULT_LOADER_IMAGE = (0x004E4960, 0x2878)

ROM_LOADER_BASE = 0x00019000
ROM_LOADER_PARAM_BAUD = 0x00018FE8
ROM_LOADER_PARAM_VARIANT = 0x00018FEC

MAX_FLASH_SIZE = 0x200000


class LoaderError(RuntimeError):
    pass


@dataclasses.dataclass(frozen=True)
class Profile:
    system_config: int
    sdram_bus_bits: int
    baud: int

    @property
    def system_name(self) -> str:
        return SYSTEM_CONFIGS[self.system_config]

    @property
    def bus_selector(self) -> int:
        return 0 if self.sdram_bus_bits == 16 else 1


class PEImage:
    def __init__(self, data: bytes):
        self.data = bytearray(data)
        if len(data) < 0x100 or data[:2] != b"MZ":
            raise LoaderError("STK source is not a PE executable")
        peoff = struct.unpack_from("<I", data, 0x3C)[0]
        if data[peoff : peoff + 4] != b"PE\0\0":
            raise LoaderError("invalid PE signature")

        number_of_sections = struct.unpack_from("<H", data, peoff + 6)[0]
        optional_size = struct.unpack_from("<H", data, peoff + 20)[0]
        optional = peoff + 24
        magic = struct.unpack_from("<H", data, optional)[0]
        if magic != 0x10B:
            raise LoaderError(f"expected PE32 image, magic=0x{magic:04x}")
        self.image_base = struct.unpack_from("<I", data, optional + 28)[0]

        section_table = optional + optional_size
        self.sections: list[tuple[int, int, int, int]] = []
        for i in range(number_of_sections):
            off = section_table + i * 40
            virtual_size = struct.unpack_from("<I", data, off + 8)[0]
            virtual_address = struct.unpack_from("<I", data, off + 12)[0]
            raw_size = struct.unpack_from("<I", data, off + 16)[0]
            raw_ptr = struct.unpack_from("<I", data, off + 20)[0]
            self.sections.append(
                (virtual_address, max(virtual_size, raw_size), raw_ptr, raw_size)
            )

    def va_to_offset(self, va: int) -> int:
        rva = va - self.image_base
        if rva < 0:
            raise LoaderError(f"VA 0x{va:08x} is below PE image base")
        for start, span, raw_ptr, raw_size in self.sections:
            if start <= rva < start + span:
                delta = rva - start
                if delta >= raw_size:
                    raise LoaderError(
                        f"VA 0x{va:08x} lies in virtual-only PE section tail"
                    )
                return raw_ptr + delta
        raise LoaderError(f"VA 0x{va:08x} is not mapped by a PE section")

    def read_va(self, va: int, size: int) -> bytes:
        off = self.va_to_offset(va)
        end = off + size
        if end > len(self.data):
            raise LoaderError("PE VA read exceeds file")
        return bytes(self.data[off:end])

    def patch_va(self, va: int, payload: bytes) -> None:
        off = self.va_to_offset(va)
        end = off + len(payload)
        if end > len(self.data):
            raise LoaderError("PE VA patch exceeds file")
        self.data[off:end] = payload

    def patch_u32(self, va: int, value: int) -> None:
        self.patch_va(va, struct.pack("<I", value & 0xFFFFFFFF))


def read_verified_stk(path: pathlib.Path) -> bytes:
    raw: bytes
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path, "r") as zf:
            names = zf.namelist()
            match = next(
                (n for n in names if n.endswith(STK_REV8203R_MEMBER)),
                None,
            )
            if match is None:
                raise LoaderError(
                    f"{STK_REV8203R_MEMBER!r} not found in {path}"
                )
            raw = zf.read(match)
    else:
        raw = path.read_bytes()

    digest = hashlib.sha256(raw).hexdigest()
    if digest != STK_REV8203R_SHA256:
        raise LoaderError(
            "unsupported STK executable: "
            f"sha256={digest}, expected {STK_REV8203R_SHA256}"
        )
    return raw


def apply_write_loader_patches(pe: PEImage, system_config: int) -> None:
    # Recovered from the WRITE action before ROM/RAM-loader bootstrap.
    if system_config == 3:
        pe.patch_u32(0x004E37A8, 0x0C006947)
        pe.patch_u32(0x004E3868, 0x0C006528)
        return

    if system_config == 0:
        pe.patch_u32(0x004E7F90, 0x0C006853)
        pe.patch_u32(0x004E808C, 0x0C006610)
        return

    if system_config == 5:
        pe.patch_u32(0x004E10C8, 0x08006862)
        pe.patch_u32(0x004E118C, 0x08006CA8)
        return

    pe.patch_u32(0x004E5E44, 0x0C006AFB)
    pe.patch_u32(0x004E5FBC, 0x0C006AFB)
    pe.patch_u32(0x004E60D0, 0x0C006616)
    pe.patch_va(0x004E6484 + 9, b" u")


def extract_write_loader(stk_source: pathlib.Path, system_config: int) -> bytes:
    exe = read_verified_stk(stk_source)
    pe = PEImage(exe)
    apply_write_loader_patches(pe, system_config)
    va, size = LOADER_IMAGES.get(system_config, DEFAULT_LOADER_IMAGE)
    blob = pe.read_va(va, size)
    if len(blob) != size or size % 4:
        raise LoaderError("unexpected WRITE RAM-loader size")
    return blob


def apply_read_loader_patches(pe: PEImage, system_config: int) -> None:
    # Recovered from the READ action before ROM/RAM-loader bootstrap.
    if system_config == 3:
        pe.patch_u32(0x004E37A8, 0x08006921)
        pe.patch_u32(0x004E3868, 0x08006D14)
        return

    if system_config == 0:
        pe.patch_u32(0x004E7F90, 0x0800679B)
        pe.patch_u32(0x004E808C, 0x08006B18)
        return

    if system_config == 5:
        pe.patch_u32(0x004E10C8, 0x08006862)
        pe.patch_u32(0x004E118C, 0x08006CA8)
        return

    pe.patch_u32(0x004E5E44, 0x08006DC0)
    pe.patch_u32(0x004E5FBC, 0x080069C7)
    pe.patch_u32(0x004E60D0, 0x08006DC0)

    # Change the stock "SPI Flash upgrade" loader text to the READ variant,
    # exactly as the STK READ path does.
    pe.patch_va(0x004E6484 + 9, b"\x0a\x00")

    if system_config < 6:
        pe.patch_u32(0x004E7140, 0x8C920000)
    else:
        pe.patch_u32(0x004E7140, 0x0C006E06)


def extract_read_loader(stk_source: pathlib.Path, system_config: int) -> bytes:
    exe = read_verified_stk(stk_source)
    pe = PEImage(exe)
    apply_read_loader_patches(pe, system_config)
    va, size = LOADER_IMAGES.get(system_config, DEFAULT_LOADER_IMAGE)
    blob = pe.read_va(va, size)
    if len(blob) != size or size % 4:
        raise LoaderError("unexpected RAM-loader size")
    return blob


def system_init_script(profile: Profile) -> tuple[tuple[int, int], ...]:
    c = profile.system_config
    bus32 = profile.sdram_bus_bits == 32
    w: list[tuple[int, int]] = []

    if c == 0:
        if bus32:
            w += [
                (0x1FFE8070, 0x5801),
                (0x1FFE8010, 0x5A),
                (0x1FFE8014, 0x08),
                (0x1FFE8018, 0x19),
                (0x1FFE8300, 0x14E),
                (0x1FFE8304, 0x09A9),
            ]
        else:
            w += [
                (0x1FFE8070, 0x5802),
                (0x1FFE8014, 0x08),
                (0x1FFE8018, 0x19),
                (0x1FFE8300, 0x13D),
                (0x1FFE8304, 0x19A7),
            ]

    elif c == 1:
        w += [
            (0x1FFE8070, 0x5831 if bus32 else 0x5811),
            (0x1FFE8010, 0xFFFF),
            (0x1FFE8014, 0x10),
            (0x1FFE8018, 0x06),
            (0x1FFE8300, 0x14E if bus32 else 0x13D),
            (0x1FFE8304, 0x09A9 if bus32 else 0x19A7),
        ]

    elif c == 3:
        w += [
            (0x1FFE8010, 0x565A),
            (0x1FFE8014, 0x08),
            (0x1FFE8018, 0x19),
            (0x1FFE8300, 0x14E if bus32 else 0x13D),
            (0x1FFE8304, 0x09A9 if bus32 else 0x19A7),
        ]

    elif c == 4:
        w += [
            (0x1FFE8070, 0x583F if bus32 else 0x581F),
            (0x1FFE8010, 0xFFFF),
            (0x1FFE8014, 0x10),
            (0x1FFE8018, 0x11),
            (0x1FFE801C, 0xA1),
            (0x1FFE8300, 0x14E if bus32 else 0x13D),
            (0x1FFE8304, 0x09A9 if bus32 else 0x19A7),
        ]

    elif c == 5:
        w += [
            (0x1FFE8070, 0x583C if bus32 else 0x581C),
            (0x1FFE948C, 0xF000),
            (0x1FFE9490, 0xFFFF),
            (0x1FFE8378, 0x43EC),
            (0x1FFE8044, 0x0E3F),
            (0x1FFE8048, 0x0101),
            (0x1FFE804C, 0x3004),
            (0x1FFE8300, 0x14E if bus32 else 0x13D),
            (0x1FFE8304, 0x0FA9 if bus32 else 0x19A7),
        ]

    else:
        # Covers the GUI's 8202 non-share / 82xx SPI / 8202L profiles.
        w += [
            (0x1FFE8070, 0x583F if bus32 else 0x581F),
            (0x1FFE8010, 0xFFFF),
            (0x1FFE8014, 0x10),
            (0x1FFE8018, 0x06),
            (0x1FFE8300, 0x14E if bus32 else 0x13D),
            (0x1FFE8304, 0x09A9 if bus32 else 0x19A7),
        ]

    w += [
        (0x1FFE8308, 0x33),
        (0x1FFE8310, 0x01),
        (0x1FFE8330, 0x34C3),
        (0x1FFE8314, 0x0540 if bus32 else 0x0541),
        (0x1FFE830C, 0x01),
        (0x1FFE834C, 0x1AB7),
    ]
    return tuple(w)


class SerialTransport:
    def __init__(
        self,
        port: str,
        baud: int,
        timeout: float = 1.5,
    ):
        try:
            import serial  # type: ignore
        except ImportError as exc:
            raise LoaderError(
                "pyserial is required for hardware access "
                "(python3 -m pip install pyserial)"
            ) from exc

        self.serial_module = serial
        self.port = serial.Serial(
            port=port,
            baudrate=baud,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=timeout,
            write_timeout=timeout,
        )

    def close(self) -> None:
        self.port.close()

    def purge(self) -> None:
        self.port.reset_input_buffer()
        self.port.reset_output_buffer()

    def write(self, data: bytes) -> None:
        n = self.port.write(data)
        if n != len(data):
            raise LoaderError(f"short serial write: {n}/{len(data)}")

    def read_exact(self, size: int) -> bytes:
        out = bytearray()
        while len(out) < size:
            chunk = self.port.read(size - len(out))
            if not chunk:
                raise LoaderError(
                    f"serial timeout reading {size} bytes "
                    f"({len(out)} received)"
                )
            out += chunk
        return bytes(out)


class SPHERomLoader:
    def __init__(self, transport: SerialTransport, profile: Profile):
        self.io = transport
        self.profile = profile

    def expect_echo(self, value: int) -> None:
        b = bytes([value])
        self.io.write(b)
        got = self.io.read_exact(1)
        if got != b:
            raise LoaderError(
                f"echo mismatch: sent 0x{value:02x}, got {got.hex()}"
            )

    def write32(self, address: int, value: int, *, ack_len: int = 1) -> bytes:
        packet = b"W" + struct.pack("<II", address & 0xFFFFFFFF, value & 0xFFFFFFFF)
        self.io.write(packet)
        ack = self.io.read_exact(ack_len)
        if ack[-1:] != b"W":
            raise LoaderError(
                f"W ack mismatch at 0x{address:08x}: {ack.hex()}"
            )
        return ack

    def read32(self, address: int) -> int:
        self.io.write(b"R" + struct.pack("<I", address & 0xFFFFFFFF))
        reply = self.io.read_exact(5)
        if reply[:1] != b"R":
            raise LoaderError(
                f"R reply mismatch at 0x{address:08x}: {reply.hex()}"
            )
        return struct.unpack_from("<I", reply, 1)[0]

    def bootstrap_read_loader(self, loader: bytes) -> None:
        self.io.purge()

        self.expect_echo(ord("A"))

        self.write32(0x1FFE8918, 0)
        self.write32(0x1FFE8914, BAUD_SELECTORS[self.profile.baud])

        for address, value in system_init_script(self.profile):
            self.write32(address, value)

        self.expect_echo(ord("C"))

        for address in (0x18FFC, 0x18FF8, 0x18FF4, 0x18FF0):
            self.write32(address, 0)

        variant = (
            1 if self.profile.system_config == 6
            else 2 if self.profile.system_config == 7
            else 3 if self.profile.system_config == 8
            else 0
        )
        self.write32(ROM_LOADER_PARAM_VARIANT, variant)
        self.write32(ROM_LOADER_PARAM_BAUD, 0xE100)

        first = struct.unpack_from("<I", loader, 0)[0]
        self.write32(ROM_LOADER_BASE, first)

        for off in range(4, len(loader), 4):
            self.io.write(b"w" + loader[off : off + 4])
            ack = self.io.read_exact(1)
            if ack != b"w":
                raise LoaderError(
                    f"sequential loader write failed at +0x{off:x}: {ack.hex()}"
                )

    def start_ram_loader(self) -> None:
        self.expect_echo(ord("S"))

        # STK expects two leading status bytes before the first W ack here.
        self.write32(0x00000000, 0x08006400, ack_len=3)
        self.write32(0x00000004, 0)
        self.write32(0x00000008, 0)

        # Preserve the exact READ/modify/write sequence used by STK.
        _ = self.read32(0x1FFE8048)
        self.write32(0x1FFE8048, 0x0000203F)
        self.write32(0x1FFE8008, 0)

    def wait_console_ready(self, seconds: float = 5.0) -> bytes:
        deadline = time.monotonic() + seconds
        transcript = bytearray()
        while time.monotonic() < deadline:
            chunk = self.io.port.read(1)
            if not chunk:
                continue
            value = chunk[0]
            if value == 0:
                return bytes(transcript)
            transcript.append(value)
            if 0x20 <= value <= 0x7A:
                sys.stderr.write(chr(value))
                sys.stderr.flush()
            elif value == 0x0D:
                sys.stderr.write("\n")
                sys.stderr.flush()
        raise LoaderError("RAM-loader ready timeout (no NUL terminator)")

    def read_flash(self) -> bytes:
        transcript = self.wait_console_ready(5.0)
        if transcript:
            sys.stderr.write("\n")

        size_raw = self.io.read_exact(4)
        size = struct.unpack("<I", size_raw)[0]
        if size <= 0 or size > MAX_FLASH_SIZE:
            raise LoaderError(f"invalid ROM size from loader: 0x{size:x}")
        if size % 16:
            raise LoaderError(
                f"unexpected non-16-byte-aligned ROM size: 0x{size:x}"
            )

        data = bytearray()

        # STK sends the low byte currently in the shared transfer buffer
        # before the first 16-byte block and then echoes the first byte of each
        # received block to request/ack the next block.
        self.io.write(size_raw[:1])

        while len(data) < size:
            block = self.io.read_exact(16)
            data += block
            self.io.write(block[:1])

        return bytes(data)


def parse_system_config(value: str) -> int:
    if value.isdigit():
        n = int(value, 10)
        if n in SYSTEM_CONFIGS:
            return n
    if value in SYSTEM_CONFIG_BY_NAME:
        return SYSTEM_CONFIG_BY_NAME[value]
    raise argparse.ArgumentTypeError(
        "system config must be 0..7 or one of: "
        + ", ".join(SYSTEM_CONFIG_BY_NAME)
    )


def add_profile_args(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--system-config",
        type=parse_system_config,
        default=2,
        help="STK system configuration (default: 2 / 8202-non-share)",
    )
    p.add_argument(
        "--sdram-bus",
        type=int,
        choices=(16, 32),
        default=16,
        help="SDRAM bus width (default: 16)",
    )
    p.add_argument(
        "--baud",
        type=int,
        choices=tuple(BAUD_SELECTORS),
        default=115200,
        help="UART baud rate (default: 115200)",
    )


def make_profile(args: argparse.Namespace) -> Profile:
    return Profile(
        system_config=args.system_config,
        sdram_bus_bits=args.sdram_bus,
        baud=args.baud,
    )


def command_profiles() -> int:
    print("system_config:")
    for index, name in SYSTEM_CONFIGS.items():
        print(f"  {index}: {name}")
    print("sdram_bus: 16, 32")
    print("baud: 57600, 115200, 230400")
    print()
    print("target candidate: system_config=2, sdram_bus=16, baud=115200")
    print("validation: implementation/profile candidate; not hardware-proven")
    return 0


def command_extract_loader(args: argparse.Namespace) -> int:
    profile = make_profile(args)
    if args.kind == "read":
        blob = extract_read_loader(args.stk, profile.system_config)
    else:
        blob = extract_write_loader(args.stk, profile.system_config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(blob)
    print(f"kind={args.kind}")
    print(f"system_config={profile.system_config}:{profile.system_name}")
    print(f"loader_size=0x{len(blob):x}")
    print(f"loader_sha256={hashlib.sha256(blob).hexdigest()}")
    print(f"output={args.output}")
    return 0


def command_handshake(args: argparse.Namespace) -> int:
    profile = make_profile(args)
    io_obj = SerialTransport(args.port, profile.baud, args.timeout)
    try:
        io_obj.purge()
        client = SPHERomLoader(io_obj, profile)
        client.expect_echo(ord("A"))
        print("boot_rom_echo=A")
        print("status=BOOT_ROM_HANDSHAKE_OK")
        return 0
    finally:
        io_obj.close()


def command_read_flash(args: argparse.Namespace) -> int:
    profile = make_profile(args)
    loader = extract_read_loader(args.stk, profile.system_config)
    io_obj = SerialTransport(args.port, profile.baud, args.timeout)
    try:
        client = SPHERomLoader(io_obj, profile)
        print(
            f"profile={profile.system_config}:{profile.system_name} "
            f"sdram_bus={profile.sdram_bus_bits} baud={profile.baud}",
            file=sys.stderr,
        )
        print(
            f"ram_loader_size=0x{len(loader):x} "
            f"sha256={hashlib.sha256(loader).hexdigest()}",
            file=sys.stderr,
        )
        client.bootstrap_read_loader(loader)
        client.start_ram_loader()
        image = client.read_flash()

        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(image)
        print(f"flash_size=0x{len(image):x}")
        print(f"sha256={hashlib.sha256(image).hexdigest()}")
        print(f"output={args.output}")
        print("status=READ_ONLY_DUMP_COMPLETE")
        return 0
    finally:
        io_obj.close()


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("profiles", help="list recovered STK configuration profiles")

    extract_p = sub.add_parser(
        "extract-loader",
        help="extract a patched READ/WRITE RAM-loader from verified STK",
    )
    extract_p.add_argument("--stk", type=pathlib.Path, required=True)
    extract_p.add_argument(
        "--kind",
        choices=("read", "write"),
        default="read",
        help="loader behavior to reconstruct (default: read)",
    )
    extract_p.add_argument("-o", "--output", type=pathlib.Path, required=True)
    add_profile_args(extract_p)

    hs_p = sub.add_parser(
        "handshake",
        help="read-only Boot ROM A/echo probe",
    )
    hs_p.add_argument("--port", required=True)
    hs_p.add_argument("--timeout", type=float, default=1.5)
    add_profile_args(hs_p)

    read_p = sub.add_parser(
        "read-flash",
        help="bootstrap stock READ loader and dump SPI flash",
    )
    read_p.add_argument("--port", required=True)
    read_p.add_argument("--stk", type=pathlib.Path, required=True)
    read_p.add_argument("-o", "--output", type=pathlib.Path, required=True)
    read_p.add_argument("--timeout", type=float, default=1.5)
    add_profile_args(read_p)

    args = p.parse_args(argv)
    try:
        if args.command == "profiles":
            return command_profiles()
        if args.command == "extract-loader":
            return command_extract_loader(args)
        if args.command == "handshake":
            return command_handshake(args)
        if args.command == "read-flash":
            return command_read_flash(args)
    except (OSError, LoaderError, zipfile.BadZipFile) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
