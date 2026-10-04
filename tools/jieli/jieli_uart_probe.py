#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pyserial>=3.5",
# ]
# ///
"""Read-only BR23 UART Boot-ROM probe.

This tool deliberately does not implement flash erase/write or arbitrary memory
writes. It is intended to answer one question first: does the exposed serial
connection reach the BR23 Boot-ROM UART at reset?
"""

from __future__ import annotations

import argparse
import binascii
import sys
import time

try:
    import serial
except ImportError as exc:
    raise SystemExit("pyserial is required: python -m pip install pyserial") from exc

SYNC = bytes.fromhex("55 AA 01 20 22 75 61 72 74")


def hexline(data: bytes) -> str:
    return " ".join(f"{b:02X}" for b in data)


def listen(port: str, baud: int, seconds: float) -> bytes:
    end = time.monotonic() + seconds
    buf = bytearray()
    with serial.Serial(port=port, baudrate=baud, timeout=0.05) as ser:
        ser.reset_input_buffer()
        while time.monotonic() < end:
            chunk = ser.read(256)
            if chunk:
                buf += chunk
                print(hexline(chunk))
    return bytes(buf)


def send_sync(port: str, baud: int, seconds: float) -> bytes:
    end = time.monotonic() + seconds
    buf = bytearray()
    with serial.Serial(port=port, baudrate=baud, timeout=0.05) as ser:
        ser.reset_input_buffer()
        ser.write(SYNC)
        ser.flush()
        while time.monotonic() < end:
            chunk = ser.read(256)
            if chunk:
                buf += chunk
                print(hexline(chunk))
    return bytes(buf)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", required=True, help="COM7, /dev/ttyUSB0, etc.")
    ap.add_argument("--baud", type=int, default=9600)
    ap.add_argument("--seconds", type=float, default=5.0)
    ap.add_argument(
        "--send-sync",
        action="store_true",
        help="send only the documented 55 AA ... uart sync prefix",
    )
    ap.add_argument(
        "--out",
        help="optional raw capture file",
    )
    args = ap.parse_args()

    print(f"[jieli] port={args.port} baud={args.baud}")
    print("[jieli] Power-cycle/reset the JieLi controller during the capture.")

    if args.send_sync:
        print(f"[jieli] sending documented sync prefix: {hexline(SYNC)}")
        data = send_sync(args.port, args.baud, args.seconds)
    else:
        data = listen(args.port, args.baud, args.seconds)

    print(f"[jieli] received {len(data)} bytes")
    if data:
        print(f"[jieli] crc32(capture)=0x{binascii.crc32(data) & 0xFFFFFFFF:08X}")

    if args.out:
        with open(args.out, "wb") as f:
            f.write(data)
        print(f"[jieli] saved {args.out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
