# Analysis runtime failure log — 2026-10-01

This file records tool/runtime failures observed during the current SPHE8202R behavior-analysis pass, together with the evidence-preserving workaround used. It is not firmware behavior evidence.

## Incident classes

| Class | Observed symptom | Impact | Working workaround | Current interpretation |
|---|---|---|---|---|
| Project-open failure | Registry reports the project available, both workers healthy, project metadata readable, but both workers return `Failed to open project: /projects/sphe8202r_decoder_p25d80.gpr` | Canonical project temporarily unavailable | `close_project` followed by a fresh `open_project` restored the session | Likely project/session-open lifecycle defect; no evidence of project-data loss |
| Dropped program handle | Project remains active but a previously opened program disappears; operations return `Program not found` and list only another program | Read/inspection calls fail for that program | Re-open only the missing program by project path | Session-local open-program state is not reliably retained |
| Runtime image-base reset | `rom12-runtime.bin` reopened at image base zero; reads at `0x8800....` failed | Runtime evidence appears missing until corrected | Set image base back to `0x88000000`, allow narrow analysis, save program | Program mapping state was not consistently restored before explicit save/reopen |
| Missing action/index state | Known runtime entry such as `0x88001C78` is not present as an action node after reopen; low-level search misses its command-slot read until the region is decoded again | Search results can falsely imply absence | Narrow `analyze_byte_region` at the known entry, then re-run the search | Analysis/index state can be incomplete after session reopen; raw bytes remain present |
| Read-only pre-tool block | `list_open_programs`, `open_program`, behavior inspection, low-level search, data read, exact semantic search or specific address inspection may be rejected before the backend runs | One evidence path is unavailable although project is healthy | Do not repeat the identical request. Use a narrower query, different inspection API, direct canonical-binary read, or another authorized backend | External request-classification layer, not demonstrated to be an analysis-runtime defect |
| Sequential-call block | In a composed sequence, the first inspection succeeds and a later similar inspection is rejected before backend execution | Batch work aborts partway through | Split into single calls and analyze each result before continuing | Request composition itself can change classification |
| Mutation block | Both batch semantic naming and later single `name_action` attempts were rejected before backend execution | Semantic naming can lag behind recovered behavior | Defer mutation; keep read-only evidence and repository documentation current | External mutation/request classification; do not bypass or retry blindly |
| Inline-script block | Read-only inline script intended to inflate packed DSP profiles was rejected before execution | Could not use server-side scripting for decompression | Read the canonical repository binary and perform deterministic local raw-DEFLATE decoding | External scripting restriction; not a firmware or analysis-runtime failure |
| Connector transport failure | GitHub connector returned `Remote end closed connection without response` during file/history operations | Repository documentation step interrupted | Retry later or use the reviewer/alternate connector path where appropriate | Separate connector/network failure; keep distinct from analysis-runtime incidents |

## Reproducible observations

### Project-open failure

During the 2026-10-01 pass:
- `list_projects` showed `sphe8202r_decoder_p25d80` at `/projects/sphe8202r_decoder_p25d80.gpr` with session `available`;
- both worker slots were enabled, idle and healthy;
- `get_project_info` reported `file_count=23`, `program_count=23`;
- `open_project` nevertheless failed on both workers.

A complete close/open cycle then succeeded immediately and assigned worker 0. This is the strongest current indication that the failure is session/open lifecycle related rather than project absence.

### Program-handle loss

After successful work, the backend has later reported only one of several previously open programs. Confirmed examples in this pass include disappearance of:
- `rom12-runtime.bin`;
- `drv_other.bin`.

Re-opening only the missing program restored access without reopening or restoring the project.

### Mapping/index loss

`rom12-runtime.bin` has been observed reopening with a zero image base in an earlier session. After restoring `0x88000000` and saving, a later full project close/open retained the correct base. Separately, some known runtime action boundaries remain absent after reopen even while raw bytes are readable. Narrow low-level decoding restores the needed local index evidence.

## Workaround policy used by the agent

1. Never repeat an identical blocked request.
2. Prefer narrow read-only evidence queries.
3. If a program handle is missing, reopen only that program.
4. If the project itself will not open, perform one explicit close/open cycle.
5. If a known runtime address is not indexed, inspect only that byte region instead of launching broad analysis.
6. If an analysis request is blocked before backend execution, use another authorized evidence surface: canonical repository bytes, a different read-only inspection API, or an alternate backend.
7. Do not promote repository-byte decoding into canonical analysis state until the result is independently consistent with target bytes and existing contracts.
8. Keep external request-classification blocks separate from actual backend/runtime defects.

## Candidate fixes for later infrastructure work

Priority suggestions, not yet implemented:

1. **Project health check:** worker health should include a real project-open probe or return a specific filesystem/lock/error reason instead of only generic `Failed to open project`.
2. **Program auto-resolution:** a tool request with an explicit program path/name should be able to load the project program when the session handle disappeared, or return a diagnostic stating why it cannot.
3. **Persisted mapping guarantees:** image base and saved analysis state should be reloaded from the project artifact consistently across worker reassignment.
4. **Index-state diagnostics:** distinguish `raw bytes exist but this region is not decoded/indexed` from `address not mapped`.
5. **Session event logging:** expose worker assignment, project open/close, program open/close, and image-base restoration events with request IDs.
6. **Avoid large composite requests:** until the external request-classification behavior is better understood, orchestrators should favor small single-purpose calls.
7. **Separate outer-layer telemetry:** pre-tool safety/request-classification rejection should be identifiable independently from backend errors so it is not mistaken for analyzer instability.

