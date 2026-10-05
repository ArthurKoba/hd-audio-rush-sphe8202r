# HD Audio Rush 5.1 / SPHE8202R

Behavior analysis of the HD Audio Rush 5.1 decoder board revision `SPHE8202RD_SPDIF_V02`.

The repository keeps the canonical firmware/tool artifacts, reproducible analysis helpers, one UART excerpt, and behavior-analysis notes.

## Current analysis milestone — 2026-10-02 late pass

The canonical Analysis project remains `sphe8202r_decoder_p25d80`. The current continuation authority is this README together with `docs/analyze-status.md` and `evidence/ap1-music-mode-20261002.md`; older handoffs are historical where they conflict with these files.

### DSP processor/tooling

- The reusable Sunplus audio-DSP processor is implemented in `ArthurKoba/ghidra-mcp` as `SunplusSPHEAudioDSP:BE:16:default` and is deployed from `ghidra-mcp/main` commit `5570d8c`.
- `srvdsp.bin` remains closed at implementation-proof level after post-deploy revalidation: 117/117 local executable words, 9/9 local action nodes, 9/9 high-level behavior views, and 21/21 named, typed and documented DM state/config slots.
- Codec-profile support is no longer blocked on missing instruction forms. Vector-seeded reachable-code acceptance is zero-gap for the current extracted profiles: AUX 5451/5451, PCM 7787/7787, AC-3 10339/10339 and DTS 9651/9651 reached words decoded.
- Wrapper-only resident handoffs and the recovered `DO ... UNTIL CE` specialization are context-scoped to canonical `srvdsp`; generic codec profiles keep ordinary local flow semantics. RTI remains distinct from RTS through an explicit status-restoration side effect.
- This is target-corpus instruction coverage, not proof of the full ADSP-218x ISA, Sunplus DSP clock/resource budget or physical output routing.

### Current AP1 / runtime audio contract

- Current saved AP1 snapshot: **3857 action nodes**, **159 custom/semantic action names (~4.12%)**. This is a naming/refactor metric only; the saved Analysis project is the canonical semantic authority.
- Saved semantic names now include `SelectDecoderProfileByStateMask` and `LoadDecoderDspProfile`. Profile selection uses the least-significant decoder-state bit and the descriptor table rooted at `0x80002264`.
- Decoder profile descriptor layout is packed-source pointer `+0`, A `+4/+5`, B `+6/+7`, C `+8/+9`; the load route derives page selectors `0xF8`, `0xF8+A`, `0xF8+A+C`, initializes runtime service state, validates input-ring compatibility and transfers the packed profile.
- Real runtime targets are `0x88001584` for service initialization and `0x88001AF8` for packed-profile transfer. Older high-level views showing `+0x800` displaced targets are stale metadata; raw MIPS transitions are authoritative.
- `ValidateDecoderProfileInputRingCapacity` now has a corrected instruction-backed contract: decoder states `0x8000`/`0x40000` add 3 to the descriptor capacity unit before scaling/comparison. The old high-level extra-call interpretation is withdrawn.
- The decoder window is a CPU-fed input ring, not a free-DSP-memory measurement. Runtime 24-bit parameter read/write, service-condition polling and input-ring free/queued-byte helpers remain saved in `/runtime/rom12-runtime.bin`.
- Master-volume action 2 maps level through runtime gain table `0x88012CA0`, stages `0x1100|gainByte`, and keeps mute as separate state. `drv_other:0x8077C554` is a constant-zero stub in this firmware.
- Speaker state is instruction-backed: FRONT `gp+0x827`, CENTER `gp+0x7DC`, REAR `gp+0x80E`, SUB `gp+0x7D6`; topology is action `0x17`; SUB also uses action 6; CENTER/REAR delay formulas are confirmed through action `0x0B`.
- External hardware mode 3 is AUX; modes 0..2 are S/PDIF-input-side patterns whose physical optical/coax meaning remains unknown. AUX uses transient state `0x0B`; S/PDIF-input uses `0x0D`; anti-pop sequencing temporarily applies master volume zero.
- Decoder status block `0x800022E4` is 16 bytes. Hardware decoder type bits map 0=PCM, 1=AC-3, 2/3=DTS-family; type changes can stop/reconfigure/restart the pipeline.
- The common dispatcher action table `0..26` is mechanically recovered. Control `0x57` is confirmed **ECHO**; canonical Analysis now saves `ApplyEchoProfileIndex @ 0x80702C8C` and `ApplyEchoHardwareProfile @ 0x80702CC8`, both on action 4 / family `0x0600`.

### Readiness boundary

The old `97–98%` whole-audio estimate is retired. A useful current scoped estimate is that the **CPU-side audio control/loader contract is approximately 90–95% implementation-proof**. The denominator is CPU-side control behavior only.

Controlled in-place behavior-preserving patches can already be designed. Replacement/custom firmware is still gated by container rebuild/repack/integrity reproduction, safe recovery/rollback, remaining resident runtime/backend ownership, DSP resource-budget evidence, physical six-channel output acceptance and at least one hardware-validated intentional modification.

Provider/safety incidents are tracked in `ArthurKoba/mcp-bridge`; this repository keeps behavior evidence and recovery state, not a duplicate incident log.

### Implementation start boundary

The intended product path is explicit:

1. reproduce the original useful audio behavior in maintainable Sunplus-side source/firmware;
2. validate that replacement against the original board behavior;
3. only then add new product features or altered behavior.

We are already far enough to design and begin source-level replacement modules for isolated CPU-side behavior. We are **not** yet at the point where a complete replacement image should be flashed as product firmware. Remaining hard gates are container/module rebuild and integrity reproduction, safe rollback/recovery, resident runtime/backend ownership, physical six-channel acceptance, and one hardware-validated intentional modification.

Current interface boundary:
- **SPHE UART:** ROM-loader/monitor behavior is implementation-recovered, including RAM-code loading, memory transactions, flash read and a minimal runtime TX contract. Physical RX/TX/bootstrap access on this PCB is not yet continuity/board-proven.
- **Secondary-controller UART:** the observed header emits AC695N/BR23-family logs; TX is confirmed, but no interactive RX shell or command protocol is established.
- **USB:** the four-pad footprint is reported on the SPHE side and firmware metadata says Host USB 2.0 supported. Device/dual-role/UAC capability is still unknown, so a computer-facing custom USB interface is not yet an accepted design assumption.
- **Secondary controller:** its firmware has not been dumped and the SPHE↔controller transport/framing is not mapped. Current UART evidence proves its software family and runtime audio/Bluetooth activity, not the inter-chip control protocol.

## Project objective

The primary engineering goal is to build our own maintainable Sunplus firmware that first reproduces the original board's useful audio behavior and can then be modified deliberately. Behavior analysis is the evidence path to that implementation, not the final product by itself.

Whole-board completion additionally requires preserving the secondary-controller firmware, explaining the relevant hardware and inter-chip contracts, rebuilding or deliberately modifying each required firmware domain through a known path, recovering after a bad experiment, flashing safely, and programmatically controlling the useful system behavior without leaving a required processor as an unexplained black box.

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

## Current work order — firmware reconstruction phase

The project is currently in a **firmware-first reconstruction phase**. New board measurements and execution tests are deferred. Areas that already require target execution, continuity, analog measurements or flash acceptance are frozen until the static/software gaps below are exhausted.

Current priorities:

1. **SPHE <-> JieLi boundary.** Resolve the SPHE-side receiver for the proven JieLi ALINK audio stream and recover the separate control/status transport between processors.
2. **JieLi firmware domain.** Preserve/dump the secondary-controller firmware when practical, bring up pi32v2 static analysis, and recover the startup/audio/Bluetooth/control behavior required by the product.
3. **DSP resource model.** Recover PM/DM ownership, resident allocations, cycle/headroom constraints and the practical limits for replacement DSP behavior.
4. **Replacement image construction.** Finish module/container rebuild, packing and integrity/checksum reproduction, plus the software side of recovery/rollback.
5. **Remaining firmware-only Sunplus gaps.** Finish clock/sample-rate semantics, backend ownership and unexplained live source/control routes only where they materially affect original behavior.

Currently frozen at hardware boundary:
- USB Host bring-up: **93%** — controller/root/EP0/descriptors are recovered; next useful proof is the prepared RAM probe on target hardware;
- SPHE UART software path: **90%** — next useful proof is physical target access and execution;
- DAC/six-channel behavior: **90%** — remaining uncertainty is mainly board continuity/levels;
- front-panel SOURCE / 2.0-5.1 behavior: **93%** — remaining work is mostly physical GPIO/board detail.

USB Device/UAC is a later extension, currently about **48%** capability understanding. It is not a prerequisite for reconstructing the stock firmware and should not displace the larger original-system gaps.

Legacy DVD/CD/UI behavior is analyzed only when it is on a live route required by startup, audio, diagnostics or inter-chip control. Do not spend time polishing already-established audio behavior merely to raise a percentage.

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
