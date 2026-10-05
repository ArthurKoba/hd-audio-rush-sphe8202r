# DSP profile initialization and program-window evidence

Date: 2026-10-01. Repository baseline: `0cd3c2350964dc246e0c50df7aafa9c6c91907f0`.
Canonical analysis project: `sphe8202r_decoder_p25d80`.

This is a reproducible evidence record for the current audio route, not an additional project plan. It supplements `docs/analyze-status.md` and the audio/DSP section of `docs/firmware.md`. No firmware bytes, hardware state or host utility implementation were changed in this pass.

## Validation and corrections

The evidence level is source/implementation analysis. No execution, board or integration acceptance is claimed.

The earlier conversational estimate of 85–87% audio completion is withdrawn as a measured coverage claim: there is no enumerated, validated denominator for the whole audio route. The historical 5.04% non-default-name metric must not be mixed with the stricter API custom-name metric below.

Two earlier interpretations are specifically corrected:

- DSP profile-table index 8 is not STK module slot 8. The profile table uses the first set bit of a decoder-state mask; the zero-mask fallback is index 8. STK container slots are a separate namespace.
- `0x8070294C` and `0x8070296C` only query descriptor-identity predicates. They do not choose a new profile. An inbound route therefore cannot identify a codec merely by reaching either wrapper.

## 1. Initial profile table: source and destination proved

The complete low-level action at `rom12-runtime.bin:0x88000240..0x8800029F` copies 32-bit words from:

- source `[0x880122E0, 0x88012C2C)`;
- destination `[0x80002000, 0x8000294C)`;
- length `0x94C` bytes.

It then clears `[0x80002950, 0x8000A8B0)`. The four bytes at `0x8000294C..0x8000294F` are not touched by this action; no reason for that gap is inferred.

Consequently the profile table at RAM `0x80002264` has its initial source at:

`0x880122E0 + (0x80002264 - 0x80002000) = 0x88012544`.

The successful 160-byte read at `0x88012538` contains all 32 table entries at byte offsets 12..139. A later redundant read was declined; no alternate transport was used to repeat it. The already-returned bytes are sufficient for this table.

The table has 32 entries and 10 distinct descriptor pointers:

| Index / indices | Initial descriptor pointer |
|---|---|
| 0 | `0x807A0D4C` |
| 1, 2, 3, 5, 7, 8, 10, 11, 12, 19, 20, 21, 22, 23, 24, 25, 29, 30, 31 | `0x807B320C` |
| 4, 9 | `0x807AD2C0` |
| 6, 13 | `0x80792F7C` |
| 14 | `0x807BCCFC` |
| 15 | `0x807A9170` |
| 16 | `0x807A5C28` |
| 17 | `0x807973C4` |
| 18 | `0x807B55DC` |
| 26, 27, 28 | `0x807BEF4C` |

The selectors at AP1 `0x80700484` and `0x807004E4` read the mask at `gp+0x698`, use the lowest set bit in positions 0..31, and fall back to index 8 for zero. AP1 `0x80700410` uses the same selection scheme for the load route. For a multi-bit mask, this is priority selection, not a combination of multiple profiles.

These are initialization values, not a live RAM capture. Later writes through a calculated pointer are not excluded by this evidence.

## 2. Descriptor fields and audio-state associations

The descriptor layout used by AP1's logical load route is:

| Offset | Representation | Evidence-backed role |
|---|---|---|
| `+0` | little-endian 32-bit pointer | Packed source passed to the runtime transfer route |
| `+4` | little-endian 16-bit A | First page-boundary increment; saved at `gp+0x540` |
| `+6` | little-endian 16-bit B | Saved at `gp+0x544`; complete downstream meaning remains open |
| `+8` | little-endian 16-bit C | Second page-boundary increment and program-size capacity check; saved at `gp+0x542` |
| `+10..+11` | two bytes | Zero in the sampled descriptors; meaning not assigned |

Combining the initial table with the already documented input decoder-state contracts gives:

| Input route | State | Index | Descriptor | Packed source | A | B | C |
|---|---|---:|---|---|---:|---:|---:|
| PCM input | `0x8000` | 15 | `0x807A9170` | `0x807A5C34` | 25 | 174 | 9 |
| AC-3 input | `0x10000` | 16 | `0x807A5C28` | `0x807A0D58` | 33 | 173 | 48 |
| DTS input | `0x20000` | 17 | `0x807973C4` | `0x80792F88` | 32 | 200 | 49 |
| AUX route | `0x40000` | 18 | `0x807B55DC` | `0x807B3218` | 23 | 95 | 9 |
| Zero-mask fallback / index-8 entry | `0` | 8 | `0x807B320C` | `0x807AD2CC` | 41 | 144 | 11 |

The input-state names come from the existing source/decoder contracts in `docs/firmware.md`; they are not inferred from descriptor sizes.

The previously inspected profile A is `0x80792F7C`, with source `0x8078EC9C` and fields 31/196/30. It is initially installed at indices 6 and 13, not at index 8.

The separate predicate target `0x8079B9A0` has source `0x807973D0` and fields 32/200/49. It is absent from all 32 initialization entries. Those fields equal the sampled DTS-input descriptor's fields, but the pointer and packed source are different. They must not be treated as the same profile. Later runtime replacement of table entries remains possible and unproven.

The first 128 compressed bytes at the PCM source were also checked with raw-DEFLATE decoding. They produce a 231-byte prefix; end-of-stream was NOT reached. This supports the packed-source format only. It is not complete image validation or DSP execution evidence.

## 3. Placement and program-window sizes

The complete logical load route is AP1 `0x807002FC..0x8070040F`. Some stored action boundaries cover only fragments; the low-level action view is authoritative.

The route computes page bases:

- `0xF8`;
- `0xF8 + A`;
- `0xF8 + A + C`.

Entry `0x807002AC` reads the last two arguments from stack offsets `+0x10/+0x14`, then stores bases in service registers `s6+0x4B0/+0x4B8/+0x4B4` and mirrors them at `gp+0x17AC/+0x17AE/+0x17B0`. Treating `0x807002B4` alone as the full entry misses the stack arguments.

The transfer destination is `0xA0000000 + (u16(gp+0x17AC) << 10)`. The separate runtime writer at `0x88001358` uses the third mirrored base and a three-byte stride for DSP service words. These address calculations establish software placement; they do not identify physical internal PM/DM sizes.

The newly documented action `ConfigureDspProgramWindow` at runtime `0x880013C8..0x880014B3` establishes the previously unresolved origin of `gp+0x71E`:

| Exact decoder state(s) | Configured byte count | Count divided by 3 |
|---|---:|---:|
| PCM `0x8000`, AUX `0x40000`, state `0x10` | `0x3000` = 12,288 | 4,096 |
| DTS `0x20000`, states `0x40` and `0x2000` | `0x3C00` = 15,360 | 5,120 |
| AC-3 `0x10000` and ordinary fallback | `0x2400` = 9,216 | 3,072 |
| Packed-media state `0x200` | Starts at `0x6C00`; falls back to `0x2400` if its selected-profile capacity is smaller | Conditional |

Except for state `0x20`, it divides the value by three through the unsigned quotient helper at `drv_other.bin:0x8077CF88` and writes the quotient into DSP service slot 1 through `0x88001338`.

The separate AP1 capacity check at `0x80700168` compares the selected count with `C << 10`, adding three capacity units only for PCM `0x8000` and AUX `0x40000`. The sampled PCM/AUX descriptors both have C=9, so the special capacity becomes `(9+3)*1024 = 12,288`, matching their configured count.

This is a software program-window contract. Do NOT report these numbers as total DSP RAM, free DSP RAM, computational throughput, samples of delay, or space available for custom filters. Resident program/data ownership, clocks and audio scheduling are still unresolved. The precise relationship between this window and the separate `srvdsp.bin` service image remains open.

## 4. Profile query use and service-state guard

AP1 `0x80702934` reads the raw 32-bit word at `s6+0x4D4` and returns it unchanged.

Route `0x806D2ED4` proceeds only when that word is 1. It then queries profile A, and, if A does not match, queries the second descriptor identity. On either match it obtains a service-data pointer through `0x807028F0`, examines bytes `+0x15..+0x17`, and reaches `0x807016EC` only for the accepted small value. The exact semantic name of that extracted field is not yet proved; do not label it a codec, channel count, or sample rate from this branch alone.

The reached reconfiguration route performs a service-state preparation, delay, audio action 9, and a DSP control-state transition. Recover its complete remainder before assigning an end-to-end effect name.

## 5. Saved analysis state and coverage

Saved in the canonical project:

- `InitializeRuntimeGlobalData` at runtime `0x88000240`;
- `ConfigureDspProgramWindow` at runtime `0x880013C8`;
- `MatchesDspProfileA` at AP1 `0x80700484`;
- `ReadAudioServiceStatusWord` at AP1 `0x80702934`;
- complete-route annotation at AP1 `0x807002FC`.

Both AP1 and runtime programs were explicitly saved. The runtime base is `0x88000000`. `srvdsp.bin` opens and contains 1,128 bytes, but its existing inspection record still carries provisional MIPS metadata and has zero action nodes. That does not mean the DSP image is empty; it must not be processed as an ordinary MIPS program.

Fresh API custom-name coverage across the four established CPU modules:

| Module | Custom names | All action nodes |
|---|---:|---:|
| AP1 | 116 | 3,828 |
| drv_other | 31 | 177 |
| wma | 5 | 51 |
| cdrom | 5 | 93 |
| Total | 157 | 4,149 |

Metric: `search_actions_enhanced(has_custom_name=true)` numerator divided by the program action inventory. Result: **3.78%**. Runtime and DSP-image records are excluded from this longstanding four-module denominator. Inventory growth is not itself recovered behavior.

## Remaining evidence boundary

Continue along the same route: determine later writes to the profile table, service-image placement, and how GM5/downmix parameters reach the actual DSP processing actions. Preserve the distinction between profile data, generic transfer machinery and the audio algorithm.

UART execution evidence, physical six-channel routing, exact DSP resources and the secondary-controller contract remain open. USB work remains limited to evidence for computer-facing device/dual-role capability after the active audio boundary; host/removable-media feature work is out of scope.


## 6. Complete packed profile images and service-parameter route — 2026-10-01

Independent raw-DEFLATE decoding of the descriptor sources produced complete profile images:

| Profile | Packed source | Decoded bytes |
|---|---|---:|
| PCM | `0x807A5C34` | 25,052 |
| AC-3 | `0x807A0D58` | 33,770 |
| DTS | `0x80792F88` | 30,536 |
| AUX | `0x807B3218` | 17,468 |
| zero-mask fallback | `0x807AD2CC` | 41,000 |
| profile A | `0x8078EC9C` | 30,296 |
| profile B | `0x807973D0` | 31,466 |

The decoded PCM/AC-3/DTS/AUX images start with coherent 24-bit DSP vector/code words. None contains `srvdsp.bin` as an identical embedded byte sequence; the longest common 24-bit-word run found against `srvdsp.bin` was only four words. Therefore `srvdsp.bin` must remain a separate specialized image/context until its target ownership is proved.

The descriptor/load route establishes this software layout:

- profile image base = `0xF8`;
- second boundary = `0xF8 + A`;
- 24-bit service-parameter base = `0xF8 + A + C`.

The transfer decoder writes the unpacked profile from the first base. The runtime 24-bit parameter writer uses the third base and a three-byte stride. Field B is saved but has no direct reader in the currently loaded MIPS modules; its meaning remains UNKNOWN.

### Decoder-service parameter block

The resolver at AP1 `0x806D1F70` is broader than audio. Runtime initialization clears 128 24-bit service words and then fills fixed and resolver-derived entries. Because service slot `0x0B` depends on DVD region state, the block must not be named an audio-only parameter table.

Confirmed audio entries:

| Service slot | Evidence-backed value |
|---|---|
| `0x07` | effective master-volume coefficient derived from master level, mute flag and runtime gain table |
| `0x09` | KEY selection encoding; runtime KEY offset is `selection - 8`, clamped by its update routes to -6..+6 |
| `0x0D` | SUBWOOFER speaker state |
| `0x0E` | S/PDIF output selection state |
| `0x1B` | packed speaker-topology word |
| `0x20` | decoder/service state influenced by downsample/profile reconfiguration; exact semantic name remains open |
| `0x21` | effective DOWNMIX mode: OFF=6, STEREO=7, LT/RT=8, VSS=9 |
| `0x23` | full GM5 packed state |

Do not confuse service slot `0x1B` with persistent control state-slot `0x1B`; they are different namespaces.

### GM5 and KEY

GM5 control descriptor `0x9E` has persistent state-slot `0x22`. Selection indices map to:
- 2 -> MODE 1 -> packed state `0x137330`;
- 3 -> MODE 2 -> packed state `0x127330`;
- 4 -> OFF -> packed state `0x037330`.

The resulting packed word is written to service slot `0x23`.

KEY control `0x5C` has persistent state-slot `0x0F`. Runtime initialization sets `key_offset = selection - 8`; the increment/decrement routes clamp it to -6..+6. The service resolver returns `key_offset + 8`, so service slot `0x09` receives the encoded current KEY selection.

### DIGITAL controls and speaker delays

The corrected translation pointer table base is `0x806DCD88`. Direct pointer lookup confirms:
- `0xF9` -> `OP MODE`;
- `0xFA` -> `LINE OUT`;
- `0xFB` -> `RF REMOD`;
- `0x6A` -> `DYNAMIC RANGE`;
- `0xFC` -> `DUAL MONO`;
- `0x31` -> `STEREO`;
- `0x2F` -> `MONO L`;
- `0x30` -> `MONO R`;
- `0xFD` -> `MIX MONO`;
- `0xD1` -> `CENTER DELAY`;
- `0xD2` -> `REAR DELAY`.

Persistent control-state mapping:
- OP MODE `0xF9` -> state-slot `0x1A`;
- DYNAMIC RANGE `0x6A` -> state-slot `0x1B`;
- DUAL MONO `0xFC` -> state-slot `0x1C`;
- CENTER DELAY `0xD1` -> state-slot `0x18`;
- REAR DELAY `0xD2` -> state-slot `0x19`.

Implementation routes:
- OP MODE LINE OUT / RF REMOD select generic audio-action-1 selectors `0x20` / `0x10`;
- DYNAMIC RANGE working state is initialized as `persistent_selection - 2`; when nonzero the apply route forms `state * 0x2020 - 0x101` and sends it through audio action 1 with selector `0x80`, while zero sends coefficient 0;
- DUAL MONO sends selectors `0x90/0x91/0x92/0x93` for STEREO/MONO L/MONO R/MIX MONO through audio action 1;
- CENTER DELAY uses audio action `0x0B`, kind 1, value `selection - 2`;
- REAR DELAY uses audio action `0x0B`, kind 2, value `selection * 3 - 6`.

These are implementation-level control/service contracts. Physical channel timing and audible behavior remain separate board/execution acceptance.




## 7. Direct DSP-side consumption of audio controls — 2026-10-01

The decoded codec profiles provide direct implementation proof that the MIPS/runtime service vector is consumed by the DSP code itself.

### GM5

Direct immediate reads:
- PCM reads `DM($0023)`;
- AC-3 reads `DM($0023)`;
- AUX reads `DM($0023)`.

Each profile splits the packed GM5 word into multiple working fields. Those fields are later read in active processing routes, so the configuration is not dead state.

The first working field acts as GM5 enable: MODE1 and MODE2 enable the spatial route while OFF disables it. A second field distinguishes MODE2 from MODE1. The coefficient initialization is repeated across PCM, AC-3 and AUX profiles.

Observed Q23-style coefficient values include approximately:
- `0.353553`;
- `0.176777`;
- `0.25`;
- `0.5`;
- `0.4`;
- `0.12`;
- `0.585786`;
- `0.414214`.

The square-root-of-two-related values and their later use in multiply-accumulate loops establish GM5 as a fixed-point spatial matrix/upmix path rather than a simple gain preset. MODE2 initializes additional coefficient pairs and therefore selects a richer matrix than MODE1.

### AC-3 DOWNMIX

AC-3 directly reads service slot `DM($0021)` and compares it against values 6, 7, 8 and 9. The resulting working state is:

| User mode | Service value | Internal matrix state `DM(0x223)` | VSS state `DM(0x29B)` |
|---|---:|---:|---:|
| OFF | 6 | 7 | 0 |
| STEREO | 7 | 2 | 0 |
| LT/RT | 8 | 0 | 0 |
| VSS | 9 | 2 | 2 |

Before this mapper runs, `L0` is explicitly zero, so the zero values above are not unknown inherited state.

The VSS state is consumed in additional MAC/buffer routes. When nonzero, AC-3 performs extra scaling and buffer-processing loops that are skipped by OFF/STEREO/LT-RT. The matrix state `DM(0x223)` is independently read by multiple later routes and therefore acts as the core downmix/output-mode selector.

## 8. DSP resource envelope and resident-backend boundary

Decoded profile sizes and active flow:

| Profile | Decoded bytes | 24-bit words | Approximate highest live flow target |
|---|---:|---:|---:|
| PCM | 25,052 | 8,350 | `0x2090` |
| AC-3 | 33,770 | 11,256 | `0x2BF3` |
| DTS | 30,536 | 10,178 | `0x27B2` |
| AUX | 17,468 | 5,822 | `0x16BA` |
| fallback | 41,000 | 13,666 | `0x355F` |

All inspected codec profiles use immediate DM addresses through `0x3FFD`. No PMOVLAY/DMOVLAY writes were found. This proves a flat program envelope of at least 13,666 24-bit words and a heavily used 14-bit DM address range. A complete `0x0000..0x3FFF` 16K-word PM/DM-style envelope is **LIKELY**, not yet CONFIRMED.

No direct ADSP-style `IO(x)` operations were found in PCM, AC-3, DTS, AUX or fallback profiles. Instead all profiles use common high-DM areas.

Two high-DM command/status groups recur across all profiles:
- `0x3F00..0x3F03`: repeated parameter writes;
- `0x3F04`: repeated status/control reads;
- `0x3F10..0x3F13`: another repeated write group;
- `0x3F14`: its status/control read.

A second common area contains repeating blocks with a `0x10` stride, including `0x3C20/30/40/50/60/70/80/90...`. Profiles write base/state/config fields at consistent offsets inside these blocks. The number of blocks exceeds the six physical analog outputs, so this area is a generic multi-stream/resident-backend descriptor contract, not a one-register-per-DAC map.

The codec profiles therefore terminate at a resident stream/DMA/service boundary. Exact `stream N -> FR/FL/SR/SL/C/SUB` ownership requires resident-service evidence or board execution proof.

## 9. Processor-model cleanup boundary

The existing canonical program `/modules_probe_mipsle/srvdsp.bin` is currently registered as `MIPS:LE:32:default` and has zero action nodes. That language assignment is wrong for the file and must not be used for DSP semantics.

The target instruction stream is 24-bit and ADSP-21xx-compatible at the encoding level used so far. A clean future processor definition must support separate PM/DM concepts and preserve the target-specific 24-bit service/data behavior instead of assuming every ordinary ADSP-218x data-width detail applies unchanged.

Known validation anchors:
- first `srvdsp.bin` word `0x19820F` at PM base `0x1800` -> unconditional jump to `0x1820`;
- `0x0A000F` -> unconditional return;
- `0x80023A` -> read `DM($0023)` into AR;
- `0x80021A` -> read `DM($0021)` into AR;
- `0x400064` -> load constant 6 into AY0.

The analysis backend can import raw files with an explicit language ID only when that processor model is already registered. Plausible ADSP language IDs failed in dry-run and no ready upstream ADSP-21xx language module was found. The backend exposes no processor-module installation tool.

Deferred migration plan:
1. preserve all current MIPS and probe programs;
2. build a separate target-specific 24-bit processor module;
3. validate the anchors above on a temporary `srvdsp.bin` copy;
4. import new codec-profile copies under a dedicated DSP project folder;
5. use PM base `0x1800` for `srvdsp.bin`; validate codec-profile base independently, with current flow evidence consistent with word-address zero;
6. only after low-level operation parity is proved, create DSP action nodes, links and semantic annotations;
7. mark the old MIPS probe copy as legacy but do not delete it until the new programs are stable.
