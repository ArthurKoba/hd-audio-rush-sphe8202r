#!/usr/bin/env python3
"""
Headless UART ROM-loader client for the target SPHE8202R board.

STATUS:
- protocol recovered from STK 0.2.3 rev-8203R;
- target image SDRAM descriptor: 8202 Non Share Mode, 16-bit;\n- target RomLoader flash profile: 8202L_128_SPI (SPI helper mode 2);
- default commands are RAM/session operations only;
- generic modified-image flash writing is deliberately not exposed;
- stock-only recovery is gated by exact size/SHA and explicit chip-erase confirmation.

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
import hashlib
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

TARGET_PROFILE_INDEX = 7
TARGET_PROFILE_NAME = "8202L_128_SPI"
TARGET_IMAGE_SDRAM_PROFILE_INDEX = 2
TARGET_IMAGE_SDRAM_PROFILE_NAME = "8202 Non Share Mode"
TARGET_SDRAM_WIDTH = 16
TARGET_FLASH_MODE = 2
TARGET_FLASH_SIZE = 0x100000
TARGET_STOCK_SHA256 = "67d8301f043ecc4d725ec09e38f3c53dd7e71ec26192775811a6a05dd13b545e"

# rev-8203R common 0x2878 RAM-loader used by the target SPI profile.
STK_EXE_MEMBER = "STK Sunplus Tool Kit 0.2.3 (rev 8203R) English.exe"
STK_EXE_SHA256 = "e58d7d6f6f9cff67cbcf7f2b1191afbf0ffc2de4ca63c4dbda30c486c82dbc89"
TARGET_STUB_VA = 0x004E5960
TARGET_STUB_SIZE = 0x2878

RAM_STUB_ADDRESS = 0x00019000
RAM_EXEC_VA = 0x80019000
IMAGE_SIZE_ADDRESS = 0x0001DFFC
IMAGE_ADDRESS = 0x0001E000
RAM_EXEC_MAX_SIZE = IMAGE_SIZE_ADDRESS - RAM_STUB_ADDRESS


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


def patch_target_stub_for_read(stub: bytes) -> bytes:
    """
    Apply the exact rev-8203R read-firmware patches to the common target helper.

    Offsets are relative to embedded target stub VA 0x004E5960.
    """
    work = bytearray(stub)

    expected = {
        0x14E4: 0x0C006AFB,
        0x165C: 0x0C006AFB,
        0x1770: 0x0C006616,
        0x27E0: 0x0C006E06,
    }
    for off, value in expected.items():
        actual = u32le(work[off:off + 4])
        if actual != value:
            raise ProtocolError(
                f"canonical rev-8203R helper mismatch at +0x{off:x}: "
                f"0x{actual:08x} != 0x{value:08x}"
            )

    def put32(off: int, value: int) -> None:
        if off < 0 or off + 4 > len(work):
            raise ProtocolError(f"stub patch outside image at +0x{off:x}")
        work[off:off + 4] = p32(value)

    put32(0x14E4, 0x08006DC0)
    put32(0x165C, 0x080069C7)
    put32(0x1770, 0x08006DC0)
    work[0x1B2D] = 0x0A
    work[0x1B2E] = 0x00
    put32(0x27E0, 0x8C920000)
    return bytes(work)


def patch_target_stub_for_full_flash_read(stub: bytes) -> bytes:
    """
    Extend the vendor read patch to the complete 1 MiB target SPI.

    The exact STK read route stops at the first 0x400-byte boundary where
    its running 16-bit sum matches flash word +0x20.  That is the encoded
    container extent, not the physical P25D80SH size.

    This project-specific patch preserves the vendor SPI/UART implementation
    but forces the loop to the known physical end of the 1 MiB target flash.
    """
    work = bytearray(patch_target_stub_for_read(stub))

    expected = {
        0x2750: 0x3C068022,  # lui a2,0x8022
        0x2768: 0x1611FFFB,  # bne s0,s1,loop
    }
    for off, value in expected.items():
        actual = u32le(work[off:off + 4])
        if actual != value:
            raise ProtocolError(
                f"full-read patch mismatch at +0x{off:x}: "
                f"0x{actual:08x} != 0x{value:08x}"
            )

    # Original end: 0x8021E000 (2 MiB cap from staging base).
    # Target end:   0x8011E000 = 0x8001E000 + 0x100000.
    work[0x2750:0x2754] = p32(0x3C068012)
    # Ignore the checksum equality and continue until the fixed target end.
    work[0x2768:0x276C] = p32(0x1000FFFB)
    return bytes(work)


def patch_target_stub_for_write(stub: bytes) -> bytes:
    """
    Apply the exact rev-8203R write-firmware patches for target profile 2.
    """
    work = bytearray(stub)

    expected = {
        0x14E4: 0x0C006AFB,
        0x165C: 0x0C006AFB,
        0x1770: 0x0C006616,
    }
    for off, value in expected.items():
        actual = u32le(work[off:off + 4])
        if actual != value:
            raise ProtocolError(
                f"canonical write-helper mismatch at +0x{off:x}: "
                f"0x{actual:08x} != 0x{value:08x}"
            )

    work[0x1B2D] = 0x20
    work[0x1B2E] = ord("u")
    return bytes(work)


def load_canonical_stk_executable(source: pathlib.Path) -> bytes:
    if zipfile.is_zipfile(source):
        with zipfile.ZipFile(source, "r") as zf:
            names = zf.namelist()
            member = next(
                (name for name in names if name.endswith(STK_EXE_MEMBER)),
                None,
            )
            if member is None:
                raise ProtocolError(
                    f"{STK_EXE_MEMBER!r} not found in {source}"
                )
            exe = zf.read(member)
    else:
        exe = source.read_bytes()

    digest = hashlib.sha256(exe).hexdigest()
    if digest != STK_EXE_SHA256:
        raise ProtocolError(
            f"unexpected rev-8203R executable SHA-256: {digest}; "
            f"expected {STK_EXE_SHA256}"
        )
    return exe


def extract_target_stub(stk_source: pathlib.Path) -> bytes:
    exe = load_canonical_stk_executable(stk_source)

    off = pe_va_to_file_offset(exe, TARGET_STUB_VA)
    stub = exe[off:off + TARGET_STUB_SIZE]
    if len(stub) != TARGET_STUB_SIZE:
        raise ProtocolError("truncated embedded RAM-loader")
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
        # Physical target uses SPI NOR. STK profile 7 selects helper mode 2;
        # profile 2 selects the separate 29/39-series parallel-NOR path.
        self.write32(0x18FEC, TARGET_FLASH_MODE)
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
        if len(stub) > RAM_EXEC_MAX_SIZE:
            raise ProtocolError(
                f"RAM executable is too large: 0x{len(stub):x}; "
                f"safe recovered window is <= 0x{RAM_EXEC_MAX_SIZE:x}"
            )
        self.prepare_stub_upload()
        self.write32(RAM_STUB_ADDRESS, u32le(stub[:4]))
        self.stream_words(stub, 4)

    def initialize_bootrom(self) -> None:
        self.handshake()
        self.configure_baud_divisor()
        self.configure_target_system()

    def initialize_session(self, stub: bytes) -> None:
        self.initialize_bootrom()
        self.upload_stub(stub)


    def start_uploaded_stub(self) -> None:
        """
        Execute the recovered post-upload system-switch sequence used by STK.
        """
        self.exchange_byte(ord("S"), ord("S"))

        # First control write has a three-byte response; STK checks byte 2.
        self.write_exact(b"W" + p32(0x00000000) + p32(0x08006400))
        reply = self.read_exact(3)
        if reply[2:3] != b"W":
            raise ProtocolError(
                f"start control ACK mismatch: {reply!r}"
            )

        self.write32(0x00000004, 0)
        self.write32(0x00000008, 0)
        _ = self.read32(0x1FFE8048)
        self.write32(0x1FFE8048, 0x0000203F)
        self.write32(0x1FFE8008, 0)

    def monitor_until_nul(self, timeout_seconds: float = 5.0) -> str:
        """
        Collect the STK-compatible textual console until a zero terminator.
        """
        ser = self._serial()
        deadline = time.monotonic() + timeout_seconds
        chars: list[str] = []
        while time.monotonic() < deadline:
            b = ser.read(1)
            if not b:
                continue
            deadline = time.monotonic() + timeout_seconds
            if b == b"\x00":
                text = "".join(chars)
                if text:
                    sys.stdout.write(text)
                    sys.stdout.flush()
                return text
            if b == b"\r":
                chars.append("\n")
            elif b == b"\n":
                # STK's target puts() emits LF then CR; its UI uses CR as
                # the visible newline and ignores LF.
                continue
            elif 0x20 <= b[0] <= 0x7E or b == b"\t":
                chars.append(b.decode("ascii", "replace"))
        raise ProtocolError("timeout waiting for RAM-loader console terminator")

    def receive_firmware_image(self) -> bytes:
        """
        Receive the read-firmware stream used by STK.

        Flow control is unusual but instruction-confirmed: after the 4-byte
        size the host echoes size_bytes[0]; after every 16-byte block it echoes
        block[0].
        """
        self.monitor_until_nul(5.0)

        size_bytes = self.read_exact(4)
        size = u32le(size_bytes)
        if size > 0x200000:
            raise ProtocolError(
                f"RAM-loader reported implausible image size 0x{size:x}"
            )

        self.write_exact(size_bytes[:1])

        output = bytearray()
        while len(output) < size:
            block = self.read_exact(16)
            output += block
            self.write_exact(block[:1])

        return bytes(output[:size])

    def read_firmware(self, stub: bytes) -> bytes:
        """
        Initialize target Boot ROM, upload read-mode RAM stub, start it and
        return the firmware image received from the stub.
        """
        self.initialize_session(patch_target_stub_for_read(stub))
        self.start_uploaded_stub()
        return self.receive_firmware_image()


    def read_full_flash(self, stub: bytes) -> bytes:
        """
        Read the complete physical P25D80SH target image.
        """
        self.initialize_session(
            patch_target_stub_for_full_flash_read(stub)
        )
        self.start_uploaded_stub()
        image = self.receive_firmware_image()
        if len(image) != TARGET_FLASH_SIZE:
            raise ProtocolError(
                f"full flash read returned 0x{len(image):x} bytes; "
                f"expected 0x{TARGET_FLASH_SIZE:x}"
            )
        return image


    def restore_stock_flash(self, stub: bytes, image: bytes) -> str:
        """
        Execute the exact vendor write helper with the preserved stock image.

        The helper validates the image checksum before programming, performs a
        full SPI chip erase, then programs sequential 32-bit words from offset
        zero.  Generic modified-image writing remains intentionally unexposed.
        """
        if len(image) != TARGET_FLASH_SIZE:
            raise ProtocolError(
                f"stock restore image must be exactly 0x{TARGET_FLASH_SIZE:x} "
                f"bytes; got 0x{len(image):x}"
            )
        digest = hashlib.sha256(image).hexdigest()
        if digest != TARGET_STOCK_SHA256:
            raise ProtocolError(
                "restore-stock refuses non-canonical image: "
                f"sha256={digest}"
            )

        self.initialize_session(patch_target_stub_for_write(stub))
        self.upload_image_to_ram(image)
        self.start_uploaded_stub()
        return self.monitor_until_nul(30.0)


    def run_ram_image(
        self,
        image: bytes,
        wait_nul: float | None = None,
    ) -> None:
        """
        Load a raw MIPS image at physical 0x00019000 / execution VA
        0x80019000 and transfer control using the recovered STK sequence.

        This is RAM-only. It does not stage or program SPI flash.
        """
        self.initialize_session(image)
        self.start_uploaded_stub()
        if wait_nul is not None:
            self.monitor_until_nul(wait_nul)

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
            elif b == b"\n":
                continue
            elif 0x20 <= b[0] <= 0x7E or b == b"\t":
                sys.stdout.write(b.decode("ascii", "replace"))
            else:
                sys.stdout.write(f"<{b[0]:02x}>")
            sys.stdout.flush()


def add_serial_args(
    p: argparse.ArgumentParser,
    *,
    with_stk: bool = False,
) -> None:
    p.add_argument("--port", required=True)
    p.add_argument(
        "--baud",
        type=int,
        choices=sorted(BAUD_DIVISOR),
        default=115200,
    )
    p.add_argument("--timeout", type=float, default=1.5)
    if with_stk:
        p.add_argument(
            "--stk",
            type=pathlib.Path,
            default=pathlib.Path("tools/STK_0.2.3.zip"),
            help="canonical rev-8203R STK ZIP or executable",
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

    write32 = sub.add_parser("write32")
    add_serial_args(write32)
    write32.add_argument("address", type=lambda x: int(x, 0))
    write32.add_argument("value", type=lambda x: int(x, 0))

    upload = sub.add_parser("upload-ram")
    add_serial_args(upload)
    upload.add_argument("image", type=pathlib.Path)

    read_flash = sub.add_parser("read-flash")
    add_serial_args(read_flash, with_stk=True)
    read_flash.add_argument("output", type=pathlib.Path)
    read_flash.add_argument(
        "--expect-sha256",
        default=None,
        help="optional expected SHA-256 for immediate readback verification",
    )

    restore_stock = sub.add_parser("restore-stock")
    add_serial_args(restore_stock, with_stk=True)
    restore_stock.add_argument(
        "image",
        type=pathlib.Path,
        nargs="?",
        default=pathlib.Path("firmware/P25D80SH@SOP8.BIN"),
    )
    restore_stock.add_argument(
        "--confirm-chip-erase",
        action="store_true",
        help="required: acknowledge that the vendor helper erases the full SPI chip",
    )

    run_ram = sub.add_parser("run-ram")
    add_serial_args(run_ram)
    run_ram.add_argument("image", type=pathlib.Path)
    run_ram.add_argument(
        "--wait-nul",
        type=float,
        default=None,
        metavar="SECONDS",
        help=(
            "wait for a NUL-terminated one-shot status instead of opening "
            "the interactive UART monitor"
        ),
    )

    mon = sub.add_parser("monitor")
    add_serial_args(mon)
    mon.add_argument("--stop-on-nul", action="store_true")

    args = ap.parse_args()

    if args.command == "info":
        stub = extract_target_stub(args.stk)
        read_stub = patch_target_stub_for_read(stub)
        print(f"stk_sha256={STK_EXE_SHA256}")
        print(f"romloader_profile_index={TARGET_PROFILE_INDEX}")
        print(f"romloader_profile={TARGET_PROFILE_NAME}")
        print(f"image_sdram_profile_index={TARGET_IMAGE_SDRAM_PROFILE_INDEX}")
        print(f"image_sdram_profile={TARGET_IMAGE_SDRAM_PROFILE_NAME}")
        print(f"flash_mode={TARGET_FLASH_MODE}")
        print(f"sdram_width={TARGET_SDRAM_WIDTH}")
        print(f"embedded_stub_va=0x{TARGET_STUB_VA:08x}")
        print(f"ram_stub_address=0x{RAM_STUB_ADDRESS:08x}")
        print(f"ram_stub_size=0x{len(stub):x}")
        print(f"ram_stub_first_word=0x{u32le(stub[:4]):08x}")
        print(f"ram_stub_sha256={hashlib.sha256(stub).hexdigest()}")
        print(
            "read_stub_sha256="
            f"{hashlib.sha256(read_stub).hexdigest()}"
        )
        full_read_stub = patch_target_stub_for_full_flash_read(stub)
        print(
            "full_read_stub_sha256="
            f"{hashlib.sha256(full_read_stub).hexdigest()}"
        )
        print(f"target_flash_size=0x{TARGET_FLASH_SIZE:x}")
        print("read_patch_validation=ok")
        return 0

    with RomLoader(args.port, args.baud, args.timeout) as rl:
        if args.command == "monitor":
            rl.monitor(args.stop_on_nul)
            return 0

        if args.command == "read-flash":
            stub = extract_target_stub(args.stk)
            image = rl.read_full_flash(stub)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_bytes(image)
            digest = hashlib.sha256(image).hexdigest()
            print(f"read 0x{len(image):x} bytes -> {args.output}")
            print(f"sha256={digest}")
            if (
                args.expect_sha256 is not None
                and digest.lower() != args.expect_sha256.lower()
            ):
                raise ProtocolError(
                    "readback SHA-256 mismatch: "
                    f"{digest} != {args.expect_sha256}"
                )
            return 0

        if args.command == "restore-stock":
            if not args.confirm_chip_erase:
                raise ProtocolError(
                    "restore-stock requires --confirm-chip-erase"
                )
            image = args.image.read_bytes()
            stub = extract_target_stub(args.stk)
            rl.restore_stock_flash(stub, image)
            print(
                "stock restore helper reached its NUL terminator; "
                "power-cycle/reset and verify the image before any further write"
            )
            return 0

        if args.command == "run-ram":
            image = args.image.read_bytes()
            rl.run_ram_image(image, wait_nul=args.wait_nul)
            print(
                f"RAM image executed at VA 0x{RAM_EXEC_VA:08x}; "
                "SPI flash was not programmed"
            )
            if args.wait_nul is None:
                rl.monitor()
            return 0

        if args.command in ("probe", "write32", "upload-ram"):
            rl.initialize_bootrom()

        if args.command == "probe":
            print("ROM-loader Boot ROM session initialized")
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
