# Firmware

## Raw SPI dump

`firmware/P25D80SH@SOP8.BIN` is a **raw byte-for-byte dump** of the Puya P25D80SH SPI NOR from the target board.

- size: 1,048,576 bytes
- SHA-256: `67d8301f043ecc4d725ec09e38f3c53dd7e71ec26192775811a6a05dd13b545e`

It is a Sunplus firmware container, not one flat CPU executable. Do not modify the canonical dump or extracted modules in place.

## Sunplus STK

Tool archive: `tools/STK_0.2.3.zip`.

The rev-8203R build successfully opens the dump and extracts the firmware modules. Observed metadata:
- version: `02R-D-02`;
- ROM required: `1M`;
- customer ID: `SUNPLUS`;
- displayed SoC profile: `SPHE8203R`;
- SDRAM: `32M`, 16-bit, non-shared;
- Host USB 2.0: supported;
- module slots: 18;
- password: `5168`.

The displayed `SPHE8203R` conflicts with the physical `SPHE8202R` package marking. Keep this contradiction open.

## Extracted modules

The already-extracted files are stored directly in `firmware/modules/`; there is intentionally no duplicate tar archive.

CPU/code classification:
- `ap1.bin` — main MIPS32 LE application;
- `drv_other.bin` — MIPS32 LE driver/auxiliary code;
- `cdrom.bin` — MIPS32 LE module;
- `wma.bin` — MIPS32 LE WMA-related module;
- `rom12.bin` — container/config/resource-like, not a linear MIPS image;
- `jpeg.bin` — data/tables;
- `iop.bin`, `iop_rst.bin`, `srvdsp.bin` — auxiliary microcode/specialized image candidates.

Zero-length module slots are retained because STK produced an 18-slot set. Exact sizes and SHA-256 values are kept in the root `README.md`.

## Ghidra and address model

Canonical project: `sphe8202r_decoder_p25d80`. CPU programs live under `/modules_mipsle/`; the existing STK tool analysis lives at `/tools/stk.exe`. Earlier flat executable imports of the 1 MiB container have been removed.

Correct workflow: preserve the container, use extracted CPU modules as `MIPS:LE:32:default`, establish placement and shared GP, and validate instruction flow before relying on decompilation.

### Current map and reopened gate

`reverse/modules.csv` now distinguishes the AP1 static candidate from completed analysis:

| Module | Working base | Validation state |
|---|---|---|
| ap1 | `0x8067B800` | Corrected base applied in canonical Ghidra; function-boundary and stale-reference cleanup still pending |
| wma | `0x8073F000` | Established base; stale direct-flow refs remain |
| cdrom | `0x8074C800` | Established base; stale direct-flow refs remain |
| drv_other | `0x80775800` | Established base; stale direct-flow refs remain |

The former claim that AP1 `0x8067B000` was confirmed is withdrawn. The old provisional `cdrom=0x80754000` and `drv_other=0x80782000` candidates remain rejected. SCORE7 is not the active ISA or a project dependency.

### AP1 +0x800 contradiction: reproducible target evidence

The 684,192 original AP1 bytes in Ghidra were hashed again and match the canonical module checksum in README. The following observations concern the unchanged bytes, not a patched firmware:

| Evidence | File offset / instruction | Observation |
|---|---|---|
| Initial delay call | `ap1+0x78`, word `0x0C19EE00` | Encodes `jal 0x8067B800`, after loading `a0=10`; file offset zero is an `a0` countdown/delay leaf. Candidate base resolves the call to that leaf. |
| Cross-module entry | `cdrom+0x38`, word `0x0C1C0691` | Encodes `jal 0x80701A44`. With candidate AP1 base, this maps to `ap1+0x86244`, a routine starting with `lhu a1,0x744(gp)`, stack allocation and saved registers. At the old base the same target lands inside unrelated-looking partial state/epilogue code. |
| Absolute/relative join | `ap1+0x8632C` and `ap1+0x86350` | The absolute jump targets `0x80701AFC`; a nearby relative branch targets file offset `0x862FC`. Base `0x8067B800` makes both enter the same MMIO-update/return block. |
| String pointer | pointer at `ap1+0x615D0`, string at `ap1+0x5EDC8` | The stored pointer agrees with `0x8067B800 + 0x5EDC8` for `SPDIF/OFF`, not the old base. RAW/PCM pointer tables provide additional supporting matches. |

The cross-module entry offset is **`0x86244`**, correcting `0x85A44` in an earlier issue comment. Individual literal-pointer matches alone are not proof. Independent code evidence supports the candidate, but a corrected Ghidra model, remaining layout/loader checks and recovered function boundaries are still required.

Further raw-pointer checks:
- corrected translation table base is `0x806DCD88` (file `+0x61588`) with language stride `0x404 = 257*4`; raw item `113` is `AUDIO OUT`, item `117` is `SPDIF/RAW`, item `119` is `SPDIF/PCM`;
- file `+0x615D0` stores `0x806DA5C8`; with base `0x8067B800` this points exactly to `SPDIF/OFF` at file `+0x5EDC8`, while `0x8067B000` points into unrelated bytes;
- `SPDIF/RAW`/`SPDIF/PCM` candidate addresses `0x806DA8AC/0x806DA8B8` are referenced repeatedly from localized pointer blocks at file offsets `+0x6175C/+0x61764`, `+0x61F64/+0x61F6C`, `+0x62368/+0x62370`, `+0x6276C/+0x62774`, and `+0x62B70/+0x62B78`;
- the old Ghidra interpretation using file `+0x61180` (`0x806DA0AC/0x806DA0B8`) and outer file `+0x62964` is invalid under the candidate placement: those targets resolve into unrelated language-text data. Any prior RAW/PCM menu-setter conclusions based on that old address chain are withdrawn pending corrected placement/relocation analysis.

AP1 is now rebased to `0x8067B800` in the canonical Ghidra project. This corrects placement but does not automatically repair pre-existing function boundaries or stale references; current symbols/callers still require evidence-level validation.

### Stale direct-flow reference audit

The read-only audit derives each currently defined MIPS J/JAL destination from its raw word:

`target = ((PC + 4) & 0xF0000000) | ((word & 0x03FFFFFF) << 2)`.

Snapshot from 2026-09-21:

| Program | Instructions scanned | Defined J/JAL | Wrong stored flow refs | Error delta |
|---|---:|---:|---:|---|
| ap1 | 95,906 | 8,910 | 0 | none in this audit scope |
| wma | 10,225 | 742 | 2 | `+0x0073F000` |
| cdrom | 6,944 | 660 | 17 | `+0x0074C800` |
| drv_other | 12,184 | 962 | 24 | `+0x00775800` |

No missing flow references were found in that scope. All 43 wrong references had source `DEFAULT`; their deltas match the low parts of their module bases, consistent with stale references after rebasing. This audit excludes indirect calls, data references and undisassembled bytes. In particular, AP1 having zero mismatches does not establish its load base.

Examples:
- CDROM `0x8074C838`: encoded target `0x80701A44`, stored target `0x80E4E244`.
- CDROM `0x8074C850`: encoded target `0x807017A8`, stored target `0x80E4DFA8`.
- CDROM `0x8074CB7C`: encoded target `0x8074C868`, stored target `0x80E99068`. This hides the initializer's call to `DetectCdromStreamType` from normal caller queries.
- WMA `0x8073F090` and `0x8073F0A4`: encoded `memset` target `0x80783F64`, stored `0x80EC2F64`.

`tools/ghidra/RepairMipsDirectFlow.java` preserves a guarded repair implementation at commit `3688a523`. It defaults to audit, checks exact module hashes/bases and expected mismatch counts, and proposes only reference/comment changes inside a transaction. It does not patch bytes, rebase or run broad analysis. Its application was blocked by the tool safety layer: **no compile/application validation or repaired-reference count is claimed**. Do not bypass the block or treat source presence as completion. A later authorized execution must repeat the audit because shared project state can change.

### Shared GP and helper contracts

The shared GP remains `$gp = 0x80002B00`, independently supported by WMA absolute/gp-relative pairs:
- `0x800035D8 = gp + 0xAD8`;
- `0x80003684 = gp + 0xB84`.

AP1 instruction pair `0x806D96F8: lui gp,0x8801` / `0x806D96FC: lw gp,0x2200(gp)` proves the runtime GP restore word is at absolute `0x88012200`. The canonical Ghidra project currently also contains a stale auxiliary block `runtime_gp_slot` at `0x88012A00`, shifted by the AP1 rebase; an attempt to create a corrected replacement block was blocked by the tool safety layer. Treat `0x88012200` as the instruction-backed address and the shifted block as known-bad metadata.

Cross-module helpers identified in `drv_other.bin`:
- `0x80783F08` — byte-wise `memcmp`;
- `0x80783F3C` — byte-wise `memcpy`;
- `0x80783F64` — byte-wise `memset`.

## Firmware anchors and audio state

### Command mailbox path

Instruction-level AP1 analysis now identifies a paired command mailbox interface:
- `WriteCommandMailboxByte` at `0x8069B070`: writes a 16-bit key to `s6+0xE80`, byte value to `s6+0xE84`, polls handshake bit `0x8000`, then performs the `0x454B` completion transaction;
- `ReadCommandMailboxByte` at `0x8069B268`: writes the key to `s6+0xE80`, polls `s6+0xE88` bit `0x8000`, and returns the low response byte;
- raw initialization body beginning at `0x8069D4F8` programs `0x4627 -> 0x75` and `0x4628 -> 0x77`; identical pairs recur in four initialization clusters;
- helper `0x8069E1A4(param1,param2)` writes mailbox key `0x4000 | param1`. One runtime control-flow branch at `0x80684AA0..0x80684940` therefore issues exact transaction `0x401A <- 0x75`.

`0x75` is the confirmed translation-table item ID for `SPDIF/RAW`; `0x77` is the item ID for `SPDIF/PCM`. The standalone mailbox key `0x401A` remains semantically unresolved, but the higher-level OFF/RAW/PCM setter contract is now recovered independently through the control-descriptor/dispatcher path.

### S/PDIF OFF / RAW / PCM control contract

`ResolveControlIdToGroupSlot(0x71)` resolves S/PDIF output control to group 2 / slot 1. The descriptor at `0x80707FA3` is 13 bytes: `03 71 12 75 77 00 00 00 00 00 00 0B 00`. A working analytical type `ControlOptionDescriptor` is applied there; proven fields are packed ID/meta, control-ID low byte, eight option-ID bytes, state-slot byte at `+0x0B`, and two still-unknown metadata bytes.

The corrected translation table identifies descriptor options:
- `0x12` -> `SPDIF/OFF`;
- `0x75` -> `SPDIF/RAW`;
- `0x77` -> `SPDIF/PCM`.

`DispatchControlOption` at `0x80776210` masks the first argument as control ID and second as option ID. Its jump-table entry for control `0x71` calls `ApplySpdifOutputOption` at `0x807759E0` with that option ID. Instruction/decompiler behavior in `ApplySpdifOutputOption` is explicit: RAW `0x75` selects internal mode 2, PCM `0x77` selects internal mode 1, and OFF `0x12` follows the clear/reconfigure path. `IsSpdifPcmSelected` at `0x8077C21C` returns whether the currently selected descriptor option is `0x77`.

The descriptor's state-slot field is `0x0B`, mapping its current option index to `DAT_80006810[0x0B] = 0x8000681B`. `LoadControlSelectionsFromStateSlots` (`0x80777C0C`) copies indexed state slots into the generic selection table at `0x800066B0 + group*9 + slot`; `SaveControlSelectionsToStateSlots` (`0x80777C94`) performs the inverse copy. This closes the static state/persistence path for OFF/RAW/PCM selection. It does **not** by itself prove physical PCB routing or hardware-observed output behavior.


AP1 contains `SPDIF/OFF`, `SPDIF/RAW`, `SPDIF/PCM`, `SPDIF IN`, audio setup/output, AC3, DTS, PCM and USB/SD strings. Prefer stable file offsets until the address model is repaired:

| Anchor | AP1 file offset | Old Ghidra listing address, NOT validated runtime address |
|---|---|---|
| SPDIF/OFF | `0x5EDC8` | `0x806D9DC8` |
| SPDIF/RAW | `0x5F0AC` | `0x806DA0AC` |
| SPDIF/PCM | `0x5F0B8` | `0x806DA0B8` |
| SPDIF IN | `0x8FCA0` | `0x8070ACA0` |

Earlier work also recorded a status pool at old listing `0x8070AC00..0x8070AD07` containing DTS/PCM/AC3/no-signal and DVD/SPDIF/TUNER/AUXIN/MIC/USB labels. These are static firmware anchors, not PCB-routing evidence.

### S/PDIF input selection contract

AP1 contains a separate external-input subsource selector at `0x800032FA` (`gp+0x7FA`). Corrected instruction flow in the status/source display path at `0x8071E428..0x8071E4EC` proves:
- selector `1` enters the AUX branch and displays `AUXIN` (`0x8070B4D4`), with a related 2CH->2.1CH / 2CH->5.1CH status line;
- selector `2` displays `SPDIF IN` (`0x8070B4A0`);
- the other branch displays `TUNER` (`0x8070B4AC`).

`ToggleTunerSpdifInput` at `0x806FB920` is the concrete static setter: after its common setup helper it reads `0x800032FA` and toggles exactly `0 -> 2` or nonzero -> `0`, while updating source-state byte `0x800032A5`. This establishes a TUNER <-> S/PDIF input-selection path. `FUN_806FED18` additionally writes selector `1` or `2` from a broader external-input transition path; its complete higher-level contract is not yet named.

The higher source dispatcher uses `gp+0x7A5 = 0x800032A5` as an index `1..9` into the handler table at `0x8070B4E0`. Table entry 1 is confirmed as USB because its handler reaches the `USB` string at `0x8070B504`. The remaining source-handler mapping is still being resolved. These findings identify firmware source state and control; they do not establish the physical TOSLINK/coax routing on the PCB.

### Audio-core findings retained with address caveats

CDROM `0x8074C800`, previously named `ApplyCdromAudioModeFromSubtype`, maps a byte subtype as `0 -> 2`, `1..5 -> 1`, `6..10 -> 2`, `>=11 -> 4`. Its encoded calls are `0x80701A44` and conditionally `0x807017A8`. It reads `gp+0x774 = 0x80003274`, first as a byte and later as a halfword; the exact storage contract should be retained rather than simplified silently.

Earlier AP1 notes at old listing `0x807012C8` record writes to `gp+0x76C` and `gp+0x774`, modes `1/2/4/0x1000/0x2000/0x4000`, and MMIO-field values `0x600/0x700/0x800/0x300/0x400/0x500`. Old listing `0x806FFD9C` records a classifier/update path with values `1/2/4/0x40`. Preserve these as code anchors, not confirmed function entries: the AP1 base issue splits at least one routine incorrectly. The full status-string-to-mode chain and exact AC3/DTS/PCM numeric mapping remain unproven.

### CDROM classifier and packed-stream initializer

`DetectCdromStreamType` at `0x8074C868` contains the repeated `0x0B77` syncword/equal-spacing branch returning `0xAC3`; the other two signatures return `1` or `2`, and failure returns `-1`.

`InitializeCdromPackedStream` at `0x8074CB2C` is now named and commented in Ghidra. It clears the packing state, then normally invokes the classifier through the raw JAL at `0x8074CB7C`. A context word `*( *(uint32_t*)0x8000343C + 0x284 ) == 0x01050B44` bypasses the scan and selects result `1`; that context-field meaning is unknown.

| Classifier result | Stored byte at `0x80003718` | Action |
|---|---:|---|
| `1` | 1 | Set flag `0x80003719`; signature table `0x80002D64`; call `0x8074CEB8`, then converter `0x8074D538` |
| `2` | 2 | Set flag `0x8000371A`; signature table `0x80002D60`; call `0x8074CEB8`, then converter `0x8074D030` |
| `-1` | 0 | Call `0x8074CD90` |
| `0xAC3` | 3 | Call `0x8074CD90` |

The initializer returns the original classifier result, not the byte mode. Instruction proof includes the comparison at `0x8074CBBC..0x8074CBC4`, store at `0x8074CBE4`, failure store at `0x8074CBF8`, and dispatch calls at `0x8074CC28/CC30/CC50/CC58`.

The two converters show different word/bit packing behavior. Do not assign them DTS format names without signature-table or equivalent target proof. This CDROM classifier state is not automatically the audio-core enum, S/PDIF receiver state, or the inter-chip protocol.

The created Ghidra type `CdromPackedStreamState` is a 24-byte working layout for the state beginning at `0x80003704`: four-byte shift/count fields at offsets 0/4, four carry bytes at 8..11, four-byte cursor/count fields at 12/16, and mode/signature-A/signature-B/sync-loss bytes at 20..23. It has 12 fields; read-back confirmed size and offsets. Six labels identify the state, mode, flags and signature tables. The type is not an original source declaration and has not been applied over fabricated RAM bytes.

## STK container and checksum investigation

This section describes **static evidence from the existing Ghidra `/tools/stk.exe` program** (`x86:LE:32:default`, base `0x00400000`). Its exact original-file hash/revision has not been re-established against the three ZIP members; this identity check is a remaining gate before treating its implementation as the exact rev-8203R tool.

The module-name initializer at `0x0040BDD8` populates an array at `0x00502420` with names including ap1, cdrom, drv_other, wma and rom12. It has 19 named entries including romL/rom; this is a tool-side table, not yet a proven mapping for the target's 18 extracted slots. Function `0x00408238` selects names through module identifiers. The container object constructor chain includes `0x00408416 -> 0x00402E0E -> 0x00402CC2`.

### Additive word sum

`CalculateContainerWordSum` at `0x00401B56` is named, prototyped and commented in Ghidra:

`uint __cdecl CalculateContainerWordSum(void *context, byte *data, int byteLength)`.

For nonnegative length, it sums `floor(byteLength / 2)` unsigned little-endian 16-bit words into a wrapping 32-bit accumulator. X86 proof: `MOVZX EAX,word ptr [ESI+ECX*2]` at `0x00401B6B`, `ADD EBX,EAX` at `0x00401B70`, and return through EAX at `0x00401B76`. The first argument is unused. An odd final byte is ignored. This helper has no CRC polynomial, complement or final XOR; that does not exclude other integrity stages elsewhere.

### Two parser stages, not yet a reproduced checksum

- `0x00402CC2` reads the expected 32-bit value from input `+0x20`, computes the word sum starting at `+0x50`, and searches the effective end by subtracting trailing words. Its initial extent is derived from trailing `0xFF` trimming and 0x400-byte rounding. A match changes the length passed onward; absence of a match is not by itself an explicit rejection in this function.
- `0x00402C62` makes a copy and invokes `0x00401ED2`. That intermediate routine is unresolved; its decompile request was blocked, so no encryption/decryption/transform semantics are assigned to it.
- After that routine succeeds, `0x00402BCE` reads an expected value at buffer `+0x40`, sums from `+0x50`, and searches up to a 0x400-byte suffix before passing an extent to `0x00402950`.

Do not assume both expected values can be verified by summing the original raw dump in the same way: the second stage uses the intermediate buffer. Full target checksum reproduction was not completed. The source dump was retained separately as an immutable artifact with its canonical hash, not imported into Ghidra as executable code.

Remaining construction gates: identify the exact STK revision, resolve container/module records and load fields, understand the intermediate stage through an authorized evidence path, reproduce checksums on the preserved target, find the save/repack writer, perform a byte-exact no-change round trip, and only then prepare an intentional modified candidate. No modified firmware image or flash-ready candidate is claimed.

## Secondary BR23 / AC695N side

The board's secondary package is marked `AK24BP24230`. The UART log proves that running firmware contains AC695N/BR23 soundbox SDK paths and runtime messages, but the exact public SKU is still unresolved.

BR23 / AC695N uses JieLi's `pi32v2` architecture, not MIPS and not SCORE7.

### Public references / pinout

Working public pinout candidate for the secondary LQFP48 device:

- AC6951C datasheet V1.3 mirror: https://opendevices.ru/wp-content/uploads/2021/08/AC6951C-Datasheet-V1.3.pdf
- alternate rendered datasheet: https://manuals.plus/m/f01af517c489b4b9a7162705aa1868219f1b5cd871d130e08f0c0d601858c359

For AC6951C LQFP48:
- pin 23 = `USBDM`
- pin 24 = `USBDP`
- pin 25 = `PA10` (also has `SPDIF_IN_B`)
- pin 26 = `PA9` (also has `SPDIF_IN_A`)

The physical package marking on this board is `AK24BP24230`; the exact mapping of that marking to AC6951C is still unproven. Use pins 23/24 only after continuity/visual package orientation confirms that this board's secondary device matches the AC6951C LQFP48 pinout.

Boot/dump references:

- jl-uboot-tool: https://github.com/kagaimiq/jl-uboot-tool
- enter UBOOT / USB_KEY: https://github.com/kagaimiq/jl-uboot-tool/blob/main/docs/how-to-enter-uboot.md
- UBOOT model: https://github.com/kagaimiq/jl-uboot-tool/blob/main/docs/what-is-uboot.md
- JieLi architecture/chip notes: https://github.com/kagaimiq/jielie
- pi32v2 Ghidra processor: https://github.com/kagaimiq/ghidra-jieli

### Read-only dump plan

The next major acquisition task is to preserve this firmware before doing deeper two-chip reverse work.

1. Identify the secondary chip's own USB D+/D- route or accessible test pads. Do not reuse the four-pad SPHE USB footprint by assumption.
2. Confirm the chip enters BR23/AC695N-family Boot ROM / UBOOT, or determine the exact hardware action needed to reach ROM download mode.
3. Use a read-only BR23-capable dumper path. The open-source `jl-uboot-tool` explicitly lists BR23 / AC695N/AC635N as working and can read flash through its RAM loader.
4. Query the online flash/device ID first and derive the real flash size. The runtime log's `disk capacity 1024 KB` is a strong clue, not the dump-size authority.
5. Read the full flash at least twice, compare byte-for-byte and record SHA-256.
6. Only after verified preservation should any write/erase/update experiment be attempted.
7. Store the verified dump in this repository under `firmware/` using the proven chip family/part name.

### Safe first-session sequence

After identifying the secondary controller's own USB D+/D- pair:

1. power the board in the safest known configuration and share ground with the USB host;
2. do not feed an unknown USB VBUS rail into the board until its power topology is mapped;
3. enter BR23 ROM `UBOOT1.00` using the documented `USB_KEY` method or another non-destructive ROM-entry path;
4. start `jluboottool.py` and record the detected BR23/series and flash/device information;
5. determine flash size from the actual flash ID before selecting a dump length;
6. use only the `read <address> <length> <file>` command for the first session;
7. read the whole flash twice and compare the two files byte-for-byte and by SHA-256;
8. do not use `write`, `erase` or `erasechip` until a verified dump and recovery path exist.

The tool's own documentation marks BR23 / AC695N/AC635N as working and documents `read <address> <length> <file>` as the flash-dump command.

### Static-analysis path

After the dump exists:

- use a pi32v2 Ghidra processor implementation such as the open-source `ghidra-jieli` module;
- cross-check instruction decoding against the JieLi toolchain/objdump;
- use available AC695N/BR23 SDK source as a semantic oracle;
- recover board configuration, UART/service behavior, ALINK/I2S/SPDIF use, volume state and the SPHE inter-chip protocol.

### Current runtime anchors

`evidence/ac695n-boot-excerpt.log` is a curated excerpt from the UART output of the secondary-controller side.

It contains:
- `AC695N_soundbox_sdk_release_3.1.0_LineIn_IIS`
- BR23 / `board_ac695x_demo`
- `jl_soundbox_lihui`
- `audio_enc_init`
- `audio_dec_init`
- `audio_dac_init`
- `ALINK_SR = 44100`
- `spdif_dec_start`
- max/default volume configuration and `VOL_SAVE`

This strongly ties the secondary side to JieLi AC695N/BR23 software, but the exact public SKU behind `AK24BP24230`, its internal-flash dump path and the inter-chip protocol remain open.

## Firmware-control acceptance

Firmware work is not complete merely because dumps decompile or a checksum helper has been named.

We need to prove repeatable extraction/dump, coherent address and call models, repeatable packing/image construction, integrity rules, a safe flash/update method, rollback/recovery, and one intentional modification that survives reboot and produces the expected hardware behavior.

Only after that should the project implement new product behavior.
