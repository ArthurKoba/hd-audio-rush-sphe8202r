# HD Audio Rush 5.1 / SPHE8202R

Behavior analysis of the HD Audio Rush 5.1 decoder board revision `SPHE8202RD_SPDIF_V02`.

The repository keeps the canonical firmware/tool artifacts, reproducible analysis helpers, one UART excerpt, and behavior-analysis notes.

## Current analysis milestone — 2026-10-02

The current canonical Analysis project is `sphe8202r_decoder_p25d80`.

**Current continuation authority:** [MUSIC MODE, decoder input ring and audio-service contracts](evidence/ap1-music-mode-20261002.md). Read this checkpoint before using older audio handoffs. Its explicit corrections supersede conflicting EQ-table, configured-window and success-result interpretations in `docs/analyze-status.md`, `docs/firmware.md` and the earlier evidence files; those older documents retain useful historical detail, not a newer acceptance claim.

- **`srvdsp.bin` is no longer a blocked/legacy-only DSP blob.** A dedicated `SunplusSPHEAudioDSP:BE:16:default` processor model is deployed through `ArthurKoba/ghidra-mcp` and validated in the live Analysis runtime. The canonical program is `/dsp_sunplus/srvdsp.bin`; the old `/modules_probe_mipsle/srvdsp.bin` remains only as a preserved wrong-language probe and must not be used for current conclusions.
- **Canonical `srvdsp` local coverage is complete at implementation-proof level:** 32 vector words, 117/117 local executable words, 9/9 local action nodes, 9/9 high-level behavior views, real CNTR-controlled `DO ... UNTIL CE` flow, 21 named/typed DM state/config slots, and a structured PM data bank. This does not close resident DSP behavior outside that blob.
- The two previously described “FIR” coefficient blocks are exact Q13 sine windows. `PM:193E..195C` is a 31-point table `round(8192*sin(pi*(i+1)/32))`; `PM:195F..1975` is a 23-point table `round(8192*sin(pi*(i+1)/24))`, with zero error for every stored coefficient.
- `PM:1906..1939` is a 4x13-word coefficient-preset bank: seven fields are constant and six change in stepped patterns. Some constant sub-sequences form near-geometric gain-like steps (~±2.44 dB/step). Exact product-level effect remains outside the local blob because the consumer is resident DSP code.
- **AP1 semantic naming is now 135/3847, approximately 3.51%.** This is a naming metric only, not audio-path completeness. The last earlier forwarder snapshot was 60; it is not being presented as a newly measured count.
- **MUSIC MODE separates SRND, EQ, BAND and KEY.** There are five fixed EQ curves (STANDARD/CLASSIC/ROCK/JAZZ/POP), not seven; the real bank starts at `0x8070B388`. Index 7 selects the USER curve. Code value 13 is displayed as 0 dB. Factory policy makes non-OFF SRND and non-STANDARD EQ mutually exclusive; this is not a silicon limitation or the same control as GM5.
- **The configured decoder window is a CPU-fed input ring.** Native producer copies, byte cursors and three-byte-unit publication establish its transport role. Its configured byte capacities must not be treated as total/free DSP program memory or proof of PCM sample width.
- **Command acceptance and final audio state are distinct.** The service wait is bounded by a poll count, not a proved time unit. The common dispatcher can return 1 without issuing a command under a state-mask gate, while some higher wrappers ignore intermediate failure results. Start/stop/pause paths have separate final-state waits. Exact routes and caveats are in the current checkpoint.
- Four runtime action nodes were added with native evidence: `SetDspParameterWord24`, `GetDspParameterWord24`, `WaitForAudioServiceConditions`, and `GetDecoderInputRingFreeBytes`. One AP1 link was corrected against its original instruction and saved; the remaining local link corrections and ABI warnings are explicitly tracked, not silently treated as repaired.
- Future upstreaming of reusable Sunplus/SPHE processor support remains separate issue **#30**. It separates reusable processor semantics from this project's MCP/import/documentation glue and requires independent review before an official upstream contribution.

**The whole audio-path task remains open.** The earlier 97–98% audio estimate is historical, not a validated measure of the remaining DSP algorithms, resource budget or physical-output acceptance. Exact DSP consumers/effect behavior, clock/free-cycle budget, backend ownership and six physical output lanes still require further evidence. Implementation proof does not imply execution, board or integration proof.

Provider/safety incidents are tracked per module/tool in `ArthurKoba/mcp-bridge` issues. The board repository retains behavior evidence and recovery locators, not a second ongoing safety log.

## Project objective

The goal is **control-complete behavior analysis** of the whole board, not merely inspecting low-level behavior one firmware image.

The project is complete when we can preserve firmware from both processors, explain the important hardware and inter-chip contracts, rebuild or controlled modification each firmware through a known path, recover after a bad firmware experiment, flash modified firmware safely, and programmatically control the useful system action nodes without treating either processor as an unexplained black box.

For this project, "behavior-complete" does **not** mean every internal action node must be given a semantic name. It means the boot/update paths, hardware contracts, audio routing, control state, inter-chip protocol and firmware modification path are understood well enough to make intentional changes and validate them on hardware.

Before claiming behavior-complete, all of the following must be true:

- Sunplus raw dump preserved and its container/module layout understood;
- secondary-controller firmware dumped and preserved;
- both CPU architectures have a usable static-analysis path;
- SPHE <-> secondary-controller data/control links are mapped;
- S/PDIF input, AC3/DTS handling, volume/mute and six-channel output ownership are identified;
- USB/service interfaces and their boot/update roles are identified;
- packing/checksum/integrity requirements are reproduced;
- at least one safe recovery method is proven for each writable firmware domain;
- at least one intentional firmware modification is flashed and hardware-validated;
- a documented control path exists for source/mode, volume/mute, status and any later USB/Bluetooth extensions.

USB Audio Class, new Bluetooth behavior and similar additions are post-analysis features, not prerequisites for understanding the original board.

## Analysis toolchain decision

**analysis workspace stays. SCORE7 does not belong to this project's dependency set.**

- The extracted Sunplus application modules are coherent **MIPS32 little-endian**, so normal analysis workspace MIPS support is the correct path for `ap1.bin`, `drv_other.bin`, `cdrom.bin` and `wma.bin`.
- The custom SCORE7 backend came from the early, incorrect assumption that the packed 1 MiB Sunplus container itself was SCORE7 code. Correct STK extraction disproved that assumption for the primary modules.
- No current target binary on this board has been proven to require SCORE7. Auxiliary `iop` / `iop_rst` images remain unidentified and must not be labelled SCORE7 without evidence. The audio DSP uses the separate Sunplus-scoped model described above.
- SCORE7 is useful general analysis workspace work and should be maintained/contributed separately from this board project rather than treated as required infrastructure here.
- The secondary BR23 / AC695N-family side uses JieLi's **pi32v2** architecture. Once its flash is dumped, the intended static-analysis path is a pi32v2 analysis workspace processor definition, cross-checked against the JieLi toolchain/objdump and available AC695N SDK sources.

## Current work order

The active scope is the useful audio/runtime behavior of the board, not exhaustive naming of unrelated legacy media code.

1. **Complete the Sunplus audio route.** Recover S/PDIF/AUX input, codec state, decoder routing, DSP program/data layout, 5.1 processing, volume/mute, speaker topology, channel delay and six-channel output ownership.
2. **Recover UART diagnostics.** Establish the main-SoC UART behavior needed for runtime logs, test commands and controlled observation of the audio route.
3. **Recover the secondary-controller link.** Preserve its firmware, determine the SPHE <-> secondary-controller transport and framing, then map Bluetooth/control events and status exchange.
4. **Check USB capability only at the architectural boundary.** Determine whether the Sunplus USB block can operate in device/dual-role mode for a computer-facing audio or diagnostic interface. If it is host-only, deep removable-media behavior is not an active priority.
5. **Keep firmware rebuild, recovery and controlled modification reproducible** for both firmware domains.

Legacy DVD/CD/UI behavior is analyzed only when it is on a live route required by audio, startup, diagnostics or inter-chip control.

## Hardware platform

| Part | Identification | Current understanding |
|---|---|---|
| Main multimedia SoC | Sunplus `SPHE8202R` | Main decoder / multimedia processor |
| External RAM | marking reported as `PMS3064 / 16BTR-60N`; transcription still needs a clean photo | External SDRAM. STK reports `32M`, 16-bit, non-shared; exact vendor/capacity is not yet proven |
| SPI NOR | Puya `P25D80SH` | 8 Mbit / 1 MiB, contains the Sunplus firmware container |
| Secondary controller | marking `AK24BP24230` | Runs JieLi AC695N/BR23-family firmware according to UART log; exact public SKU unresolved |
| Analog switch | `HCF4052` / HCF4052B-family marking reported | Dual 4-channel analog multiplexer/demultiplexer; exact board routing still to be traced |
| Logic | `74HC04D` marking reported | Hex inverter; exact role on this board still to be traced |
| Analog output stage | `4558D`-marked 8-pin ICs near the outputs | 4558-family parts are dual op-amps; likely channel buffering/filtering/preamplification, exact topology not yet traced |

Physical/interface observations:
- the UART jumper/header used for the captured boot log routes to the secondary controller side; TX output is confirmed, an interactive RX shell is not;
- the four-pad USB/service footprint is reported to route to the main Sunplus side; exact D+/D-/VBUS/GND pin mapping is not yet archived as continuity evidence;
- board I/O includes optical/coaxial S/PDIF, AUX and six analog outputs (FL/FR/SL/SR/CEN/SUB).

See `docs/hardware.md` for evidence levels and open measurements.

## Repository artifacts

| Path | Size | SHA-256 |
|---|---:|---|
| `firmware/P25D80SH@SOP8.BIN` | 1,048,576 | `67d8301f043ecc4d725ec09e38f3c53dd7e71ec26192775811a6a05dd13b545e` |
| `tools/STK_0.2.3.zip` | 1,420,979 | `cba31e5d7d7345078d3178290a4578f0484b3eaa7bea4a7ea303b3db0da01c3a` |

`firmware/P25D80SH@SOP8.BIN` is the raw byte-for-byte SPI NOR dump from the target board. It is not a rebuilt image.

The STK ZIP contains exactly:
- `STK Sunplus Tool Kit 0.2.3 (rev 8203R) English.exe` — 1,057,792 bytes — SHA-256 `e58d7d6f6f9cff67cbcf7f2b1191afbf0ffc2de4ca63c4dbda30c486c82dbc89`
- `STK Sunplus Tool Kit 0.2.3 (rev 090811) English.exe` — 1,057,280 bytes — SHA-256 `c55483e26c520467e953660b417a329014135213d7f0d3c5e1279bff5a71fb00`
- `STK Sunplus Tool Kit 0.2.3 (rev 090824) English.exe` — 1,058,304 bytes — SHA-256 `855cabb99b057a00236c88ccb81a09b73fdb2c69c33f78879e3c5e09199f2025`

The rev-8203R build is confirmed to open the target dump and extract the module set.

## Extracted modules

The extracted files live directly in `firmware/modules/`. The redundant `modules.tar` archive is intentionally not kept.

| Module | Bytes | SHA-256 |
|---|---:|---|
| `ap1.bin` | 684192 | `3ccee96ffeb5a8668f055ce97b59fe65084d4f28d47286ee63dd21c4bd96047b` |
| `drv_other.bin` | 301072 | `e9463f81093a43990c39ca39555d2742f29ebb2fe7fc7ca7e8eac0b694de6451` |
| `rom12.bin` | 82528 | `6747dadb731d13fdd17ba29121e9267ccc221fdfd7f7337df19d6f6c89c4e52f` |
| `cdrom.bin` | 63264 | `476368446103ddeb3e067ec556472e7d2e18d68e6da2ce7911a539661f6f3b61` |
| `wma.bin` | 51308 | `8fd9d673b847b6764e8bd52888a86f42f040c0c07a141b9c3384f503eae8f26f` |
| `jpeg.bin` | 38816 | `466487578636c97949f1abf6a752279df98a80c51f3a8c38645db6181bc0a9ee` |
| `iop.bin` | 1424 | `f2bc8ee705fb723710998a452617facc12a7d044626cdce45a0e18c7f8afffca` |
| `srvdsp.bin` | 1128 | `f1c1cd85a647e3669f8bd39ccb75e53ec84a7d6951d17565207155d3e0457d12` |
| `iop_rst.bin` | 712 | `b1e9ecc0240a767f12b1f8cb544f1747d5fe85a8d0e11a5caf7bec1990a0e373` |

The remaining STK slots (`ap2`, `ap3`, `dvb`, `dvd`, `dvd_ipod`, `free`, `mp4`, `mpeg`, `rom3`) are zero-length files and are retained because they are part of the exact 18-slot extraction.

## Firmware findings — preserved early checkpoint

This section preserves earlier identification and address-audit evidence. Historical statements of open validation work below do not override subsequent milestones in the current checkpoint and `docs/analyze-status.md`.

STK identifies the dump as:
- version `02R-D-02`
- ROM requirement `1M`
- customer `SUNPLUS`
- `SDRAM 32M`, 16-bit, non-shared
- `Host USB 2.0 supported`
- 18 module slots
- password `5168`

STK displays `SPHE8203R` while the physical package is marked `SPHE8202R`; this remains an explicit contradiction.

The primary application modules `ap1.bin`, `cdrom.bin`, `drv_other.bin` and `wma.bin` contain coherent **MIPS32 little-endian** code. Working module map:
- `ap1.bin` -> `0x8067B800`, corrected base applied in canonical analysis workspace; remaining action node-boundary/reference cleanup is tracked separately;
- `wma.bin` -> `0x8073F000` established;
- `cdrom.bin` -> `0x8074C800` established;
- `drv_other.bin` -> `0x80775800` established.

The shared MIPS small-data/global pointer is confirmed as `$gp = 0x80002B00`. In `wma.bin`, independent absolute/gp-relative pairs resolve both `0x800035D8 - 0xAD8` and `0x80003684 - 0xB84` to the same GP.

A 2026-09-21 raw-instruction audit found 43 stale stored direct action links in the three non-AP1 modules. The encoded targets and stored links disagree; a repair source is saved but its application was blocked and is not claimed complete. Separately, AP1 initial-delay invokes, absolute/relative branch joins and string pointers contradict its old base. See `docs/firmware.md` before using existing action node addresses or inbound action lists.

The application contains S/PDIF/AC3/DTS/PCM/USB anchors. CDROM stream initialization now has a documented classifier-result-to-mode mapping, including `0xAC3 -> 3`, and a working state type in analysis workspace. STK's additive word-sum helper is identified, but target checksum reproduction, container reconstruction and safe repack are still open in this early checkpoint.

The canonical analysis project contains extracted CPU modules and the STK tool analysis. Flat imports of the 1 MiB Sunplus container remain removed; the raw dump is preserved as container evidence. No modified firmware image or hardware acceptance is claimed by this early checkpoint.

## Layout

```
firmware/
  P25D80SH@SOP8.BIN
  modules/
tools/
  STK_0.2.3.zip
  analysis workspace/RepairMipsDirectFlow.java
evidence/
  ac695n-boot-excerpt.log
  ap1-music-mode-20261002.md
analysis/
  modules.csv
docs/
  hardware.md
  firmware.md
  analyze-status.md
```

The GitHub issues are the task backlog; avoid creating extra planning documents for the same work.


## ROM-loader host support

The canonical headless client is `tools/sphe_romloader.py`. The older
`tools/sunplus_romloader.py` duplicate was removed because it encoded an
obsolete target/profile model.

Host transport is platform-selectable:

- `--transport auto` is the default;
- on Windows, `auto` selects the recovered synchronous Win32 transport;
- on Linux and other POSIX hosts, `auto` selects the pyserial transport and
  accepts normal serial device paths such as `/dev/ttyUSB0`,
  `/dev/ttyACM0`, `/dev/ttyS0`, or platform UART devices;
- `--transport factory` forces the Windows reference transport;
- `--transport pyserial` forces the portable transport on any supported host.

The portable backend keeps the recovered protocol and exact-length wrapper
semantics and applies the recovered size-dependent read/write timeout model as
closely as pyserial permits. Windows COMMTIMEOUTS behavior remains the exact
host-side timing reference.

No broad unit-test suite is enabled at this stage. The intended CI smoke is
deliberately small: Python syntax/import plus `sphe_romloader.py info`, which
verifies the canonical STK identity, helper extraction and controlled modification guards on
Windows and Linux. Hardware tests remain manual acceptance work.
