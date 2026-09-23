#!/usr/bin/env python3
"""
Headless UART ROM-loader client for the target SPHE8202R board.

STATUS:
- protocol recovered from STK 0.2.3 rev-8203R;
- target profile implemented: 8202 Non Share Mode, 16-bit;
- default commands are RAM/session operations only;
- flash-affecting execution is deliberately not exposed yet.

Requires: pyserial

Recovered target UART:
- 8N1
- 57600 / 115200 / 230400
- single-byte command echo/ack protocol
- memory write: b'W' + <addr:u32le> + <value:u32le>, ack b'W'
- memory read:  b'R' + <addr:u32le>, response b'R' + <value:u32le>
"""

from __future__ import annotations

import argparse
import pathlib
import struct
import sys
import time
import zipfile

try:
    import serial
except ImportError as exc:
    raise SystemExit("pyserial is required: pip install pyserial") from exc


BAUD_DIVISOR = {
    57600: 0x74,
    115200: 0x3A,
    230400: 0x1D,
}

TARGET_PROFILE_INDEX = 2
TARGET_PROFILE_NAME = "8202 Non Share Mode"
TARGET_SDRAM_WIDTH = 16

# rev-8203R embedded RAM-loader used by target profile 2.
STK_EXE_MEMBER = "STK Sunplus Tool Kit 0.2.3 (rev 8203R) English.exe"
TARGET_STUB_VA = 0x004E4960
TARGET_STUB_SIZE = 0x2878

RAM_STUB_ADDRESS = 0x00019000
IMAGE_SIZE_ADDRESS = 0x0001DFFC
IMAGE_ADDRESS = 0x0001E000


class ProtocolError(RuntimeError):
    pass


def u32le(data: bytes) -> int:
    if len(data) != 4:
        raise ValueError("u32le requires exactly four bytes")
    return struct.unpack("<I", data)[0]


def p32(value: int) -> bytes:
    return struct.pack("<I", value & 0xFFFFFFFF)


def pe_va_to_file_offset(exe: bytes, va: int) -> int:
    if exe[:2] != b"MZ":
        raise ProtocolError("STK executable is not a PE image")
    pe = struct.unpack_from("<I", exe, 0x3C)[0]
    if exe[pe:pe + 4] != b"PE\0\0":
        raise ProtocolError("invalid PE signature")

    num_sections = struct.unpack_from("<H", exe, pe + 6)[0]
    opt_size = struct.unpack_from("<H", exe, pe + 20)[0]
    opt = pe + 24
    magic = struct.unpack_from("<H", exe, opt)[0]
    if magic != 0x10B:
        raise ProtocolError(f"expected PE32, got optional-header magic 0x{magic:x}")
    image_base = struct.unpack_from("<I", exe, opt + 28)[0]
    rva = va - image_base

    sec = opt + opt_size
    for _ in range(num_sections):
        virtual_size = struct.unpack_from("<I", exe, sec + 8)[0]
        virtual_addr = struct.unpack_from("<I", exe, sec + 12)[0]
        raw_size = struct.unpack_from("<I", exe, sec + 16)[0]
        raw_ptr = struct.unpack_from("<I", exe, sec + 20)[0]
        span = max(virtual_size, raw_size)
        if virtual_addr <= rva < virtual_addr + span:
            return raw_ptr + (rva - virtual_addr)
        sec += 40
    raise ProtocolError(f"VA 0x{va:08x} is outside PE sections")


def extract_target_stub(stk_zip: pathlib.Path) -> bytes:
    with zipfile.ZipFile(stk_zip, "r") as zf:
        names = zf.namelist()
        member = next(
            (name for name in names if name.endswith(STK_EXE_MEMBER)),
            None,
        )
        if member is None:
            raise ProtocolError(
                f"{STK_EXE_MEMBER!r} not found in {stk_zip}"
            )
        exe = zf.read(member)

    off = pe_va_to_file_offset(exe, TARGET_STUB_VA)
    stub = exe[off:off + TARGET_STUB_SIZE]
    if len(stub) != TARGET_STUB_SIZE:
        raise ProtocolError("truncated embedded RAM-loader")
    # First word is target MIPS code: lui s6,0xbffe = 0x3c16bffe LE.
    if stub[:4] != bytes.fromhex("febf163c"):
        raise ProtocolError(
            "embedded RAM-loader signature mismatch; wrong STK revision?"
        )
    return stub


class RomLoader:
    def __init__(self, port: str, baud: int, timeout: float = 1.5):
        if baud not in BAUD_DIVISOR:
            raise ValueError(f"unsupported baud: {baud}")
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.ser: serial.Serial | None = None

    def __enter__(self) -> "RomLoader":
        self.ser = serial.Serial(
            self.port,
            self.baud,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=self.timeout,
            write_timeout=self.timeout,
        )
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.ser is not None:
            self.ser.close()
            self.ser = None

    def _serial(self) -> serial.Serial:
        if self.ser is None:
            raise ProtocolError("serial port is not open")
        return self.ser

    def write_exact(self, data: bytes) -> None:
        ser = self._serial()
        n = ser.write(data)
        ser.flush()
        if n != len(data):
            raise ProtocolError(f"short UART write: {n}/{len(data)}")

    def read_exact(self, n: int) -> bytes:
        ser = self._serial()
        data = ser.read(n)
        if len(data) != n:
            raise ProtocolError(f"UART timeout/short read: {len(data)}/{n}")
        return data

    def exchange_byte(self, value: int, expected: int | None = None) -> int:
        self.write_exact(bytes([value]))
        got = self.read_exact(1)[0]
        if expected is not None and got != expected:
            raise ProtocolError(
                f"unexpected ACK 0x{got:02x}, expected 0x{expected:02x}"
            )
        return got

    def write32(self, address: int, value: int) -> None:
        self.write_exact(b"W" + p32(address) + p32(value))
        ack = self.read_exact(1)
        if ack != b"W":
            raise ProtocolError(f"write32 ACK mismatch: {ack!r}")

    def read32(self, address: int) -> int:
        self.write_exact(b"R" + p32(address))
        reply = self.read_exact(5)
        if reply[:1] != b"R":
            raise ProtocolError(f"read32 ACK mismatch: {reply!r}")
        return u32le(reply[1:])

    def handshake(self) -> None:
        self.exchange_byte(ord("A"), ord("A"))

    def configure_baud_divisor(self) -> None:
        self.write32(0x1FFE8918, 0)
        self.write32(0x1FFE8914, BAUD_DIVISOR[self.baud])

    def configure_target_system(self) -> None:
        """8202 Non Share Mode + 16-bit, recovered from STK."""
        writes = (
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
        for address, value in writes:
            self.write32(address, value)

    def prepare_stub_upload(self) -> None:
        self.exchange_byte(ord("C"), ord("C"))
        for address in (0x18FFC, 0x18FF8, 0x18FF4, 0x18FF0):
            self.write32(address, 0)
        # Target system profile index 2 maps to zero here.
        self.write32(0x18FEC, 0)
        self.write32(0x18FE8, 0xE100)

    def stream_words(self, data: bytes, start_offset: int = 4) -> None:
        padded = data + b"\x00" * ((-len(data)) & 3)
        for off in range(start_offset, len(padded), 4):
            self.write_exact(b"w" + padded[off:off + 4])
            ack = self.read_exact(1)
            if ack != b"w":
                raise ProtocolError(
                    f"stream ACK mismatch at +0x{off:x}: {ack!r}"
                )

    def upload_stub(self, stub: bytes) -> None:
        if len(stub) < 4:
            raise ProtocolError("stub is too short")
        self.prepare_stub_upload()
        self.write32(RAM_STUB_ADDRESS, u32le(stub[:4]))
        self.stream_words(stub, 4)

    def initialize_session(self, stub: bytes) -> None:
        self.handshake()
        self.configure_baud_divisor()
        self.configure_target_system()
        self.upload_stub(stub)

    def upload_image_to_ram(self, image: bytes) -> None:
        """
        Transfer an image into the loader's image staging area without issuing
        the final S/system-switch sequence.
        """
        if len(image) < 4:
            raise ProtocolError("image must contain at least four bytes")
        self.exchange_byte(ord("C"), ord("C"))
        self.write32(IMAGE_SIZE_ADDRESS, len(image))
        self.write32(IMAGE_ADDRESS, u32le(image[:4]))
        self.stream_words(image, 4)

    def monitor(self, stop_on_nul: bool = False) -> None:
        ser = self._serial()
        while True:
            b = ser.read(1)
            if not b:
                continue
            if b == b"\x00" and stop_on_nul:
                return
            if b == b"\r":
                sys.stdout.write("\n")
            elif 0x20 <= b[0] <= 0x7E or b in (b"\n", b"\t"):
                sys.stdout.write(b.decode("ascii", "replace"))
            else:
                sys.stdout.write(f"<{b[0]:02x}>")
            sys.stdout.flush()


def add_serial_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--port", required=True)
    p.add_argument(
        "--baud",
        type=int,
        choices=sorted(BAUD_DIVISOR),
        default=115200,
    )
    p.add_argument("--timeout", type=float, default=1.5)
    p.add_argument(
        "--stk",
        type=pathlib.Path,
        default=pathlib.Path("tools/STK_0.2.3.zip"),
        help="STK archive used only as the source of the recovered RAM-loader",
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)

    info = sub.add_parser("info")
    info.add_argument(
        "--stk",
        type=pathlib.Path,
        default=pathlib.Path("tools/STK_0.2.3.zip"),
    )

    probe = sub.add_parser("probe")
    add_serial_args(probe)

    read32 = sub.add_parser("read32")
    add_serial_args(read32)
    read32.add_argument("address", type=lambda x: int(x, 0))

    write32 = sub.add_parser("write32")
    add_serial_args(write32)
    write32.add_argument("address", type=lambda x: int(x, 0))
    write32.add_argument("value", type=lambda x: int(x, 0))

    upload = sub.add_parser("upload-ram")
    add_serial_args(upload)
    upload.add_argument("image", type=pathlib.Path)

    mon = sub.add_parser("monitor")
    add_serial_args(mon)
    mon.add_argument("--stop-on-nul", action="store_true")

    args = ap.parse_args()

    if args.command == "info":
        stub = extract_target_stub(args.stk)
        print(f"profile_index={TARGET_PROFILE_INDEX}")
        print(f"profile={TARGET_PROFILE_NAME}")
        print(f"sdram_width={TARGET_SDRAM_WIDTH}")
        print(f"ram_stub_address=0x{RAM_STUB_ADDRESS:08x}")
        print(f"ram_stub_size=0x{len(stub):x}")
        print(f"ram_stub_first_word=0x{u32le(stub[:4]):08x}")
        return 0

    stub = extract_target_stub(args.stk)

    with RomLoader(args.port, args.baud, args.timeout) as rl:
        if args.command == "monitor":
            rl.monitor(args.stop_on_nul)
            return 0

        rl.initialize_session(stub)

        if args.command == "probe":
            print("ROM-loader session initialized; RAM stub uploaded")
            return 0
        if args.command == "read32":
            value = rl.read32(args.address)
            print(f"0x{args.address:08x}: 0x{value:08x}")
            return 0
        if args.command == "write32":
            rl.write32(args.address, args.value)
            print(
                f"wrote 0x{args.value & 0xffffffff:08x} "
                f"to 0x{args.address:08x}"
            )
            return 0
        if args.command == "upload-ram":
            image = args.image.read_bytes()
            rl.upload_image_to_ram(image)
            print(
                f"uploaded {len(image)} bytes into RAM staging area "
                f"at 0x{IMAGE_ADDRESS:08x}; image was NOT executed"
            )
            return 0

    raise AssertionError(args.command)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ProtocolError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
