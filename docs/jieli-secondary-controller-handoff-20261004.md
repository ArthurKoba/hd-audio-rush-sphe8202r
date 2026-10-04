# Secondary JieLi controller — acquisition / identification handoff (2026-10-04)

This document is the continuation authority for the secondary 48-pin JieLi controller investigation. It records **physical target facts**, **software/runtime evidence**, **rejected identifications**, **external research**, **tooling**, and the exact continuation boundary.

## 1. Goal and current phase

Current project phase is firmware reconstruction first. For the secondary controller the immediate goal is:

1. identify the actual silicon/package variant strongly enough to select the correct Boot-ROM/update transport pins;
2. acquire the original firmware **read-only first**;
3. preserve two identical independent dumps;
4. only then begin pi32v2/static analysis and recover the remaining SPHE <-> secondary-controller boundary.

Do not erase, program, burn OTP/chip keys, or guess boot pins from a merely similar JieLi datasheet.

## 2. Target hardware facts — authoritative

These are physical observations from the actual HD Audio Rush board and override family guesses.

- Manufacturer/logo: JieLi/JL logo reported on package.
- Package: quad 48-pin package, 12 leads per side.
- Top mark transcription: `AK24 / BB24 / 230`.
  - Earlier repository text used `AK24BP24230`; this is **not proven as one continuous literal part number**.
  - Treat line joining / missing characters such as `BP` as unresolved until a clear macro image is archived.
- Direct continuity to board ground with power removed:
  - **pin 12 = GND**;
  - **pin 13 = GND**;
  - **pin 36 = GND**.
- Existing accessible serial header/adapter traces to package pins **23 and 24**.
- The pins 23/24 connection produces a coherent runtime/debug log at **115200 baud**.

The three hard-ground pins are a mandatory fingerprint. A candidate package is rejected if any of pins 12, 13, or 36 is documented as a non-ground signal.

## 3. UART observations from the target

Host used by the user: Windows, COM5, `uv run` workflow.

### Passive 9600 capture

Command family: local `tools/jieli/jieli_uart_probe.py`, listen-only.

Observed:
- one byte: `0C`.

Interpretation:
- line is electrically active around reset;
- this is **not sufficient** to identify a Boot-ROM UART.

### 9600 documented-sync experiment

The local probe sent only the public BR23-style sync prefix:
`55 AA 01 20 22 75 61 72 74`.

Observed:
- 196 received bytes;
- capture CRC32: `0x0A617C9D`;
- response consisted mostly of zeros / non-text pseudo-random bytes and ended in `0C`.

Interpretation:
- this did **not** look like a confirmed BR23 Boot-ROM handshake;
- no flash erase/write/program operation was implemented or used.

### Passive 115200 capture

Observed:
- 3160 bytes;
- capture CRC32: `0x4599AFDB`;
- coherent readable boot/runtime log.

Important strings reconstructed from the capture include:

- `setup_arch Feb 12 2023 14:40:24`
- `P3 Reset Source : 0x2`
- `[SDFILE]VM size: 0x2a000 @ 0x53000`
- `[SDFILE]disk capacity 1024 KB`
- `[SDFILE]sdfile mount succ`
- source-build path containing:
  `AC69XX/Software/AC695N_soundbox_sdk_release_3.1.0_LineIn_IIS/SDK/apps/soundbox/board/br23/board_ac695x_demo/board_ac695x_demo.c`
- `UserUartInit success`
- `[TEST-UPDATE]testbox msg handle reg:...`
- `audio_enc_init`
- `audio_dec_init`
- `[AUDIO-DAC]audio_dac_init`
- `ALINK_SR = 44100`
- `pcm`
- `spdif_dec_start`
- `APP_LINEIN_TASK`
- `ladc_ch_num[2],[3]`
- `linein->channel_num:2`

Interpretation:
- pins 23/24 are a **runtime/debug serial path** in the running target firmware;
- the firmware has strong BR23/AC695N SDK lineage;
- this is **software-lineage evidence, not exact silicon identification**;
- the reported 1024 KB is a useful firmware/storage observation, but it does not by itself prove the physical flash die/package arrangement.

The raw `reset_115200.bin`, `reset_9600.bin` and `boot_sync_reply.bin` remain on the user's workstation unless separately uploaded. The repository currently records the observed metadata and strings, not those raw files.

## 4. What the software lineage does and does not prove

Strongly supported from runtime execution:
- target code is derived from / highly compatible with the AC695N soundbox SDK lineage;
- board source lineage references `br23/board_ac695x_demo`;
- runtime initializes ALINK at 44.1 kHz;
- target line-in uses two LADC channels;
- target has JieLi test/update infrastructure registered.

Not proven:
- exact commercial silicon model;
- exact package pinout;
- that the chip is literally AC6951B/AC6951C;
- that BR23 Boot-ROM UART uses the same pins on this top-mark/package;
- that pins 23/24 are USB D+/D- on this physical variant;
- that the current accessible UART can enter Boot ROM/update mode;
- that the exact 1 MiB physical flash can already be read through that UART.

## 5. Rejected LQFP48 / 48-pin candidates

Candidates are rejected against the mandatory target fingerprint GND=12/13/36.

### AC6951C
Rejected.
- public pinout: pin 13 = VSSIO, pin 36 = DACVSS;
- but pin 12 = BT_RF, not ground.
Therefore it cannot be used as the target package pinout.

### AC6921A
Rejected.
- pin 12 = VSSIO;
- pin 13 = BT_OSCI;
- pin 36 = DACR.
Does not match.

### JL7031C
Rejected.
- pin 13 = VSS;
- pin 12 = BTRF.
Does not match.

### AC4601
Rejected.
- pin 12 = FMVSS;
- pin 13 = USBDM;
- pin 36 = PA9.
Does not match.

Any older statement assigning a target boot pin from one of these candidates is withdrawn.

## 6. Marking-code research

The exact literal `AK24BP24230` has not been found in a trustworthy public datasheet or model mapping.

However, multiple real marking/top-code strings with the same `AK24BP...` shape were found in marking-code/search databases, including:

- `AK24BP24178-51C8`
- `AK24BP24220-C8` / `AK24BP24220-51C8`
- `AK24BP0H003`
- `AK24BP0K599`
- `AK24BP21078`
- `AK24BP27485-51C8`

Related JieLi-looking contemporary marks also occur as `AC24BP...`, `AB24BP...`, `AS24BP...`, `AG24BP...`.

What this supports:
- `AK24...` is plausibly a production/top-mark family, not a normal public model name.

What it does **not** support:
- a direct mapping from the target mark to one specific retail model;
- any exact target pinout.

## 7. External sources / sites inspected

### Primary / technically useful

1. **kagaimiq/jl-uboot-tool**
   - https://github.com/kagaimiq/jl-uboot-tool
   - https://github.com/kagaimiq/jl-uboot-tool/blob/main/README.md
   - https://github.com/kagaimiq/jl-uboot-tool/blob/main/docs/uart-protocol.md
   - https://github.com/kagaimiq/jl-uboot-tool/blob/main/data/uart-loaders.yaml
   - https://github.com/kagaimiq/jl-uboot-tool/blob/main/docs/what-is-uboot.md

   Useful findings:
   - BR23/AC695N is supported by the project in its established UBOOT workflow;
   - public BR23 Boot-ROM UART-loader framing exists;
   - upstream metadata includes a BR23 UART loader and a RAM-load address/encryption description.

   Limitation:
   - the project's normal complete flash-reading flow is centered on UBOOT/USB;
   - the post-RAM-loader UART flash-return/read transport is not sufficiently established in our project to invent a complete UART dumper safely.

2. **Official JieLi documentation / repositories**
   - https://doc.zh-jieli.com/
   - https://doc.zh-jieli.com/AW33/zh-cn/master/update/testbox_update/testbox_update.html
   - https://doc.zh-jieli.com/AC63/zh-cn/release_v2.3.0/module_demo/ota/ota_introduce.html
   - https://github.com/Jieli-Tech
   - https://github.com/Jieli-Tech/fw-Bootloader
   - https://github.com/Jieli-Tech/AD24N

   Useful findings:
   - confirms JieLi update/testbox/boot infrastructure as a real platform concept;
   - supports treating the runtime `[TEST-UPDATE]` string as meaningful software infrastructure rather than random application text.

   Limitation:
   - no public document inspected so far maps target top mark `AK24 / BB24 / 230` to an exact 48-pin model/pinout.

3. **Yunthinker JieLi document archive**
   - https://www.yunthinker.com/
   - https://www.yunthinker.net/
   - example archive PDF opened during research:
     https://www.yunthinker.com/static/upload/file/20250104/1735974520457924.pdf

   Useful:
   - large collection of JieLi datasheets/reference material;
   - used to search/compare 48-pin candidates and ground/power layouts.

   Limitation:
   - no exact target fingerprint match was obtained in the current pass.

4. **Shenzhen Guanrong marking-code database**
   - https://www.tvs-gr.com/code/
   - https://www.tvs-gr.com/en/code/

   Useful:
   - search/index pages expose many `AK24BP...` / `AC24BP...` style strings;
   - supports the top-mark-family hypothesis.

   Important negative result:
   - direct exact lookup for `AK24BP24220` returned no structured model row even though the string is indexed in the site's popular/search corpus;
   - therefore these strings must not be treated as proven model mappings.

### Search engines / discovery surfaces

- Google Search and Google Images: many query variants for exact mark, Chinese JieLi terms, LQFP48, GND/VSS fingerprint, adjacent AK24BP codes.
- Bing: exact/variant marking queries; no useful exact model mapping found.
- Baidu: attempted through the MCP browser; repeated upstream timeout, no usable result from this pass.
- Google searches scoped to GitHub, Gitee and GitCode for `AK24BP`: no useful source-code mapping found.

These search-engine summaries are discovery aids only, not evidence for a part-number claim.

## 8. Acquisition tooling currently in repository

Directory: `tools/jieli/`

- `jieli_uart_probe.py`
  - PEP 723 inline dependency metadata;
  - intended to run via `uv run`;
  - passive UART capture;
  - optional documented sync-prefix transmission;
  - **no flash erase/write/program implementation**.
- `verify_dumps.py`
  - compares two independent reads by size and SHA-256.
- `README.md`
  - acquisition workflow and safety boundary.

The user already has `uv`; do not instruct them to install/download uv again.

## 9. Safety / acceptance rules for dumping

Until exact hardware transport is established:

- no erase;
- no chip erase;
- no generic flash write;
- no OTP write;
- no chip-key burn;
- no guessed strap/boot pin based on a rejected candidate;
- no 5 V/RS-232 signaling assumptions.

A successful acquisition is accepted only after:
- two independent complete reads;
- same byte count;
- identical SHA-256;
- first raw dump preserved immutable;
- analysis performed on a copy.

## 10. Current continuation priority

The next agent should **not** re-prove the AC695N runtime log or ALINK 44.1 kHz.

Priority order:

1. Search for exact or adjacent `AK24 / BB24 / 230` top-mark mapping.
2. Search 48-pin JieLi packages/schematics/datasheets for exact hard-ground fingerprint:
   `pin12=GND, pin13=GND, pin36=GND`.
3. Only after a package matches all three grounds, identify that variant's Boot-ROM/update UART/USB pins.
4. If no public mapping exists, use non-destructive target fingerprinting next (additional GND/power/known UART continuity) rather than guessing a model.
5. Build/enable a read-only UART RAM dumper only once the correct Boot-ROM transport and post-loader return protocol are grounded.
6. After dump acquisition, create the pi32v2 static-analysis target and recover the remaining control/status transport to SPHE.

## 11. Current project-level percentages

These are approximate behavior/reconstruction coverage, not hardware/product readiness.

- SPHE <-> JieLi audio/control boundary: ~72%.
- JieLi firmware/control domain: ~45%; raw firmware is the major missing artifact.
- JieLi UART: runtime/debug path known; Boot-ROM/update acquisition path not yet established.
- USB Host on SPHE: ~93%, paused at hardware boundary.
- USB Device/UAC: ~48%, deferred.
- DSP resource/headroom model: ~55%, active firmware-analysis gap.

The firmware-first project policy remains: areas already blocked only on hardware acceptance stay frozen while software/reconstruction gaps such as JieLi acquisition and SPHE<->JieLi integration are attacked.
