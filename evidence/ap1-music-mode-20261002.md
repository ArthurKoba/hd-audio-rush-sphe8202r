# AP1 MUSIC MODE control contract — 2026-10-02

## Scope and recovery point

Repository baseline: `1351bdd7d3cf8e761e0f1887deaa56670be39b9c`.
Canonical Analysis project: `ghp_8847e7bcc4fa1ca3b69ff2f5`; program `/modules_mipsle/ap1.bin`, base `0x8067B800`.

This checkpoint preserves the previously uncommitted correction. It supersedes the seven-fixed-EQ-curves description in the 2026-10-01 handoff. No firmware bytes are modified. Validation is CPU-side implementation proof, not execution/board proof or complete DSP algorithm recovery.

## Confirmed control mapping

The four 11-byte MUSIC MODE records at `0x8070B35C` separate distinct pages:
- page 0: SRND; OFF / CONCERT / CHURCH / PASSIVE / WIDE / LIVE;
- page 1: EQ; STANDARD / CLASSIC / ROCK / JAZZ / POP / USER;
- page 2: BAND;
- page 3: KEY.

Translation pointers use the established table at `0x806DCD88`. Page-1 option IDs 195..200 map to STANDARD through USER. EQ selections 2..6 choose five fixed seven-byte records; selection 7 chooses the runtime USER curve at `gp+0x10..0x16`. The fixed bank begins at `0x8070B388`, not `0x8070B37A`. The earlier address is the arithmetic origin `bank - 2*7`, and its first 14 bytes overlap the preceding page table.

Fixed curves in displayed dB units (`stored_code - 13`):
- STANDARD: [0,0,0,0,0,0,0]
- CLASSIC: [0,0,0,0,0,-3,-10]
- ROCK: [8,8,2,-2,-6,-2,10]
- JAZZ: [8,6,3,-4,5,-4,10]
- POP: [2,8,-6,0,8,2,-2]

The displayed scale is confirmed; an actual measured frequency response and band center frequencies are not established here.

## Apply route

`ApplySevenBandEqCurve` at `0x806E8ED0` calls `ApplySevenBandEqParameters` at `0x80702D64` with count 7, then `ApplySurroundModeIndex` at `0x80702D0C` with mode 0.

The raw parameter action accepts `(count & 0xff) < 8`. Each byte is passed as `(index + 7, value)` through `0x807028D0` to runtime writer `0x88001358`. It then writes 1 to `s6+0x130`, polls while that register reads zero, and sends `DispatchAudioHardwareAction(8,0x10,0)`. Count zero skips payload writes but still performs handshake/dispatch; count >=8 returns zero without those side effects. The individual payload writes have no observed result check in this action.

Raw evidence refreshed in this session:
- `ap1:0x807028D8`, bytes `d6 04 00 0e`, word `0x0E0004D6`, encodes JAL `0x88001358`;
- `ap1:0x80702DE4`, word `0x0C1C0A34`, encodes JAL `0x807028D0`;
- `ap1:0x80702DB0`, word `0x0C1BFF47`, encodes JAL `0x806FFD1C`;
- `ap1:0x80702DF8`, word `0x081C0B66`, encodes J `0x80702D98`.

The saved high-level view followed several destinations displaced by +0x800. Do not use those stored destinations as DSP-consumer evidence. No broad metadata repair is claimed. One exact link was corrected as recorded below; the remaining EQ links still need reconciliation.

## State interaction

`gp+0x0C` stores SRND selection; `gp+0x0D` stores EQ selection. SRND mode is selection minus 2, sent as hardware action 5 / command family `0x0700|mode`. The MUSIC MODE apply route makes non-OFF SRND and non-STANDARD EQ mutually exclusive. This is a factory control policy, not proof that the silicon cannot combine them. It must not be conflated with the distinct GM5 control.

## Parameter-bank contract

Native runtime analysis now confirms `SetDspParameterWord24` at `0x88001358` and `GetDspParameterWord24` at `0x8800138C`.

Both compute `0xA0000000 + (u16[gp+0x17B0]<<10) + index*3` with 32-bit arithmetic. Writer stores low byte at +2, high byte at +0, middle byte at +1; reader assembles the three bytes in big-endian order and zero-extends to 32 bits. There is no local index bound, handshake or atomic three-byte commit in either action. Initialization uses 128 entries, but that is a caller contract, not an enforced writer limit. No atomic hardware visibility guarantee is inferred.

Initialization and later EQ payload use the same writer. Thus an index alone is not a permanent semantic identity. The DSP consumption/copy timing and ownership of this reused bank remain to be established.

## Audio-service wait contract

`WaitForAudioServiceConditions` at `0x88001C78..0x88001CCF` has 22/22 decoded native operations and a matching high-level behavior view.

Inputs: a0 enables command-flag checking; a1 enables status-word checking; a2 is expected status; a3 is an unsigned maximum poll count. A successful poll satisfies both enabled conditions: `(u32[s6+0x4C0] & 0x8000) != 0` and/or `u32[s6+0x4D4] == a2`. Return is 1 for success and 0 for zero budget or exhausted polls. There are no command writes, delay calls or timer reads here. The AP1 dispatcher passes `(1,0,0,100000)`; 100000 is a poll limit, not a demonstrated time unit or physical-effect guarantee.

## Persistent Analysis changes in this pass

Runtime program `/runtime/rom12-runtime.bin`:
- native decode added for exactly 112 bytes at `0x88001358..0x880013C7` and 88 bytes at `0x88001C78..0x88001CCF`;
- created SetDspParameterWord24 (52-byte body), GetDspParameterWord24 (60-byte body), and WaitForAudioServiceConditions (88-byte body);
- set typed parameter/return signatures and evidence comments;
- explicit save_program succeeded after these additions;
- high-level behavior is available for all three; ABI convention warning remains unresolved. The rejected literal `default` convention was not adopted.

AP1 recovery checkpoint:
- clean baseline was explicitly saved and exported before link mutation;
- backup: `/artifacts/exports/ap1-before-audio-links-20261002.gzf`, 3082627 bytes, native program package;
- exactly one reference was changed: from `0x807028D8`, operand 0, UNCONDITIONAL_CALL to `0x88001B58` with source DEFAULT was removed; replacement UNCONDITIONAL_CALL to `0x88001358`, source USER_DEFINED, was added and reported primary=true;
- refresh_action_behavior then showed the correct `0x88001358` destination;
- no raw bytes, other references or action bodies were changed in AP1 by this repair;
- an attempted rename to SetAudioDspParameterWord24 has an unverified outcome; inspect current name before any further naming action;
- persistence of the AP1 reference correction has NOT yet been confirmed by a successful post-change save. Before further AP1 edits, read current name/reference and reconcile with this record. Do not apply a blanket -0x800 adjustment.

## Pending decisions

1. Reconcile and save the recorded AP1 delta before stacking more metadata edits.
2. Reconcile the three exact EQ action links identified above, then check how the caller uses the command result.
3. Follow SRND/EQ command acceptance and DSP consumption before asserting complete effect behavior.
4. Preserve the nested neutral-reset block and disputed shared-return entries until their exact raw transitions are reconciled; do not delete them from stored links alone.
5. Keep processor clock, free-cycle budget, resident backend ownership and six physical output lanes as explicit remaining evidence boundaries.

Safety/provider incident records belong to `ArthurKoba/mcp-bridge` issues, not this board evidence file.
