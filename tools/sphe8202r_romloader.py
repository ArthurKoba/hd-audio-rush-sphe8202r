#!/usr/bin/env python3
"""
Headless Sunplus SPHE8202R UART ROM-loader client.

Target scope:
- HD Audio Rush 5.1, PCB SPHE8202RD_SPDIF_V02;
- STK system profile: "8202 Non Share Mode";
- SDRAM bus: 16 bits;
- ROM-loader serial protocol recovered from STK 0.2.3 rev-8203R.

Safety:
- no flash-write command is exposed;
- canonical firmware files are never modified in place;
- read-firmware uses the vendor read-stub reconstructed from the preserved STK
  executable;
- arbitrary write32 requires --allow-write.

Dependency:
    pip install pyserial

The protocol is intentionally implemented directly rather than driving the STK
GUI, so agents and scripts can use it non-interactively.
"""

from __future__ import annotations

import argparse
import pathlib
import struct
import sys
import time
import zipfile
from dataclasses import dataclass

try:
    import serial
except ImportError:  # pragma: no cover - user environment dependency
    serial = None


STK_ZIP_DEFAULT = pathlib.Path(__file__).with_name("STK_0.2.3.zip")
STK_EXE_NAME_FRAGMENT = "8203R"

# Target profile recovered from STK UI/config parsing.
PROFILE_NAME = "8202 Non Share Mode"
PROFILE_INDEX = 2
SDRAM_BUS_BITS = 16
SDRAM_BUS_INDEX = 0

BAUD_DIVISORS = {
    57600: 0x74,
    115200: 0x3A,
    230400: 0x1D,
}

# Boot-ROM UART/system registers used by STK.
UART_CONTROL = 0x1FFE8918
UART_DIVISOR = 0x1FFE8914

TARGET_INIT_WRITES = (
    (0x1FFE8070, 0x581F),
    (0x1FFE8010, 0xFFFF),
    (0x1FFE8014, 0x0010),
    (0x1FFE8018, 0x0006),
    (0x1FFE8300, 0x013D),
    (0x1FFE8304, 0x19A7),
    (0x1FFE8308, 0x0033),
    (0x1FFE8310, 0x0001),
    (0x1FFE8330, 0x34C3),
    (0x1FFE8314, 0x0541),
    (0x1FFE830C, 0x0001),
    (0x1FFE834C, 0x1AB7),
)

STUB_LOAD_ADDRESS = 0x00019000
STUB_ENTRY_VIRTUAL = 0x80019000

# For target profile index 2, STK uses this embedded stub.
STK_TARGET_STUB_VA = 0x004E4960
STK_TARGET_STUB_SIZE = 0x2878

# The stock executable contains the write/upgrade version of the stub.
# ReadFirmwareViaRomLoader patches these bytes before uploading it.
READ_STUB_PATCHES_U32 = {
    0x004E5E44: 0x08006DC0,
    0x004E5FBC: 0x080069C7,
    0x004E60D0: 0x08006DC0,
    0x004E7140: 0x8C920000,
}
READ_STUB_PATCHES_U8 = {
    0x004E648D: 0x0A,
    0x004E648E: 0x00,
}

# Vendor RAM-stub header/control area.
STUB_META_WRITES = (
    (0x00018FFC, 0),
    (0x00018FF8, 0),
    (0x00018FF4, 0),
    (0x00018FF0, 0),
    (0x00018FEC, 0),  # profile index 2 maps to loader mode 0
    (0x00018FE8, 0xE100),
)

MAX_READBACK_SIZE = 0x200000


class RomLoaderError(RuntimeError):
    pass


@dataclass(frozen=True)
class PeSection:
    virtual_address: int
    virtual_size: int
    raw_offset: int
    raw_size: int


class PeImage:
    """Minimal PE32 reader sufficient for extracting the embedded STK stub."""

    def __init__(self, data: bytes):
        self.data = data
        if data[:2] != b"MZ":
            raise RomLoaderError("STK executable is not an MZ/PE image")
        pe_off = struct.unpack_from("<I", data, 0x3C)[0]
        if data[pe_off : pe_off + 4] != b"PE\0\0":
            raise RomLoaderError("PE signature not found")

        coff = pe_off + 4
        self.section_count = struct.unpack_from("<H", data, coff + 2)[0]
        opt_size = struct.unpack_from("<H", data, coff + 16)[0]
        opt = coff + 20
        magic = struct.unpack_from("<H", data, opt)[0]
        if magic != 0x10B:
            raise RomLoaderError(f"expected PE32 optional header, got 0x{magic:x}")
        self.image_base = struct.unpack_from("<I", data, opt + 28)[0]

        sec_off = opt + opt_size
        sections: list[PeSection] = []
        for i in range(self.section_count):
            p = sec_off + i * 40
            virtual_size = struct.unpack_from("<I", data, p + 8)[0]
            virtual_address = struct.unpack_from("<I", data, p + 12)[0]
            raw_size = struct.unpack_from("<I", data, p + 16)[0]
            raw_offset = struct.unpack_from("<I", data, p + 20)[0]
            sections.append(
                PeSection(
                    virtual_address=virtual_address,
                    virtual_size=virtual_size,
                    raw_offset=raw_offset,
                    raw_size=raw_size,
                )
            )
        self.sections = tuple(sections)

    def va_to_offset(self, va: int) -> int:
        rva = va - self.image_base
        for sec in self.sections:
            span = max(sec.virtual_size, sec.raw_size)
            if sec.virtual_address <= rva < sec.virtual_address + span:
                delta = rva - sec.virtual_address
                if delta >= sec.raw_size:
                    raise RomLoaderError(
                        f"VA 0x{va:08x} lies in zero-filled PE section tail"
                    )
                return sec.raw_offset + delta
        raise RomLoaderError(f"VA 0x{va:08x} is outside PE sections")

    def read_va(self, va: int, size: int) -> bytes:
        off = self.va_to_offset(va)
        out = self.data[off : off + size]
        if len(out) != size:
            raise RomLoaderError("truncated PE data")
        return out


def load_stk_executable(stk_zip: pathlib.Path) -> bytes:
    with zipfile.ZipFile(stk_zip, "r") as zf:
        names = [
            name
            for name in zf.namelist()
            if STK_EXE_NAME_FRAGMENT.lower() in name.lower()
            and name.lower().endswith(".exe")
        ]
        if len(names) != 1:
            raise RomLoaderError(
                f"expected one rev-8203R executable in {stk_zip}, found {names}"
            )
        return zf.read(names[0])


def build_target_read_stub(stk_zip: pathlib.Path) -> bytes:
    pe = PeImage(load_stk_executable(stk_zip))
    stub = bytearray(pe.read_va(STK_TARGET_STUB_VA, STK_TARGET_STUB_SIZE))

    for va, value in READ_STUB_PATCHES_U32.items():
        rel = va - STK_TARGET_STUB_VA
        if not (0 <= rel <= len(stub) - 4):
            raise RomLoaderError(f"read-stub patch 0x{va:08x} outside stub")
        struct.pack_into("<I", stub, rel, value)

    for va, value in READ_STUB_PATCHES_U8.items():
        rel = va - STK_TARGET_STUB_VA
        if not (0 <= rel < len(stub)):
            raise RomLoaderError(f"read-stub byte patch 0x{va:08x} outside stub")
        stub[rel] = value

    return bytes(stub)


class RomLoader:
    def __init__(self, port: str, baud: int):
        if serial is None:
            raise RomLoaderError(
                "pyserial is required; install it with: pip install pyserial"
            )
        if baud not in BAUD_DIVISORS:
            raise RomLoaderError(
                f"unsupported baud {baud}; choose {sorted(BAUD_DIVISORS)}"
            )
        self.port = port
        self.baud = baud
        self.ser = serial.Serial(
            port=port,
            baudrate=baud,
            bytesize=8,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.6,
            write_timeout=1.0,
        )
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()

    def close(self) -> None:
        self.ser.close()

    def __enter__(self) -> "RomLoader":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def read_exact(self, size: int) -> bytes:
        # Approximate the STK COMMTIMEOUTS contract:
        # 100 ms per requested byte + 500 ms constant.
        deadline = time.monotonic() + 0.5 + 0.1 * size
        out = bytearray()
        while len(out) < size:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RomLoaderError(
                    f"serial read timeout: wanted {size}, got {len(out)}"
                )
            self.ser.timeout = min(remaining, 0.25)
            chunk = self.ser.read(size - len(out))
            if chunk:
                out += chunk
        return bytes(out)

    def write_exact(self, data: bytes) -> None:
        n = self.ser.write(data)
        if n != len(data):
            raise RomLoaderError(f"short serial write: {n}/{len(data)}")
        self.ser.flush()

    def echo(self, value: int) -> None:
        b = bytes((value,))
        self.write_exact(b)
        got = self.read_exact(1)
        if got != b:
            raise RomLoaderError(
                f"echo mismatch for 0x{value:02x}: got {got.hex()}"
            )

    def write32(self, address: int, value: int) -> None:
        pkt = b"W" + struct.pack("<II", address & 0xFFFFFFFF, value & 0xFFFFFFFF)
        self.write_exact(pkt)
        ack = self.read_exact(1)
        if ack != b"W":
            raise RomLoaderError(
                f"W32 0x{address:08x} ack mismatch: {ack.hex()}"
            )

    def read32(self, address: int) -> int:
        pkt = b"R" + struct.pack("<I", address & 0xFFFFFFFF)
        self.write_exact(pkt)
        reply = self.read_exact(5)
        if reply[:1] != b"R":
            raise RomLoaderError(
                f"R32 0x{address:08x} reply mismatch: {reply.hex()}"
            )
        return struct.unpack_from("<I", reply, 1)[0]

    def stream_words(self, data: bytes) -> None:
        if len(data) % 4:
            raise RomLoaderError("word stream length must be a multiple of 4")
        for off in range(0, len(data), 4):
            self.write_exact(b"w" + data[off : off + 4])
            ack = self.read_exact(1)
            if ack != b"w":
                raise RomLoaderError(
                    f"word-stream ack mismatch at +0x{off:x}: {ack.hex()}"
                )

    def synchronize_target(self) -> None:
        # Initial A/A echo acts as the ROM-loader synchronization/autobaud edge.
        self.echo(ord("A"))

        self.write32(UART_CONTROL, 0)
        self.write32(UART_DIVISOR, BAUD_DIVISORS[self.baud])

        for address, value in TARGET_INIT_WRITES:
            self.write32(address, value)

        self.echo(ord("C"))

    def upload_stub(self, stub: bytes) -> None:
        if len(stub) < 4 or len(stub) % 4:
            raise RomLoaderError("stub must be non-empty and dword aligned")
        for address, value in STUB_META_WRITES:
            self.write32(address, value)
        self.write32(STUB_LOAD_ADDRESS, struct.unpack_from("<I", stub, 0)[0])
        self.stream_words(stub[4:])

    @staticmethod
    def encode_jump(target_virtual: int) -> int:
        if target_virtual & 3:
            raise RomLoaderError("jump target must be 4-byte aligned")
        return 0x08000000 | ((target_virtual >> 2) & 0x03FFFFFF)

    def start_uploaded_code(self, target_virtual: int = STUB_ENTRY_VIRTUAL) -> None:
        self.echo(ord("S"))
        self.write32(0x00000000, self.encode_jump(target_virtual))
        self.write32(0x00000004, 0)
        self.write32(0x00000008, 0)

        # STK reads this register before modifying it but does not use the
        # returned value in the subsequent decision path.
        self.read32(0x1FFE8048)
        self.write32(0x1FFE8048, 0x203F)
        self.write32(0x1FFE8008, 0)

    def monitor_console(self, timeout: float) -> tuple[bytes, bool]:
        """
        Mirror the STK RAM-stub console contract.

        Printable bytes are text; CR ends a line; NUL is completion.
        Returns (raw_bytes_without_nul, completed).
        """
        deadline = time.monotonic() + timeout
        raw = bytearray()
        while time.monotonic() < deadline:
            self.ser.timeout = min(0.25, max(0.01, deadline - time.monotonic()))
            b = self.ser.read(1)
            if not b:
                continue
            if b == b"\x00":
                return bytes(raw), True
            raw += b
            if 0x20 <= b[0] <= 0x7A:
                sys.stdout.write(chr(b[0]))
                sys.stdout.flush()
            elif b == b"\r":
                sys.stdout.write("\n")
                sys.stdout.flush()
        return bytes(raw), False

    def receive_firmware_from_stub(self) -> bytes:
        # STK first waits for the read-stub's ASCII/NUL completion marker.
        _, completed = self.monitor_console(5.0)
        if not completed:
            raise RomLoaderError("read-stub did not emit completion NUL")

        size_raw = self.read_exact(4)
        size = struct.unpack("<I", size_raw)[0]
        if size > MAX_READBACK_SIZE:
            raise RomLoaderError(
                f"stub reported 0x{size:x} bytes, above STK limit 0x{MAX_READBACK_SIZE:x}"
            )
        if size == 0:
            return b""
        if size % 16:
            raise RomLoaderError(
                f"stub reported non-16-byte-aligned size 0x{size:x}; "
                "STK's recovered receive loop always reads 16-byte blocks"
            )

        # STK echoes the first byte of the received size field.
        self.write_exact(size_raw[:1])

        out = bytearray()
        while len(out) < size:
            block = self.read_exact(16)
            out += block
            # The RAM stub uses the first byte of the block as its ACK token.
            self.write_exact(block[:1])
        return bytes(out)


def parse_int(text: str) -> int:
    return int(text, 0)


def add_serial_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--port", required=True)
    p.add_argument(
        "--baud",
        type=int,
        choices=sorted(BAUD_DIVISORS),
        default=115200,
    )


def command_profile(_: argparse.Namespace) -> int:
    print(f"profile={PROFILE_NAME}")
    print(f"profile_index={PROFILE_INDEX}")
    print(f"sdram_bus_bits={SDRAM_BUS_BITS}")
    print(f"sdram_bus_index={SDRAM_BUS_INDEX}")
    print("baud_rates=" + ",".join(map(str, sorted(BAUD_DIVISORS))))
    print(f"stub_load_address=0x{STUB_LOAD_ADDRESS:08x}")
    print(f"stub_entry_virtual=0x{STUB_ENTRY_VIRTUAL:08x}")
    return 0


def command_probe(args: argparse.Namespace) -> int:
    with RomLoader(args.port, args.baud) as rl:
        rl.synchronize_target()
        print(
            f"connected port={args.port} baud={args.baud} "
            f"profile={PROFILE_NAME!r} bus={SDRAM_BUS_BITS}"
        )
    return 0


def command_read32(args: argparse.Namespace) -> int:
    with RomLoader(args.port, args.baud) as rl:
        rl.synchronize_target()
        value = rl.read32(args.address)
        print(f"0x{args.address:08x}: 0x{value:08x}")
    return 0


def command_write32(args: argparse.Namespace) -> int:
    if not args.allow_write:
        raise RomLoaderError(
            "write32 is disabled by default; pass --allow-write explicitly"
        )
    with RomLoader(args.port, args.baud) as rl:
        rl.synchronize_target()
        rl.write32(args.address, args.value)
        print(f"W32 0x{args.address:08x} <- 0x{args.value:08x}")
    return 0


def command_extract_read_stub(args: argparse.Namespace) -> int:
    stub = build_target_read_stub(args.stk_zip)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(stub)
    print(f"output={args.output}")
    print(f"size=0x{len(stub):x}")
    return 0


def command_read_firmware(args: argparse.Namespace) -> int:
    stub = build_target_read_stub(args.stk_zip)
    with RomLoader(args.port, args.baud) as rl:
        rl.synchronize_target()
        rl.upload_stub(stub)
        rl.start_uploaded_code()
        data = rl.receive_firmware_from_stub()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    print(f"read_size=0x{len(data):x}")
    print(f"output={args.output}")
    return 0


def command_run_ram(args: argparse.Namespace) -> int:
    image = args.image.read_bytes()
    if len(image) % 4:
        raise RomLoaderError("RAM image must be dword aligned")
    if args.address != STUB_LOAD_ADDRESS:
        raise RomLoaderError(
            "current recovered lowercase-w stream is validated only for "
            f"load base 0x{STUB_LOAD_ADDRESS:x}"
        )

    with RomLoader(args.port, args.baud) as rl:
        rl.synchronize_target()
        # Reuse only the upload framing, not the vendor flash stub.
        for address, value in STUB_META_WRITES:
            rl.write32(address, value)
        rl.write32(args.address, struct.unpack_from("<I", image, 0)[0])
        rl.stream_words(image[4:])
        rl.start_uploaded_code(0x80000000 | args.address)
        _, completed = rl.monitor_console(args.console_timeout)
        print(f"completion_marker={int(completed)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)

    profile_p = sub.add_parser("profile")
    profile_p.set_defaults(func=command_profile)

    probe_p = sub.add_parser("probe")
    add_serial_args(probe_p)
    probe_p.set_defaults(func=command_probe)

    read32_p = sub.add_parser("read32")
    add_serial_args(read32_p)
    read32_p.add_argument("address", type=parse_int)
    read32_p.set_defaults(func=command_read32)

    write32_p = sub.add_parser("write32")
    add_serial_args(write32_p)
    write32_p.add_argument("address", type=parse_int)
    write32_p.add_argument("value", type=parse_int)
    write32_p.add_argument("--allow-write", action="store_true")
    write32_p.set_defaults(func=command_write32)

    stub_p = sub.add_parser("extract-read-stub")
    stub_p.add_argument("--stk-zip", type=pathlib.Path, default=STK_ZIP_DEFAULT)
    stub_p.add_argument("-o", "--output", type=pathlib.Path, required=True)
    stub_p.set_defaults(func=command_extract_read_stub)

    read_fw_p = sub.add_parser("read-firmware")
    add_serial_args(read_fw_p)
    read_fw_p.add_argument("--stk-zip", type=pathlib.Path, default=STK_ZIP_DEFAULT)
    read_fw_p.add_argument("-o", "--output", type=pathlib.Path, required=True)
    read_fw_p.set_defaults(func=command_read_firmware)

    ram_p = sub.add_parser("run-ram")
    add_serial_args(ram_p)
    ram_p.add_argument("image", type=pathlib.Path)
    ram_p.add_argument(
        "--address",
        type=parse_int,
        default=STUB_LOAD_ADDRESS,
    )
    ram_p.add_argument("--console-timeout", type=float, default=10.0)
    ram_p.set_defaults(func=command_run_ram)

    args = p.parse_args(argv)
    try:
        return args.func(args)
    except (OSError, RomLoaderError, zipfile.BadZipFile) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
