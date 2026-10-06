# AUX resident / UART boundary checkpoint — 2026-10-06

Scope: firmware-only behavior recovery for the SPHE-side AUX ingress and the remaining control/status transport question. Canonical semantic authority is the saved Analysis project `sphe8202r_decoder_p25d80`. This file is a durable evidence checkpoint while the Analysis backend is unavailable; it does not replace the saved Analysis project.

## 1. AUX selector chain — CONFIRMED

Canonical Analysis now contains `InitializeAuxServiceParametersFromBank @ PM:01F2` in `aux-profile.bin`.

Instruction-backed chain:

1. CPU/runtime initializes decoder-service slot `0x32 = 5`.
2. AUX reads `DM:0032` once during service-parameter import.
3. The value is copied directly, with no remap, to `DM:07D0` (`g_aux_capture_pair_selector`).
4. `InitializeAuxResidentAudioChannels @ PM:031D` consumes that selector.
5. Selector `4` selects resident channel IDs `0x0E/0x0F`.
6. Any other stock selector observed here, including target selector `5`, selects resident channel IDs `0x10/0x11`.

No second selector transform is present in the accessible AUX profile.

## 2. AUX resident route command word — CONFIRMED

`DM:3C2A` is a resident route command/status word, not a PM pointer.

Native construction is:

`command = class | (slot << 4) | (route_index << 6)`

Recovered slot assignment:

- slot `0` -> target channel A, resident ID `0x10`;
- slot `1` -> target channel B, resident ID `0x11`;
- slot `2` -> alternate channel A, resident ID `0x0E`;
- slot `3` -> alternate channel B, resident ID `0x0F`.

Recovered command classes:

- class `0x800`: route-index submission; acknowledgement/busy state is `DM:3C2A & 0x2000`;
- class `0x400`: route-parameter submission paired with `DM:3C2B`; acknowledgement/busy state is `DM:3C2A & 0x1000`.

Observed route indices are `1, 2, 4, 5, 6, 7, 8`; index `8` is submitted twice in each route family. Do not reinterpret encoded words such as `0x840`, `0x880`, `0x900` as resident PM addresses.

## 3. AUX resident route parameter word — CONFIRMED behavior / UNKNOWN electrical meaning

`DM:3C2B` is the parameter word for class-`0x400` route submissions.

Both target and alternate capture-pair branches submit the same ordered values:

- `0xFD00`;
- `0x0800`;
- `0xF800`.

The target-vs-alternate distinction is therefore carried by the slot field in `DM:3C2A`, not by `DM:3C2B`.

Exact electrical/vendor meaning of the three parameter values remains **UNKNOWN**.

## 4. Resident consumer boundary — CONFIRMED implementation-proof limit

Canonical Analysis searches establish:

- AUX, PCM, AC-3 and DTS codec profiles contain no IO-space operations;
- `DM:3CA0/3CB0`, which hold the two AUX resident channel IDs, are written by AUX initialization but have no direct reader in the accessible AUX/PCM/AC-3/DTS/srvdsp corpus;
- `GetResidentAudioBlock @ PM:0DE1` forwards caller values through `DM:3F00/3F01/3F02`, submits command `0x63` through `DM:3F03`, and waits on `DM:3F04.bit0`; it does not translate channel IDs and performs no IO-space access;
- `srvdsp.bin` has initialized PM only at `PM:1800..1977` and local uninitialized DM state at `DM:0000..017F`;
- the wrapper's resident handoffs target PM addresses outside that initialized PM image.

Therefore the consumer that turns resident channel IDs / AUX route commands into the physical receiver behavior is in resident firmware not present in the available initialized PM image.

This is the current firmware proof boundary. Exact `DATA/BCLK/LRCLK <-> GPIO19/20/21` ownership/order remains board proof unless a new resident firmware artifact appears.

## 5. DSP resource / clock boundary — CONFIRMED unknown

`InitializeSrvdspImageUpload @ 0x8069ACC8` is now materialized in canonical Analysis. Native behavior programs the `0x4500..0x4506` DSP upload command family, emits staged 24-bit service-image words into DSP PM, writes the fixed DSP hardware-config key block `0x47A0..0x47AF`, and performs the service acknowledgement/start sequence.

The fixed `0x47A0..0x47AF` bytes are real DSP hardware configuration, but their vendor field meanings are not recovered. No field is proved to be a DSP PLL/divider/core-frequency selector.

Consequences:

- DSP core clock remains **UNKNOWN** at implementation proof;
- SoC input clock / SDRAM clock must not be promoted into DSP core clock;
- cycle/headroom cannot be converted into a trustworthy numeric budget without core-clock semantics and execution timing.

## 6. UART lead on AUX mode — LIKELY transport activity, framing UNKNOWN

A real new lead exists on the SPHE side:

- `ApplyExternalInputHardwareMode` mode `3` / AUX reaches `FUN_806FF5F4`;
- `FUN_806FF5F4` samples UART status `s6+0x904` RX-ready bit `0x2` and reads one byte from `s6+0x900` when ready;
- those addresses are the already-recovered SPHE UART DATA/STATUS registers.

However, the currently saved flow around the post-read trampoline is structurally stale. The observed low-level route enters the middle of the decoder/service-state action rooted at `0x806FFBC8` with index state forced to zero; the UART byte is not demonstrably consumed as a framed payload in that path.

Therefore:

- AUX mode is **CONFIRMED** to service UART RX activity;
- this is **not yet proof** that the UART is the JieLi <-> SPHE control/status transport;
- no byte framing, command IDs, checksum or message-direction contract is currently proved;
- the next Analysis step is to repair/trace the UART RX action route from the exact mode-3 call site and identify any state that is actually derived from the received byte.

## 7. Tooling state

During this pass the canonical Analysis backend stopped accepting connections after several successful narrow queries. A worker recovery attempt then failed internally. No alternate analysis engine was used after that point. Work continued only by recording already-obtained canonical Analysis evidence in this checkpoint.
