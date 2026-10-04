# JieLi secondary-controller firmware acquisition

This directory is intentionally **read-only first**.

## Current identification boundary

The exact silicon model is **UNKNOWN**.

Target hardware facts:
- JieLi/JL logo;
- 48-pin quad package;
- top mark transcribed as `AK24 / BB24 / 230`;
- hard ground by target-board continuity: pins **12, 13, 36**;
- exposed runtime/debug serial traces to package pins **23/24** and is readable at **115200 baud**.

The target firmware has strong AC695N/BR23 SDK lineage, but that is **software evidence only**. Do not use an AC6951B/AC6951C pinout for this target unless a future datasheet matches all confirmed ground pins.

See:
- `docs/jieli-secondary-controller-handoff-20261004.md`
- `evidence/jieli-uart-probes-20261004.md`
- `docs/hardware.md`

## Host workflow

Use `uv`. Do not create a venv manually and do not install dependencies with pip.

The user already has uv installed.

### Runtime/debug UART capture

Known working target capture on the user's current setup:

```powershell
uv run .\jieli_uart_probe.py --port COM5 --baud 115200 --seconds 15 --out reset_115200.bin
```

This is passive/listen-only.

The currently exposed UART is **not proven to be the Boot-ROM/update UART**. Do not send additional boot/update packets until the exact package/transport is identified.

## Local tool safety

`jieli_uart_probe.py`:
- captures serial bytes;
- can send only the explicitly implemented sync prefix when requested;
- contains no flash erase/write/program command.

`verify_dumps.py`:
- compares two independent dump files by size and SHA-256.

## Upstream UBOOT research tool

https://github.com/kagaimiq/jl-uboot-tool

It remains relevant as protocol/reference material and may later be usable if the exact target can enter a compatible UBOOT transport.

Do not use destructive commands during acquisition:
- `write`;
- `erase`;
- `erasechip`;
- `burnchipkey`;
- OTP programming;
- any operation that changes the original firmware.

## Acquisition acceptance

A firmware dump becomes project authority only after:
- two independent reads are byte-identical;
- SHA-256 matches;
- size matches the established physical/logical flash capacity;
- the first dump is preserved immutable;
- reverse engineering uses a copy.
