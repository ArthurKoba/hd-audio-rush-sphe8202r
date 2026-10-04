# JieLi BR23 / AC695N firmware acquisition

This directory is intentionally **read-only first**.

The current target evidence identifies the secondary controller as JieLi
BR23 / AC695N-family. The goal is to preserve its firmware before any write,
erase, OTP or chip-key operation is attempted.

## Preferred host workflow

Use `uv`. Do not create a venv manually and do not install Python packages
with pip.

### Windows with an existing COM port

Windows is the simplest path for the currently exposed USB-UART because
`COMx` can be opened directly. Python does not need to be installed:
`uv run` downloads/manages the requested Python runtime and script dependency.

From the repository root:

```powershell
.\uv.exe run .\tools\jieli\jieli_uart_probe.py --port COM7 --baud 9600 --seconds 10 --out reset_9600.bin
```

Replace `COM7` with the actual port.

First run **without** `--send-sync` while power-cycling/resetting the JieLi
controller. This only listens and records bytes.

Only after a passive reset capture, the documented BR23 Boot-ROM sync prefix
may be tested:

```powershell
.\uv.exe run .\tools\jieli\jieli_uart_probe.py --port COM7 --baud 9600 --seconds 10 --send-sync --out boot_sync_reply.bin
```

This local probe has no flash erase/write implementation.

### WSL / Linux

If the serial adapter is genuinely visible inside WSL/Linux:

```bash
uv run ./tools/jieli/jieli_uart_probe.py --port /dev/ttyUSB0 --baud 9600 --seconds 10 --out reset_9600.bin
```

A Windows `COMx` being present does not guarantee a matching Linux
`/dev/ttyUSBx` in WSL2. If the adapter is not visible, use the Windows
portable-`uv` path rather than adding USB passthrough just for this probe.

## USB UBOOT1.00 path

Upstream tool:

https://github.com/kagaimiq/jl-uboot-tool

BR23 / AC695N is listed as working by upstream.

Clone it separately:

```powershell
git clone https://github.com/kagaimiq/jl-uboot-tool.git
cd jl-uboot-tool
```

No `pip install` is required. Run it through uv with its declared upstream
dependencies:

```powershell
..\uv.exe run --with crcmod --with pyyaml --with pycryptodomex --with tqdm .\jluboottool.py --chip br23
```

On Linux/WSL the same invocation is:

```bash
uv run --with crcmod --with pyyaml --with pycryptodomex --with tqdm ./jluboottool.py --chip br23
```

If UBOOT1.00 is detected, start with a small read:

```text
dump 0 256
```

Then read the detected flash capacity twice to two different files:

```text
read 0 <FLASH_SIZE> jieli_flash_read1.bin
exit
```

Re-enter UBOOT and repeat:

```text
read 0 <FLASH_SIZE> jieli_flash_read2.bin
exit
```

Verify the two files from the project repository:

```powershell
.\uv.exe run .\tools\jieli\verify_dumps.py .\jieli_flash_read1.bin .\jieli_flash_read2.bin
```

or:

```bash
uv run ./tools/jieli/verify_dumps.py ./jieli_flash_read1.bin ./jieli_flash_read2.bin
```

## Commands that are out of scope during acquisition

Do not use:

- `write`;
- `erase`;
- `erasechip`;
- `burnchipkey`;
- OTP programming;
- any command that changes flash contents.

## UART limitation

The public BR23 Boot-ROM UART protocol is sufficient to identify the loader
entry mechanism and upload/execute RAM code. The post-loader UART flash-read
transport is not yet documented strongly enough in this project to call the
UART path a complete firmware dumper.

Therefore the current sequence is:

1. passive UART reset capture;
2. Boot-ROM sync probe if appropriate;
3. prefer USB UBOOT1.00 for a complete flash read when available;
4. only add a custom UART RAM dumper after its return/read protocol has been
   recovered, never by guessing packet formats.

## Acquisition acceptance

A firmware dump becomes analysis authority only after:

- two independent reads are byte-identical;
- SHA-256 matches;
- size matches the detected flash capacity;
- the first captured image is preserved immutable;
- reverse engineering is done on a copy.
