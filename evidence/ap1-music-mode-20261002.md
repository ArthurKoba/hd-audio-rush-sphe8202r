# MUSIC MODE, decoder input ring and audio-service contracts — 2026-10-02

## Scope and continuation authority

Repository baseline: `1351bdd7d3cf8e761e0f1887deaa56670be39b9c`.
Canonical Analysis project: `ghp_8847e7bcc4fa1ca3b69ff2f5`; AP1 `/modules_mipsle/ap1.bin`, base `0x8067B800`; runtime `/runtime/rom12-runtime.bin`, base `0x88000000`.

This checkpoint supersedes the seven-fixed-EQ-curves description and the interpretation of configured decoder input-window sizes as DSP program-memory evidence in the 2026-10-01 handoff. It preserves the previously uncommitted correction and new native Analysis results. No firmware bytes are modified. Validation is CPU-side implementation proof, not execution/board proof or complete DSP algorithm recovery.

Latest directly queried AP1 semantic naming count: **135/3847 = approximately 3.51%**. This is not audio-path completion. The older 97–98% estimate is not a validated completeness measure for the remaining DSP/resource/physical-output contract.

## Confirmed MUSIC MODE mapping

The four 11-byte records at `0x8070B35C` separate distinct pages:
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

The displayed scale is confirmed; measured frequency response and band-center frequencies are not established here.

`gp+0x0C` stores SRND selection; `gp+0x0D` stores EQ selection. SRND mode is selection minus 2, sent as hardware action 5 / command family `0x0700|mode`. The apply route makes non-OFF SRND and non-STANDARD EQ mutually exclusive. This is factory control policy, not proof that the silicon cannot combine them, and is distinct from GM5.

## EQ payload and result propagation

`ApplySevenBandEqCurve` at `0x806E8ED0` calls `ApplySevenBandEqParameters` at `0x80702D64` with count 7, then `ApplySurroundModeIndex` at `0x80702D0C` with mode 0. All 10 native operations in this wrapper were inspected: it does not test the parameter-application result before issuing the SRND-OFF request.

The raw parameter action accepts `(count & 0xff) < 8`. Each byte is passed as `(index + 7, value)` through `0x807028D0` to runtime writer `0x88001358`. It writes 1 to `s6+0x130`, polls while that register reads zero, then sends `DispatchAudioHardwareAction(8,0x10,0)` and returns its result. Count zero skips payload writes but still performs handshake/dispatch; count >=8 returns zero without those side effects. There is no local result check for individual payload writes and no local bound in the `s6+0x130` readback loop. That loop is separate from the bounded service wait below.

Native target anchors refreshed in this session:
- `ap1:0x807028D8`, bytes `d6 04 00 0e`, word `0x0E0004D6`, encodes JAL `0x88001358`;
- `ap1:0x80702DE4`, word `0x0C1C0A34`, encodes JAL `0x807028D0`;
- `ap1:0x80702DB0`, word `0x0C1BFF47`, encodes JAL `0x806FFD1C`;
- `ap1:0x80702DF8`, word `0x081C0B66`, encodes J `0x80702D98`.

The stored high-level view followed several destinations displaced by +0x800; the last anchor was even stored as a call instead of a jump. One exact link was corrected as recorded below. The other three remain unrepaired and must not be used as DSP-consumer evidence.

## Shared 24-bit parameter bank

Native Analysis confirms `SetDspParameterWord24` at `0x88001358` (13 operations) and `GetDspParameterWord24` at `0x8800138C` (15 operations).

Both compute `0xA0000000 + (u16[gp+0x17B0]<<10) + index*3` with 32-bit arithmetic. Writer stores low byte at +2, high byte at +0, middle byte at +1; reader assembles the three bytes in big-endian order and zero-extends to 32 bits. Neither has a local index bound, handshake or atomic three-byte commit. Initialization uses 128 entries, but that is a caller contract, not an enforced writer limit. No atomic visibility guarantee is inferred.

Initialization and later EQ payload use the same writer. Thus an index alone is not a permanent semantic identity. DSP consumption/copy timing and ownership of this reused bank remain to be established.

## Bounded service wait and dispatcher returns

`WaitForAudioServiceConditions` at `0x88001C78..0x88001CCF` has 22/22 decoded native operations and a matching high-level view.

Inputs: a0 enables command-flag checking; a1 enables status-word checking; a2 is expected status; a3 is an unsigned maximum poll count. Each poll succeeds only when every enabled condition holds: `(u32[s6+0x4C0] & 0x8000) != 0` and/or `u32[s6+0x4D4] == a2`. Return is 1 on success and 0 for zero budget or exhausted polls. There are no command writes, timer reads or delay calls. The dispatcher passes `(1,0,0,100000)`; 100000 is a poll count, not a proved time unit or physical-effect guarantee.

The 59 native operations in the common dispatcher region at `0x806FFD1C` establish important return semantics:
- if `u32[gp+0x698] & 0x800` is nonzero, it returns 1 before writing either the auxiliary or command field. That return is a state-gated no-op, not command-execution proof;
- otherwise it writes the masked 16-bit auxiliary value to `s6+0x4C4` before validating the top-level action range;
- an out-of-range action returns -1, but the auxiliary write has already occurred;
- action 0 writes `0x0200|value` before its sub-value validation. A negative return cannot universally be equated with zero side effects;
- normal accepted paths return the bounded command-flag wait result. The exact meaning of the dispatcher state-mask gate remains separate from these instruction-proven mechanics.

These are factory semantics, not evidence of a measured device failure. A future control layer must distinguish skipped requests, command acceptance and the requested final state.

## Decoder input ring: corrected role of the configured window

`ConfigureDspProgramWindow` is retained as a historical action name, but its consumers now establish a CPU-fed decoder INPUT RING:

- buffer base `gp+0x600 = 0x80000000 + (u16[gp+0x17AE]<<10)`;
- capacity in bytes `N = u16[gp+0x71E]`;
- CPU producer byte cursor `W = u16[gp+0x730]`;
- service consumer byte cursor `R = 3*u32[s6+0x4CC]`;
- CPU publishes producer position in three-byte units through `s6+0x4C8`.

Native helper at `0x88001CD0` returns `d=R-W; d>0 ? d : d+N`. It is now named `GetDecoderInputRingFreeBytes`. The adjacent 12-operation region at `0x88001D00` computes queued bytes as `d=W-R; d>=0 ? d : d+N`. Equality therefore yields N free and zero queued under valid ring invariants. These are single-wrap adjustments, not general modulo normalization or independent full/empty synchronization.

Ownership evidence:
- native AP1 wrappers at `0x80702824` and `0x80702844` call the two runtime helpers;
- raw JAL searches find the free wrapper used at `0x8071BD3C/60/80` and the queued wrapper at `0x8071BD20`;
- CPU producers writing `gp+0x730` were found at `0x806822D8` and `0x806B908C`;
- the logical producer route starting `0x806B8EA0` computes consumer distance, adds N when needed, subtracts 30 bytes of headroom, and copies at most the available source bytes/free capacity;
- it copies one or two byte ranges across the destination wrap using `0x806D8E4C`, updates the source cursor and W, divides W by 3 through `0x8077CF88`, then publishes via `0x80702904` to `s6+0x4C8`;
- the other producer uses a guard read from `gp+0x772`; do not apply the fixed 30-byte margin to every producer;
- runtime `0x880014B4` clears the consumer register, W, and the published producer cursor during service reset, then selects a route based on the previous service state.

Configured capacities remain the observed byte values: 0x3C00 for decoder states 0x40/0x2000/0x20000; 0x3000 for 0x10/0x8000/0x40000; 0x2400 for 0x10000/ordinary fallback; state 0x200 conditionally uses 0x6C00. Capacity/3 is published as parameter 1 except in state 0x20.

This establishes the software transport-ring role. Those numbers are NOT total/free DSP program memory or evidence for PCM sample width. Exact DSP memory ownership, clock and filter budget remain unknown.

## Start, stop, pause and state-reconfiguration observations

Raw searches identified six AP1 calls to the bounded runtime wait: common dispatcher `0x806FFDD8`, start `0x80700C18`, stop `0x80700D04`, pause `0x80700D90`, resume/start route `0x80700EA0`, and decoder reconfiguration `0x80701814`.

The specific inspected lifecycle paths separate command acknowledgement from a second wait for the final service-state word:
- configured start requests action 0/value 1 and waits for state 1;
- stop route at `0x80700C84` requests action 0/value 3 and waits for state 0;
- pause route at `0x80700D34` requests action 0/value 4 and waits for state 2;
- the route surrounding `0x80700EA0` requests action 0/value 2 and waits for state 1.

The inspected start/stop/pause return paths require both a positive dispatcher result and a successful state wait. Already-in-requested-state branches may return 1 without a new request. These facts support stopped/running/paused roles for states 0/1/2; they do not establish physical signal state by themselves.

Pause additionally calls the native `SetMasterVolumeLevel(0)` wrapper at `0x8070129C` and writes `0x800F` to `s6+0xDA4` after the wait, even when the request/wait result will be reported as failure. The volume wrapper sends hardware action 2. This is a failure-side-effect observation, not a measured analog mute claim.

The delay helper `0x880120DC` has 12 native operations: repeat an inner decrement loop initialized to 0x6976 for each a0 outer iteration. It does not read a timer. Caller values 0x3C/0x50/0x78 are not independently established milliseconds or microseconds.

All 35 native operations of `ApplyAudioDecoderState` at `0x807017CC..0x80701857` were previewed. It issues action 9, requests stop, stores status -1, invokes profile configuration, waits for state 0, sets producer guard (0x400 for requested state 0x10, otherwise 8), starts the configured pipeline, then performs two post-configuration calls. It does NOT check results of the initial command, stop, profile configuration, state wait or configured start. In particular the wait result is overwritten immediately. No aggregate successful-application contract can be inferred from wrapper completion alone.

## Persistent Analysis changes and exact recovery state

Runtime `/runtime/rom12-runtime.bin`:
- exactly 112 bytes at `0x88001358..0x880013C7`, 88 at `0x88001C78..0x88001CCF`, and 96 at `0x88001CD0..0x88001D2F` were newly decoded;
- four action nodes created: SetDspParameterWord24 (52 bytes), GetDspParameterWord24 (60), WaitForAudioServiceConditions (88), GetDecoderInputRingFreeBytes (48);
- all four have explicit signatures; first three have matching high-level views, and the free-ring action is grounded in native operations;
- parameter-bank, free-ring, configured-window and busy-wait comments are saved;
- the queued-byte action at `0x88001D00` was NOT created: a postcondition read confirmed no action node there. Its 48-byte decoded region remains available;
- explicit save_program succeeded after the latest comments. ABI-convention warnings remain unresolved; no guessed convention was adopted.

AP1:
- baseline was saved and exported before metadata mutation; backup `/artifacts/exports/ap1-before-audio-links-20261002.gzf`, 3082627 bytes, native program package;
- exactly one reference changed: source `0x807028D8`, operand 0, old UNCONDITIONAL_CALL target `0x88001B58`/DEFAULT removed; correct target `0x88001358`/USER_DEFINED added with primary=true;
- refresh_action_behavior and later get_links_from both confirmed the corrected destination; subsequent save_program succeeded;
- the wrapper name remains `FUN_807028d0`, independently checked; no rename is claimed;
- no raw bytes or action bodies changed in AP1 by this repair;
- the three remaining EQ links at `0x80702DE4`, `0x80702DB0`, `0x80702DF8` remain unapplied corrections;
- the attempted extended comment on ApplyAudioDecoderState is absent on postcondition read; its older saved comment remains. The complete new source evidence is retained here.

## Remaining acceptance boundaries

1. Reconcile only the three independently proven EQ links when the normal metadata path permits; never blanket-adjust stored destinations.
2. Complete DSP-side payload consumption/copy timing and exact EQ/SRND processing, including band-center frequencies and effect algorithms, before calling that lane complete.
3. Trace stream underflow/overflow and source-switch interactions from the established ring and lifecycle contracts; do not restart unrelated DVD/UI analysis.
4. Keep the nested neutral-reset block and disputed shared-return entries until exact raw transitions are reconciled; do not delete them from stored links alone.
5. Establish DSP clock, free-cycle budget, resident backend ownership and six physical output lanes separately. CPU-side source proof cannot replace target execution/continuity measurements.

The whole audio-path task remains OPEN. Safety/provider incident records belong to `ArthurKoba/mcp-bridge` issues, not this board evidence file.
