#!/usr/bin/env python3
"""Headless Sunplus SPHE8202R ROM-loader client recovered from STK rev-8203R.

The implementation is intentionally target-first.  The currently supported
hardware profile is the HD Audio Rush SPHE8202R board configuration used by
the recovered STK path: 8202 non-shared SDRAM, 16-bit bus.

Validation levels:
- packet formats and state transitions are implementation-proven from STK;
- the target readback RAM-stub behavior is implementation-proven;
- no serial command in this file is claimed board-proven until exercised on
  the physical unit;
- flash write is gated explicitly because it is destructive.

The tool does not embed the vendor RAM stub.  Supply the recovered 10360-byte
profile stub with --stub.  Read mode patches a private in-memory copy of that
stub to the readback route before upload.
"""

from __future__ import annotations

import argparse
import dataclasses
import pathlib
import struct
import sys
import time
from typing import Protocol, Sequence


class RomLoaderError(RuntimeError):
    pass


BAUD_DIVISORS = {
    57600: 0x74,
    115200: 0x3A,
    230400: 0x1D,
}

TARGET_STUB_SIZE = 0x2878
MAX_READBACK_SIZE = 0x200000

# Target STK profile: "8202 Non Share Mode" + "16 bits".
TARGET_PROFILE_INDEX = 2
TARGET_BUS_WIDTH = 16

# The target profile uses the 0x2878-byte embedded stub.  STK rewrites these
# locations before read mode.  Values are exact bytes written by rev-8203R.
READ_STUB_PATCHES: tuple[tuple[int, bytes], ...] = (
    (0x14E4, bytes.fromhex("c06d0008")),
    (0x165C, bytes.fromhex("c7690008")),
    (0x1770, bytes.fromhex("c06d0008")),
    (0x1B2D, b"\x0a\x00"),
    (0x27E0, bytes.fromhex("0000928c")),
)

# Boot-ROM register writes for the target profile.  These are applied after
# the baud divisor writes and before the 'C' phase of the handshake.
TARGET_SYSTEM_WRITES: tuple[tuple[int, int], ...] = (
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

# ROM-loader workspace used by the uploaded stub.
WORK_ABORT = 0x18FFC
WORK_1 = 0x18FF8
WORK_2 = 0x18FF4
WORK_3 = 0x18FF0
WORK_PROFILE = 0x18FEC
WORK_UART = 0x18FE8
STUB_BASE = 0x19000
FIRMWARE_SIZE_WORD = 0x1DFFC
FIRMWARE_BASE = 0x1E000

# Start/execute sequence used after the RAM stub is present.
START_VECTOR_VALUE = 0x08006400
SYSTEM_CONTROL_READ = 0x1FFE8048
SYSTEM_CONTROL_RUN = 0x1FFE8008
SYSTEM_CONTROL_VALUE = 0x203F


class Transport(Protocol):
    def write(self, data: bytes) -> None: ...
    def read_exact(self, size: int, timeout: float | None = None) -> bytes: ...
    def close(self) -> None: ...


class SerialTransport:
    def __init__(self, port: str, baud: int, timeout: float) -> None:
        try:
            import serial  # type: ignore
        except ImportError as exc:
            raise RomLoaderError(
                "pyserial is required for hardware access; install it with "
                "'python -m pip install pyserial'"
            ) from exc

        try:
            self._serial = serial.Serial(
                port=port,
                baudrate=baud,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=min(timeout, 0.25),
                write_timeout=timeout,
            )
        except Exception as exc:
            raise RomLoaderError(f"cannot open serial port {port!r}: {exc}") from exc
        self._default_timeout = timeout
        try:
            self._serial.reset_input_buffer()
            self._serial.reset_output_buffer()
        except Exception:
            pass

    def write(self, data: bytes) -> None:
        try:
            written = self._serial.write(data)
            self._serial.flush()
        except Exception as exc:
            raise RomLoaderError(f"serial write failed: {exc}") from exc
        if written != len(data):
            raise RomLoaderError(
                f"short serial write: expected {len(data)}, wrote {written}"
            )

    def read_exact(self, size: int, timeout: float | None = None) -> bytes:
        if size < 0:
            raise ValueError(size)
        deadline = time.monotonic() + (
            self._default_timeout if timeout is None else timeout
        )
        out = bytearray()
        while len(out) < size:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RomLoaderError(
                    f"serial read timeout: wanted {size}, received {len(out)}"
                )
            self._serial.timeout = min(remaining, 0.25)
            try:
                chunk = self._serial.read(size - len(out))
            except Exception as exc:
                raise RomLoaderError(f"serial read failed: {exc}") from exc
            if chunk:
                out += chunk
        return bytes(out)

    def close(self) -> None:
        self._serial.close()


@dataclasses.dataclass
class ScriptedTransport:
    """Tiny deterministic transport used only by selftest."""

    reads: bytearray
    writes: list[bytes] = dataclasses.field(default_factory=list)

    def write(self, data: bytes) -> None:
        self.writes.append(bytes(data))

    def read_exact(self, size: int, timeout: float | None = None) -> bytes:
        del timeout
        if len(self.reads) < size:
            raise RomLoaderError("selftest scripted transport underflow")
        out = bytes(self.reads[:size])
        del self.reads[:size]
        return out

    def close(self) -> None:
        return


def u32le(data: bytes | bytearray, off: int = 0) -> int:
    if off < 0 or off + 4 > len(data):
        raise RomLoaderError("32-bit value outside buffer")
    return struct.unpack_from("<I", data, off)[0]


def p32(value: int) -> bytes:
    return struct.pack("<I", value & 0xFFFFFFFF)


def expect_byte(actual: bytes, expected: int, context: str) -> None:
    if actual != bytes((expected,)):
        raise RomLoaderError(
            f"{context}: expected {bytes((expected,))!r}, received {actual!r}"
        )


def patch_target_read_stub(stub: bytes) -> bytes:
    if len(stub) != TARGET_STUB_SIZE:
        raise RomLoaderError(
            f"target stub must be exactly {TARGET_STUB_SIZE} bytes, "
            f"got {len(stub)}"
        )
    out = bytearray(stub)
    for off, value in READ_STUB_PATCHES:
        out[off : off + len(value)] = value
    return bytes(out)


class RomLoaderClient:
    def __init__(
        self,
        transport: Transport,
        baud: int = 115200,
        verbose: bool = False,
    ) -> None:
        if baud not in BAUD_DIVISORS:
            raise RomLoaderError(
                f"unsupported baud {baud}; choose one of {sorted(BAUD_DIVISORS)}"
            )
        self.io = transport
        self.baud = baud
        self.verbose = verbose

    def log(self, message: str) -> None:
        if self.verbose:
            print(message, file=sys.stderr)

    def _exchange_echo(self, value: int, context: str) -> None:
        packet = bytes((value,))
        self.io.write(packet)
        expect_byte(self.io.read_exact(1), value, context)

    def write32(self, address: int, value: int) -> None:
        packet = b"W" + p32(address) + p32(value)
        self.io.write(packet)
        expect_byte(self.io.read_exact(1), ord("W"), "write32")

    def read32(self, address: int) -> int:
        self.io.write(b"R" + p32(address))
        reply = self.io.read_exact(5)
        if reply[:1] != b"R":
            raise RomLoaderError(f"read32: invalid reply {reply!r}")
        return u32le(reply, 1)

    def _configure_uart_divisor(self) -> None:
        self.write32(0x1FFE8918, 0)
        self.write32(0x1FFE8914, BAUD_DIVISORS[self.baud])

    def _initialize_target_system(self) -> None:
        for address, value in TARGET_SYSTEM_WRITES:
            self.write32(address, value)

    def _initialize_stub_workspace(self, first_word: int) -> None:
        self.write32(WORK_ABORT, 0)
        self.write32(WORK_1, 0)
        self.write32(WORK_2, 0)
        self.write32(WORK_3, 0)
        self.write32(WORK_PROFILE, 0)
        self.write32(WORK_UART, 0xE100)
        self.write32(STUB_BASE, first_word)

    def connect_and_upload_stub(self, stub: bytes) -> None:
        if len(stub) < 4 or len(stub) % 4:
            raise RomLoaderError("RAM stub size must be a non-zero multiple of 4")

        self.log("ROM sync")
        self._exchange_echo(ord("A"), "ROM sync A")
        self._configure_uart_divisor()
        self._initialize_target_system()
        self._exchange_echo(ord("C"), "ROM sync C")
        self._initialize_stub_workspace(u32le(stub, 0))

        self.log(f"uploading RAM stub: {len(stub)} bytes")
        for off in range(4, len(stub), 4):
            self.io.write(b"w" + stub[off : off + 4])
            expect_byte(self.io.read_exact(1), ord("w"), "RAM stub upload")

    def start_uploaded_code(self) -> int:
        self._exchange_echo(ord("S"), "start S")

        self.io.write(b"W" + p32(0) + p32(START_VECTOR_VALUE))
        reply = self.io.read_exact(3)
        if reply[2:3] != b"W":
            raise RomLoaderError(f"start vector reply is invalid: {reply!r}")

        self.write32(4, 0)
        self.write32(8, 0)
        control_before = self.read32(SYSTEM_CONTROL_READ)
        self.write32(SYSTEM_CONTROL_READ, SYSTEM_CONTROL_VALUE)
        self.write32(SYSTEM_CONTROL_RUN, 0)
        return control_before

    def upload_firmware_image(self, image: bytes) -> None:
        if len(image) < 4 or len(image) % 4:
            raise RomLoaderError("firmware upload size must be a multiple of 4")
        self._exchange_echo(ord("C"), "firmware upload C")
        self.write32(FIRMWARE_SIZE_WORD, len(image))
        self.write32(FIRMWARE_BASE, u32le(image, 0))
        for off in range(4, len(image), 4):
            self.io.write(b"w" + image[off : off + 4])
            expect_byte(self.io.read_exact(1), ord("w"), "firmware upload")

    def wait_status_until_nul(self, timeout: float) -> bytes:
        deadline = time.monotonic() + timeout
        out = bytearray()
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RomLoaderError("status terminator timeout")
            value = self.io.read_exact(1, timeout=remaining)[0]
            if value == 0:
                return bytes(out)
            out.append(value)
            if self.verbose and (value == 0x0D or 0x20 <= value <= 0x7E):
                if value == 0x0D:
                    print(file=sys.stderr)
                else:
                    print(chr(value), end="", file=sys.stderr, flush=True)

    def receive_firmware_readback(self) -> bytes:
        self.wait_status_until_nul(5.0)
        size = u32le(self.io.read_exact(4))
        if size > MAX_READBACK_SIZE:
            raise RomLoaderError(
                f"RAM stub announced oversized readback: {size} bytes"
            )
        self.log(f"readback size: {size} bytes")

        self.io.write(b"\x00")
        out = bytearray()
        while len(out) < size:
            count = min(16, size - len(out))
            out += self.io.read_exact(count)
            self.io.write(b"\x00")
        return bytes(out)

    def read_flash(self, stub: bytes) -> bytes:
        read_stub = patch_target_read_stub(stub)
        self.connect_and_upload_stub(read_stub)
        control_before = self.start_uploaded_code()
        self.log(f"pre-run control value: 0x{control_before:08x}")
        return self.receive_firmware_readback()

    def write_flash(self, stub: bytes, image: bytes) -> bytes:
        self.connect_and_upload_stub(stub)
        self.upload_firmware_image(image)
        control_before = self.start_uploaded_code()
        self.log(f"pre-run control value: 0x{control_before:08x}")
        return self.wait_status_until_nul(30.0)


def open_client(args: argparse.Namespace) -> RomLoaderClient:
    io = SerialTransport(args.port, args.baud, args.io_timeout)
    return RomLoaderClient(io, baud=args.baud, verbose=args.verbose)


def command_probe(args: argparse.Namespace) -> int:
    client = open_client(args)
    try:
        client._exchange_echo(ord("A"), "ROM sync A")
        print("rom_sync=ok")
        return 0
    finally:
        client.io.close()


def command_patch_read_stub(args: argparse.Namespace) -> int:
    stub = args.stub.read_bytes()
    patched = patch_target_read_stub(stub)
    args.output.write_bytes(patched)
    print(f"output={args.output}")
    print(f"size={len(patched)}")
    return 0


def command_read_flash(args: argparse.Namespace) -> int:
    stub = args.stub.read_bytes()
    client = open_client(args)
    try:
        data = client.read_flash(stub)
    finally:
        client.io.close()
    args.output.write_bytes(data)
    print(f"output={args.output}")
    print(f"size={len(data)}")
    print("status=SERIAL_READBACK_COMPLETED")
    return 0


def command_write_flash(args: argparse.Namespace) -> int:
    if not args.i_understand_this_erases_flash:
        raise RomLoaderError(
            "write-flash is destructive; repeat with "
            "--i-understand-this-erases-flash after recovery is proven"
        )
    stub = args.stub.read_bytes()
    image = args.image.read_bytes()
    client = open_client(args)
    try:
        status = client.write_flash(stub, image)
    finally:
        client.io.close()
    if status:
        print(status.decode("ascii", "replace"), file=sys.stderr)
    print("status=SERIAL_FLASH_WRITE_COMPLETED")
    return 0


def command_selftest(_: argparse.Namespace) -> int:
    stub = bytes(TARGET_STUB_SIZE)
    patched = patch_target_read_stub(stub)
    for off, value in READ_STUB_PATCHES:
        if patched[off : off + len(value)] != value:
            raise RomLoaderError("read-stub patch selftest failed")

    io = ScriptedTransport(bytearray(b"W"))
    client = RomLoaderClient(io)
    client.write32(0x11223344, 0xAABBCCDD)
    if io.writes != [b"W\x44\x33\x22\x11\xdd\xcc\xbb\xaa"]:
        raise RomLoaderError("write32 packet selftest failed")

    payload = bytes(range(32))
    scripted = bytearray(b"\x00" + p32(len(payload)) + payload)
    io2 = ScriptedTransport(scripted)
    client2 = RomLoaderClient(io2)
    got = client2.receive_firmware_readback()
    if got != payload:
        raise RomLoaderError("readback payload selftest failed")
    if io2.writes != [b"\x00", b"\x00", b"\x00"]:
        raise RomLoaderError("readback ACK selftest failed")

    print("selftest=ok")
    return 0


def add_serial_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--port", required=True)
    p.add_argument("--baud", type=int, choices=sorted(BAUD_DIVISORS), default=115200)
    p.add_argument("--io-timeout", type=float, default=1.0)
    p.add_argument("--verbose", action="store_true")


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)

    selftest_p = sub.add_parser("selftest")
    selftest_p.set_defaults(handler=command_selftest)

    patch_p = sub.add_parser("patch-read-stub")
    patch_p.add_argument("stub", type=pathlib.Path)
    patch_p.add_argument("-o", "--output", type=pathlib.Path, required=True)
    patch_p.set_defaults(handler=command_patch_read_stub)

    probe_p = sub.add_parser("probe")
    add_serial_args(probe_p)
    probe_p.set_defaults(handler=command_probe)

    read_p = sub.add_parser("read-flash")
    add_serial_args(read_p)
    read_p.add_argument("--stub", type=pathlib.Path, required=True)
    read_p.add_argument("-o", "--output", type=pathlib.Path, required=True)
    read_p.set_defaults(handler=command_read_flash)

    write_p = sub.add_parser("write-flash")
    add_serial_args(write_p)
    write_p.add_argument("--stub", type=pathlib.Path, required=True)
    write_p.add_argument("--image", type=pathlib.Path, required=True)
    write_p.add_argument(
        "--i-understand-this-erases-flash",
        action="store_true",
        help="required destructive-operation acknowledgement",
    )
    write_p.set_defaults(handler=command_write_flash)

    args = p.parse_args(argv)
    try:
        return int(args.handler(args))
    except (OSError, RomLoaderError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
