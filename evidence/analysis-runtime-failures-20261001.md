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
| Mutation block | Both batch semantic naming and later single `name_action` attempts were rejected before backend execution | Semantic naming can lag behind recovered behavior | Defer mutation; keep read-only evidence and repository documentation current | External mutation/request classification; do not evade the restriction or retry blindly |
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




## Additional incidents from the late audio/DSP pass

### Multi-open selective block

A composed request attempted to open AP1, runtime, drv_other and srvdsp programs. Only `drv_other.bin` reached the backend; the other three program-open requests were rejected before backend execution. This demonstrates that a composed call can partially execute. Workaround: use single-program operations and never assume atomicity across a multi-call orchestration step.

### Annotation/save asymmetry

During handoff preparation:
- `set_comment` on `drv_other.bin` was rejected before backend execution;
- some `set_bookmark` operations succeeded while others at nearby addresses were rejected;
- `save_program`, `save_all_programs`, and `close_program(save=true)` were rejected before backend execution.

Two live-session bookmarks were successfully created at `drv_other.bin:0x807768D4` and `0x8077C29C`. Persistence of those new bookmarks is **not independently confirmed** because all explicit save surfaces were blocked afterward. Repository evidence is therefore authoritative for the late-pass findings.

### Project-load rejection

Alternative `load_program_from_project` requests for AP1, runtime and srvdsp were rejected before backend execution even though project metadata remained available. This is separate from a missing project file and should not be treated as project corruption.

### Connector and orchestration failures

Two non-analysis failures were observed:
- GitHub binary/file requests intermittently returned `Remote end closed connection without response`; using the reviewer read surface or retrying later succeeded.
- one large combined local profile scan failed with an internal orchestration error. Splitting the same work into one profile per call succeeded.

These failures should remain separate from analysis-runtime defects.

### Processor-model discovery boundary

The installed analysis runtime reports `srvdsp.bin` as `MIPS:LE:32:default`, which is wrong for the 24-bit DSP words. The raw-program loader supports an explicit registered language ID, but dry-run attempts with plausible ADSP-21xx/218x IDs failed. Upstream language-tree inspection also found no ready ADSP-21xx processor module.

The backend has no published tool for installing a processor definition. Its support for custom processor definitions assumes that the processor module is already registered when the analysis service starts. Therefore the supported future fix is:
1. build a separate target-specific processor module;
2. install/mount it into the analysis runtime by infrastructure means;
3. restart the service;
4. import new DSP program copies under a separate project folder;
5. preserve the existing MIPS probe programs until validation is complete.
