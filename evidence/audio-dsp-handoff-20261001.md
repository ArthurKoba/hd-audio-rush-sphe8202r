# Audio/DSP handoff — 2026-10-01

## Current decision boundary

Canonical analysis project: `sphe8202r_decoder_p25d80`.

Target audio behavior estimate: **94–96% at implementation-proof level**. This is an approximate denominator-specific engineering estimate, not action-node coverage and not board acceptance.

Strict semantic-name metric for the four established CPU modules remains **157/4149 = 3.78%**.

The ordinary MIPS-side audio/control path is sufficiently recovered that the remaining audio uncertainty is concentrated below the codec-profile DSP algorithms:
- resident stream/DMA/backend ownership;
- exact backend-stream-to-six-DAC-lane mapping;
- exact DSP clock/free-cycle budget;
- board/execution acceptance.

The user has explicitly deferred installation of the custom DSP processor definition until later. Do not spend the next session rebuilding it unless requested. With that work deferred, the next planned product-analysis lane is the bounded USB device/dual-role capability check; after USB, continue with the secondary-controller/Bluetooth contract.

## Do not redo

Do not restart these paths:
- S/PDIF OFF/RAW/PCM control recovery;
- AUX/S/PDIF-IN source transition;
- master volume/mute;
- speaker topology and delays;
- DOWNMIX control semantics;
- GM5 control semantics;
- KEY;
- OP MODE / DYNAMIC RANGE / DUAL MONO;
- profile-table initialization;
- PCM/AC-3/DTS/AUX profile descriptor association;
- raw-DEFLATE profile decoding;
- DSP-side proof that GM5/DOWNMIX reach active profile code.

The authoritative detailed evidence is in:
- `evidence/dsp-profile-map-20261001.md`;
- `evidence/analysis-runtime-failures-20261001.md`;
- `docs/firmware.md`;
- `docs/analyze-status.md`.

## CPU/runtime audio chain

Central hardware/service dispatcher: `DispatchAudioHardwareAction`.

Confirmed user-facing families include:
- DOWNMIX;
- effective master volume;
- KEY;
- S/PDIF output mode;
- packed speaker topology;
- CENTER/REAR delay;
- GM5 packed control;
- digital controls.

Runtime builds a broader 128-word decoder-service parameter block. It is not audio-only; at least one slot is tied to DVD region state. Proven audio entries include:
- `0x07`: effective volume coefficient;
- `0x09`: KEY encoding;
- `0x0D`: SUBWOOFER state;
- `0x0E`: S/PDIF output state;
- `0x1B`: speaker topology word;
- `0x20`: service/profile state, exact semantic name still open;
- `0x21`: DOWNMIX;
- `0x23`: GM5 packed state.

Profile selection uses the first set bit of decoder state. Zero mask falls back to profile-table index 8. This table is unrelated to STK module-slot numbering.

## Decoder profiles

Initial state/profile association:
- PCM `0x8000` -> descriptor `0x807A9170` -> packed source `0x807A5C34`;
- AC-3 `0x10000` -> `0x807A5C28` -> `0x807A0D58`;
- DTS `0x20000` -> `0x807973C4` -> `0x80792F88`;
- AUX `0x40000` -> `0x807B55DC` -> `0x807B3218`;
- zero-mask fallback -> `0x807B320C` -> `0x807AD2CC`.

Complete raw-DEFLATE decoding produced:
- PCM: 25,052 bytes / 8,350 24-bit words;
- AC-3: 33,770 / 11,256;
- DTS: 30,536 / 10,178;
- AUX: 17,468 / 5,822;
- fallback: 41,000 / 13,666;
- profile A: 30,296 bytes;
- profile B: 31,466 bytes.

Descriptor fields:
- `+0`: packed source pointer;
- `+4`: field A, used in first placement boundary;
- `+6`: field B, saved but no direct MIPS reader found; semantic meaning UNKNOWN;
- `+8`: field C, used in second placement/capacity logic.

Placement route:
- base0 = `0xF8`;
- base1 = `0xF8 + A`;
- base2 = `0xF8 + A + C`;
- the 24-bit service writer uses the third base with a three-byte stride.

## DOWNMIX DSP behavior

MIPS/service mapping:
- OFF -> 6;
- STEREO -> 7;
- LT/RT -> 8;
- VSS -> 9.

AC-3 reads `DM($0021)` and maps:
- OFF -> matrix state 7, VSS state 0;
- STEREO -> matrix state 2, VSS state 0;
- LT/RT -> matrix state 0, VSS state 0;
- VSS -> matrix state 2, VSS state 2.

The VSS state is later read as an enable/gate for extra MAC/buffer routes. Matrix state is separately consumed by multiple output/matrix paths.

## GM5 DSP behavior

Persistent GM5 selection:
- MODE1 -> packed `0x137330`;
- MODE2 -> `0x127330`;
- OFF -> `0x037330`.

PCM, AC-3 and AUX directly read service slot `DM($0023)`. The packed value is split into multiple working fields and those fields are consumed later.

GM5 is a fixed-point spatial matrix/upmix path. Repeated coefficient families across profiles include approximate Q23 values around:
- 0.353553;
- 0.176777;
- 0.25;
- 0.5;
- 0.4;
- 0.12;
- 0.585786;
- 0.414214.

The square-root-of-two relationships and pairwise multiply-accumulate use are strong algorithmic evidence. MODE2 uses additional coefficient pairs compared with MODE1.

## Other closed audio controls

KEY:
- control `0x5C`;
- persistent state-slot `0x0F`;
- runtime offset `selection-8`, clamped -6..+6;
- service slot `0x09` receives encoded current selection.

DYNAMIC RANGE:
- control `0x6A`;
- persistent state-slot `0x1B`;
- working state `selection-2`;
- nonzero apply coefficient `state*0x2020-0x101`;
- sent through audio action 1 selector `0x80`.

OP MODE:
- `0xFA LINE OUT` -> selector `0x20`;
- `0xFB RF REMOD` -> selector `0x10`.

DUAL MONO:
- STEREO -> `0x90`;
- MONO L -> `0x91`;
- MONO R -> `0x92`;
- MIX MONO -> `0x93`.

Speaker delays:
- CENTER DELAY control `0xD1`, state-slot `0x18`, action `0x0B` kind 1, `selection-2`;
- REAR DELAY control `0xD2`, state-slot `0x19`, action `0x0B` kind 2, `selection*3-6`.

## DSP resource evidence

Largest proven active profile: fallback, 13,666 24-bit program words, live flow to about `0x355F`.

All major profiles use immediate DM addresses through `0x3FFD`. No PMOVLAY/DMOVLAY writes were observed.

Interpretation:
- at least ~13.7K 24-bit program words are definitely usable by stock profiles;
- a full 16K-word 14-bit PM/DM envelope is likely but not yet proved as the exact hardware capacity;
- the exact DSP clock and free-cycle budget are UNKNOWN;
- do not promise a number of PEQ sections, crossover orders, FIR taps or delay samples until execution/resource measurements exist.

## Resident multi-stream/backend boundary

No direct `IO(x)` operations were found in the major codec profiles.

Common high-DM areas:
- `0x3F00..0x3F03`: repeated writes;
- `0x3F04`: repeated status/control reads;
- `0x3F10..0x3F13`: another repeated write group;
- `0x3F14`: status/control read.
- repeating `0x3C20/30/40/50/60/70/80/90...` blocks receive base/state/config fields with a consistent stride.

This is a shared resident stream/DMA/service contract. It is not a simple six-register DAC map.

Reference-board evidence proves the SPHE8202R silicon has dedicated analog outputs for FR/FL/SR/SL/SUB/C. Target-board continuity and exact backend stream ownership remain board proof.

## DSP processor-definition status

Existing canonical probe:
`/modules_probe_mipsle/srvdsp.bin`

Current language:
`MIPS:LE:32:default`

This is known-wrong. Keep it only as a preserved legacy probe.

The backend raw loader can use an explicit language ID if the language is already registered. No ready ADSP-21xx/218x language was found in the installed/upstream language set; plausible IDs failed dry-run.

The available MCP surface has no processor-module installation operation. The analysis-MCP issue-205 support only exposes decoded low-level text for already installed custom processor definitions; it is not an installer.

Deferred correct migration:
1. create a separate target-specific 24-bit ADSP-compatible processor module;
2. preserve the existing MIPS probe;
3. install the processor module into the analysis runtime and restart the service;
4. validate `0x19820F -> JUMP $1820`, `0x0A000F -> RTS`, `0x80023A -> AR=DM($0023)`, `0x80021A -> AR=DM($0021)`;
5. import new DSP copies into a dedicated project folder;
6. use PM base `0x1800` for `srvdsp.bin`; validate codec-profile base separately;
7. only then create DSP action boundaries, action links and semantic annotations.

The user explicitly deferred this processor-module work for a later session.

## Analysis-runtime incidents to remember

Do not confuse these incident classes:
- project visible/healthy but open fails -> one explicit close/open cycle fixed it;
- active project loses an individual program handle -> reopen only that program;
- runtime can reopen with missing local action/index state -> narrow low-level decode restores local evidence;
- external pre-tool filtering intermittently rejects read-only queries and mutations;
- composed calls can partially execute;
- GitHub connector can drop transport independently;
- large orchestration scripts can fail internally even when smaller equivalent steps succeed.

During the final handoff pass, new `set_comment`, `save_program`, `save_all_programs`, `close_program(save=true)` and several program-load operations were rejected before backend execution. Bookmark writes were inconsistent: bookmarks at `drv_other:0x807768D4` and `0x8077C29C` reported success in the live session, but explicit save was blocked, so their persistence is not guaranteed. **Repository evidence is authoritative for the latest findings.**

## Exact continuation order

If DSP processor-module work remains deferred:

1. Do not reopen already closed audio-control questions.
2. Treat the audio route as 94–96% implementation proof with the remaining gap at resident-backend/resource/board proof.
3. Start the bounded USB architecture check:
   - establish whether the SPHE controller has computer-facing device or dual-role capability;
   - distinguish silicon capability from this board's current host-only firmware;
   - stop deep USB work if device/dual-role is unsupported;
   - do not return to removable-media behavior except where needed for controller ownership.
4. After USB, recover the SPHE <-> secondary-controller contract and Bluetooth control route.
5. Return to the custom DSP processor module when requested, using the migration checklist above.

If audio is resumed first, only work below the resident backend boundary or on execution/board proof; do not repeat the control/profile/DSP-matrix work already recorded here.
