# JieLi UART probe evidence — 2026-10-04

## Target connection

- Host OS: Windows.
- Serial port used by user: COM5.
- Physical board trace: accessible serial lines reach secondary-controller package pins 23 and 24.
- Tool: `tools/jieli/jieli_uart_probe.py` executed with `uv run`.

## Probe 1 — passive 9600

Observed target output:
`0C`

No bytes were intentionally transmitted by the probe.

Conclusion: reset-time activity exists, but one byte is not enough to identify Boot ROM.

## Probe 2 — 9600 with documented sync prefix

Transmitted by explicit user action:
`55 AA 01 20 22 75 61 72 74`

Received:
- 196 bytes;
- CRC32 `0x0A617C9D`;
- mostly zeros/non-text binary-looking bytes;
- final observed `0C`.

No erase/program/flash-write functionality exists in the local probe.

Conclusion: no confirmed BR23 Boot-ROM handshake was demonstrated on the currently exposed serial path.

## Probe 3 — passive 115200

Received:
- 3160 bytes;
- CRC32 `0x4599AFDB`;
- coherent firmware boot/runtime text.

High-value strings:
- `setup_arch Feb 12 2023 14:40:24`
- `[SDFILE]VM size: 0x2a000 @ 0x53000`
- `[SDFILE]disk capacity 1024 KB`
- `[SDFILE]sdfile mount succ`
- `AC695N_soundbox_sdk_release_3.1.0_LineIn_IIS`
- `board/br23/board_ac695x_demo/board_ac695x_demo.c`
- `UserUartInit success`
- `[TEST-UPDATE]testbox msg handle reg`
- `audio_dec_init`
- `audio_dac_init`
- `ALINK_SR = 44100`
- `spdif_dec_start`
- `APP_LINEIN_TASK`
- `ladc_ch_num[2],[3]`
- `linein->channel_num:2`

Conclusion:
- the exposed pins 23/24 form a working runtime/debug UART at 115200 in this firmware;
- the firmware's software lineage is strongly tied to the AC695N/BR23 soundbox SDK;
- exact silicon/package model remains unknown and must not be inferred from the build path alone.
