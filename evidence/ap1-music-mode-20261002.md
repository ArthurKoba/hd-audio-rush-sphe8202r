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

The current saved high-level view instead follows several destinations displaced by +0x800. Do not use those stored destinations as DSP-consumer evidence. No broad metadata repair is claimed.

## State interaction

`gp+0x0C` stores SRND selection; `gp+0x0D` stores EQ selection. SRND mode is selection minus 2, sent as hardware action 5 / command family `0x0700|mode`. The MUSIC MODE apply route makes non-OFF SRND and non-STANDARD EQ mutually exclusive. This is a factory control policy, not proof that the silicon cannot combine them. It must not be conflated with the distinct GM5 control.

## Parameter-bank caveat

Earlier raw runtime evidence shows writer `0x88001358` computes `0xA0000000 + (u16[gp+0x17B0]<<10) + index*3` and stores the low 24 bits in big-endian order. Initialization and later EQ payload use the same writer. Thus an index alone is not a permanent semantic identity. The DSP consumption/copy timing and ownership of this reused bank remain to be established.

## Pending decisions

1. Confirm and annotate the writer/reader and command-dispatch continuation through the canonical Analysis surface.
2. Follow SRND/EQ command acceptance and DSP consumption before asserting complete effect behavior.
3. Preserve the nested neutral-reset block and disputed shared-return entries until their exact raw transitions are reconciled; do not delete them from stored links alone.
4. Keep processor clock, free-cycle budget, resident backend ownership and six physical output lanes as explicit remaining evidence boundaries.

Safety/provider incident records belong to `ArthurKoba/mcp-bridge` issues, not this board evidence file.
