# Secondary JieLi controller — acquisition / identification handoff (2026-10-04)

This document is the continuation authority for the secondary 48-pin JieLi controller investigation. It records **physical target facts**, **software/runtime evidence**, **rejected identifications**, **external research**, **tooling**, and the exact continuation boundary.

## 1. Goal and current phase

Current project phase is firmware reconstruction first. For the secondary controller the immediate goal is:

1. identify the actual silicon/package variant strongly enough to select the correct Boot-ROM/update transport pins;
2. acquire the original firmware **read-only first**;
3. preserve two identical independent dumps;
4. only then begin pi32v2/static analysis and recover the remaining SPHE <-> secondary-controller boundary.

Do not erase, program, burn OTP/chip keys, or guess boot pins from a merely similar JieLi datasheet.

## 2. Target hardware facts — authoritative

These are physical observations from the actual HD Audio Rush board and override family guesses.

- Manufacturer/logo: JieLi/JL logo reported on package.
- Package: quad 48-pin package, 12 leads per side.
- Top mark transcription: `AK24 / BB24 / 230`.
  - Earlier repository text used `AK24BP24230`; this is **not proven as one continuous literal part number**.
  - Treat line joining / missing characters such as `BP` as unresolved until a clear macro image is archived.
- Direct continuity to board ground with power removed:
  - **pin 12 = GND**;
  - **pin 13 = GND**;
  - **pin 36 = GND**.
- Existing accessible serial header/adapter traces to package pins **23 and 24**.
- The pins 23/24 connection produces a coherent runtime/debug log at **115200 baud**.

The three hard-ground observations are a mandatory **physical-position fingerprint**, but the current user numbering is not yet proven to share the datasheet pin-1 orientation. Do not reject a candidate from literal `12/13/36` alone until all allowed LQFP48 orientation transforms have been checked. The known runtime-serial pair at physical positions `23/24` must be transformed by the same mapping and used as a second anchor.

## 3. UART observations from the target

Host used by the user: Windows, COM5, `uv run` workflow.

### Passive 9600 capture

Command family: local `tools/jieli/jieli_uart_probe.py`, listen-only.

Observed:
- one byte: `0C`.

Interpretation:
- line is electrically active around reset;
- this is **not sufficient** to identify a Boot-ROM UART.

### 9600 documented-sync experiment

The local probe sent only the public BR23-style sync prefix:
`55 AA 01 20 22 75 61 72 74`.

Observed:
- 196 received bytes;
- capture CRC32: `0x0A617C9D`;
- response consisted mostly of zeros / non-text pseudo-random bytes and ended in `0C`.

Interpretation:
- this did **not** look like a confirmed BR23 Boot-ROM handshake;
- no flash erase/write/program operation was implemented or used.

### Passive 115200 capture

Observed:
- 3160 bytes;
- capture CRC32: `0x4599AFDB`;
- coherent readable boot/runtime log.

Important strings reconstructed from the capture include:

- `setup_arch Feb 12 2023 14:40:24`
- `P3 Reset Source : 0x2`
- `[SDFILE]VM size: 0x2a000 @ 0x53000`
- `[SDFILE]disk capacity 1024 KB`
- `[SDFILE]sdfile mount succ`
- source-build path containing:
  `AC69XX/Software/AC695N_soundbox_sdk_release_3.1.0_LineIn_IIS/SDK/apps/soundbox/board/br23/board_ac695x_demo/board_ac695x_demo.c`
- `UserUartInit success`
- `[TEST-UPDATE]testbox msg handle reg:...`
- `audio_enc_init`
- `audio_dec_init`
- `[AUDIO-DAC]audio_dac_init`
- `ALINK_SR = 44100`
- `pcm`
- `spdif_dec_start`
- `APP_LINEIN_TASK`
- `ladc_ch_num[2],[3]`
- `linein->channel_num:2`

Interpretation:
- pins 23/24 are a **runtime/debug serial path** in the running target firmware;
- the firmware has strong BR23/AC695N SDK lineage;
- this is **software-lineage evidence, not exact silicon identification**;
- the reported 1024 KB is a useful firmware/storage observation, but it does not by itself prove the physical flash die/package arrangement.

The raw `reset_115200.bin`, `reset_9600.bin` and `boot_sync_reply.bin` remain on the user's workstation unless separately uploaded. The repository currently records the observed metadata and strings, not those raw files.

## 4. What the software lineage does and does not prove

Strongly supported from runtime execution:
- target code is derived from / highly compatible with the AC695N soundbox SDK lineage;
- board source lineage references `br23/board_ac695x_demo`;
- runtime initializes ALINK at 44.1 kHz;
- target line-in uses two LADC channels;
- target has JieLi test/update infrastructure registered.

Not proven:
- exact commercial silicon model;
- exact package pinout;
- that the chip is literally AC6951B/AC6951C;
- that BR23 Boot-ROM UART uses the same pins on this top-mark/package;
- that pins 23/24 are USB D+/D- on this physical variant;
- that the current accessible UART can enter Boot ROM/update mode;
- that the exact 1 MiB physical flash can already be read through that UART.

## 5. Canonical candidate ledger — checked models and no-repeat policy

This section is the authority for candidate status. Future agents must consult it before opening another datasheet or repeating pin checks.

Status meanings:

- **CLOSED / DO NOT REVISIT** — the candidate has a decisive package-level contradiction that survives every allowed orientation transform. Do not re-check it unless new physical evidence invalidates the target fingerprint or a genuinely different package revision is found.
- **CHECKED / PARKED** — the model was already investigated, but the historical rejection was based on incomplete/literal pin-number comparison rather than a complete orientation-aware pin table. Do not repeat the same manual pin checks. Re-open only if a new complete pin table or a new target-board anchor allows a materially stronger test.
- **ACTIVE** — still worth resolving because the required package map has not been recovered.

### CLOSED / DO NOT REVISIT

| Candidate | Status | Decisive evidence |
|---|---|---|
| **AC6951B / AC6951B8** | **CLOSED** | Complete V1.1 datasheet + automotive reference schematic recovered. LQFP48 exposes only two explicit ground-class package pins (VSSIO and DACVSS). The target has three independent hard-ground physical positions, so no rotation/reflection can make this package match. |
| **AC6951C / AC6951C8** | **CLOSED** | Complete public LQFP48 pinout recovered. Ground-class package pins are VSSIO and DACVSS only. Three hard grounds on the target are therefore impossible under every orientation transform. The apparent 23/24 USB-DM/DP similarity is not sufficient. |
| **AC6951G** | **CLOSED** | Authentic LQFP48 datasheet recovered. Only two ground-class package pins are present in the package map. This cannot satisfy the target's three-hard-ground fingerprint under any transform. |

These three models are excluded as target silicon. Do not spend time verifying them again.

### CHECKED / PARKED — do not repeat the historical test

| Candidate | Existing check | Why it is parked instead of active |
|---|---|---|
| **AC6921A** | Historical literal check found pin 12=VSSIO, pin 13=BT_OSCI, pin 36=DACR. | Already investigated and not a current BR23/AC695N favorite. The old literal check must not be repeated. Only re-open with a complete pin table and one-pass orientation scoring. |
| **JL7031C** | Historical literal check found pin 13=VSS and pin 12=BTRF. | Already investigated; not an active target candidate. Do not repeat the same pin-number comparison. |
| **AC4601** | Historical literal check found pin 12=FMVSS, pin 13=USBDM, pin 36=PA9. | Already investigated; use only as comparison corpus. Do not repeat the same pin-number comparison. |
| **AC6901A** | Compared during the earlier 48-pin search as a neighboring JieLi generation. | Not supported by the target's BR23/AC695N runtime lineage. Keep only as comparison corpus; do not restart manual verification. |
| **AC6351B / AC6351D** | Checked as neighboring BR23/AC63-family LQFP48 variants during catalog/datasheet search. | No target fingerprint match was established and the observed target runtime/storage/software evidence favors the AC695N branch. Do not re-run broad manual checks unless F/T are exhausted and a complete package map adds new evidence. |

### ACTIVE unresolved candidates

| Candidate | Why it remains active | Current blocker |
|---|---|---|
| **AC6951F8** | Live TOME data: eLQFP48 7x7x1.4, 8 Mbit flash, 4-channel DAC; same BR23/AC695N family and a plausible board class. | Full package pinout has not been recovered. TOME's English product page still exposes a direct CMS download record (product attachment id 248), but the attachment currently returns the site's error path. |
| **AC6951T8** | Family tables identify it as an LQFP48 / 8 Mbit BR23/AC695N variant. | No trustworthy full pinout/reference schematic recovered yet. |

**Active search is F8/T8 only.** Broad AC695N-family enumeration is complete enough that closed/parked models must not be cycled through again.

## 6. Package-marking policy — top text is not a model identifier

The JieLi/Jerry package text is **not a reliable commercial part-number key**. The physical target transcription `AK24 / BB24 / 230` is retained only as an observed artifact.

Observed market/teardown evidence shows that:
- commercial models can carry production/lot/date-style top codes that do not contain the public model name;
- the same general top-code namespace appears across different JieLi parts and products;
- a suffix can correlate with a model in an individual listing, but that correlation cannot be generalized into a stable decoding rule;
- joining the target lines into `AK24BP24230` was an inference and is withdrawn as an identification method.

Therefore:

1. **Do not select, accept, reject, or prioritize a silicon candidate from the package marking.**
2. Do not spend another research cycle trying to decode `AK24...` into a model number.
3. Marking searches are allowed only as weak discovery aids for locating board photos, reseller pages, archived documents or schematics.
4. Exact identification must come from the electrical/package fingerprint: package type, hard-ground set, known runtime-serial pair, then additional power/USB/audio anchors under one consistent orientation transform.
5. Candidate enumeration should come from product catalogs/family tables, not from top-mark databases.

The authoritative target anchors remain:
- physical hard-ground positions: `12,13,36`;
- physical runtime-serial pair: `23,24`;
- one single square-package transform must explain all anchors simultaneously.

## 7. External sources / sites inspected

### Candidate enumeration and document recovery — preferred order

1. **LCSC JieLi Tech catalog**
   - https://www.lcsc.com/brand-detail/959.html
   - Use as a finite product-family/catalog enumeration surface, especially for package filtering.
   - Do not infer identity from a listing name alone; use its datasheet/package map when available.

2. **TOME / Shenzhen TOME**
   - Chinese catalog: https://www.tome-sz.com/
   - English catalog: http://en.tome-sz.com/
   - Old technical-document index and CMS download records are especially valuable.
   - The English AC6951F8 product page still contains a direct CMS Download record for product/attachment id **248**, proving that an F8 downloadable artifact existed; the artifact currently resolves to the site's error path.
   - The older technical index still exposes working CMS records for models such as AC6951G and AC6951C. Use these records/CDN paths to recover historical documents rather than assuming deleted product-card links mean the files never existed.

3. **Yunthinker JieLi document archive**
   - https://www.yunthinker.com/
   - https://www.yunthinker.net/
   - High-value mirror for complete datasheets and reference schematics.
   - Used to recover/validate AC6951B and other 48-pin package material.

4. **Official JieLi documentation, GitLab and GitHub**
   - https://doc.zh-jieli.com/
   - https://github.com/Jieli-Tech
   - https://github.com/Jieli-Tech/fw-Bootloader
   - public JieLi GitLab AC695N soundbox SDK
   - Source authority for SDK lineage, UART/update/testbox behavior and board configuration; software lineage is not exact silicon identity.

5. **kagaimiq/jielie and jl-uboot-tool**
   - https://github.com/kagaimiq/jielie
   - https://github.com/kagaimiq/jl-uboot-tool
   - Useful for BR23/AC695N family inventory, architecture, UBOOT behavior and read-only acquisition tooling.

6. **Qingyue / blevoice and Chinese schematic/repair forums**
   - http://www.blevoice.com/
   - https://bbs.ntpcb.com/
   - Useful for hidden/unindexed product pages, reference-board context and schematic attachment names.
   - Respect access controls: search public mirrors/caches for protected attachments rather than bypassing forum permissions.

### Low-value / discovery-only surfaces

- Marking-code databases such as Shenzhen Guanrong are **not** an identification authority. They may prove that a production code exists, but not what target silicon it maps to.
- Search engines, image search, marketplaces and repair forums are discovery surfaces only until a datasheet, schematic, package table or direct board evidence supports the claim.
- Exact `AK24...` searches are no longer an active identification path.


## 8. Acquisition tooling currently in repository

Directory: `tools/jieli/`

- `jieli_uart_probe.py`
  - PEP 723 inline dependency metadata;
  - intended to run via `uv run`;
  - passive UART capture;
  - optional documented sync-prefix transmission;
  - **no flash erase/write/program implementation**.
- `verify_dumps.py`
  - compares two independent reads by size and SHA-256.
- `README.md`
  - acquisition workflow and safety boundary.

The user already has `uv`; do not instruct them to install/download uv again.

## 9. Safety / acceptance rules for dumping

Until exact hardware transport is established:

- no erase;
- no chip erase;
- no generic flash write;
- no OTP write;
- no chip-key burn;
- no guessed strap/boot pin based on a rejected candidate;
- no 5 V/RS-232 signaling assumptions.

A successful acquisition is accepted only after:
- two independent complete reads;
- same byte count;
- identical SHA-256;
- first raw dump preserved immutable;
- analysis performed on a copy.

## 10. Current continuation priority

The next agent should **not** re-prove the AC695N runtime log or ALINK 44.1 kHz.

Priority order:

1. Search for exact or adjacent `AK24 / BB24 / 230` top-mark mapping.
2. Search 48-pin JieLi packages/schematics/datasheets and score them against the **orientation-aware** physical fingerprint. For the observed hard grounds `{12,13,36}`, the eight LQFP48 top/bottom-orientation hypotheses map to datasheet-number sets `{12,13,36}`, `{24,25,48}`, `{12,36,37}`, `{1,24,48}`, `{14,37,38}`, `{1,2,26}`, `{13,14,38}`, `{2,25,26}`. The observed runtime-serial pair `{23,24}` maps under the same hypotheses to `{23,24}`, `{35,36}`, `{47,48}`, `{11,12}`, `{26,27}`, `{38,39}`, `{2,3}`, `{14,15}` respectively.
3. Require one *single* transform to make the candidate's ground pins and plausible serial-capable pins agree simultaneously before using that datasheet for Boot-ROM/update UART/USB pin selection.
4. If no public mapping exists, use non-destructive target fingerprinting next (additional GND/power/known UART continuity) rather than guessing a model.
5. Build/enable a read-only UART RAM dumper only once the correct Boot-ROM transport and post-loader return protocol are grounded.
6. After dump acquisition, create the pi32v2 static-analysis target and recover the remaining control/status transport to SPHE.

## 11. Current project-level percentages

These are approximate behavior/reconstruction coverage, not hardware/product readiness.

- SPHE <-> JieLi audio/control boundary: ~72%.
- JieLi firmware/control domain: ~45%; raw firmware is the major missing artifact.
- JieLi UART: runtime/debug path known; Boot-ROM/update acquisition path not yet established.
- USB Host on SPHE: ~93%, paused at hardware boundary.
- USB Device/UAC: ~48%, deferred.
- DSP resource/headroom model: ~55%, active firmware-analysis gap.

The firmware-first project policy remains: areas already blocked only on hardware acceptance stay frozen while software/reconstruction gaps such as JieLi acquisition and SPHE<->JieLi integration are attacked.


## 12. Secondary-controller role in the product

Current recovered audio model:

```text
Bluetooth / analog AUX L/R / PCM S/PDIF
        -> secondary JieLi firmware
        -> LADC line-in channels [2],[3] / common mixer / digital volume
        -> ALINK TX @ 44.1 kHz
        -> [SPHE-side receiver still unidentified]
        -> SPHE PCM/AUX processing / GM5 / EQ / 2.0->5.1
        -> six-channel SPHE output
```

The recovered direction is secondary controller -> external receiver: the matching SDK lineage opens ALINK as TX and the target runtime prints `ALINK_SR = 44100`.

The target secondary firmware also starts an S/PDIF decoder path, but recovered runtime/SDK evidence for the observed route selects PCM. Current architecture therefore keeps original AC-3/DTS multichannel decode on the SPHE side.

Two separate inter-chip contracts remain open and must not be conflated:
1. audio transport: JieLi common mixer -> ALINK TX -> unknown SPHE receiver;
2. control/status transport: source/state/status/control messages between processors.

The exposed 115200 debug UART does not prove that inter-chip control uses UART.

Recovered target behavior places SOURCE and 2.0/5.1 physical buttons on the SPHE side. Historical JieLi `key_event:276` was corrected to an internal LINEIN-start event, not a front-panel button.

## 13. Important corrections / dead ends

Do not resurrect these without genuinely new evidence:

- **AC6951B/B8, AC6951C/C8 and AC6951G are CLOSED target candidates.** Their recovered package maps cannot supply the target's three independent hard-ground positions under any allowed orientation transform. Do not re-open them from package appearance, USB-pin similarity or another reseller listing.
- Pins 23/24 = USB D-/D+ because one AC6951-family datasheet says so: invalid for this target; target physical positions 23/24 are observed as runtime serial at 115200.
- One `0x0C` byte at 9600 = Boot ROM: not proven.
- 196 binary bytes after BR23-style sync = successful Boot ROM: not proven.
- AC695N/BR23 build path = exact chip model: false; software lineage only.
- Decoding `AK24 / BB24 / 230` or any reconstructed `AK24BP...` string into a commercial model is withdrawn as an identification method.
- USB as immediate acquisition route: deferred because actual target USB pins are unknown; physically accessible interface is UART.
- Guessing PB5/LDO_IN or another boot/update pin from a different package variant is prohibited until the target package map is grounded.

## 14. Closed research dead ends — do not repeat

The following work has already been attempted and should not consume another research cycle:

- exact/variant searches for `AK24BP24230`, `AK24BB24230`, neighboring `AK24BP...` codes and suffix guessing;
- top-mark databases, marketplace-code searches and GitHub/Gitee/GitCode searches as a way to identify the commercial SKU;
- repeated Google/Bing/Baidu/image searches whose only new input is the package marking;
- manual literal-pin checks of AC6921A, JL7031C, AC4601, AC6901A or AC6351B/D without a new complete package map;
- treating search-engine/AI summaries as part-number evidence;
- using AC695N/BR23 software lineage as an exact silicon claim.

These sources may still be used to discover a **new document or schematic**, but package marking itself is not a decision variable.

## 15. Best next evidence paths

1. recover the missing **AC6951F8** package document/reference schematic, prioritizing TOME's historical CMS/download record (attachment/product id 248), public CDN paths, caches and legitimate mirrors;
2. recover a trustworthy **AC6951T8** full pinout/reference schematic;
3. build complete F8/T8 pin tables and score all orientation transforms mechanically against both target anchors;
4. if F8/T8 fail, expand the LQFP48 candidate set from LCSC/TOME/JieLi family catalogs by package/family/electrical capability — **not by top mark** — and strengthen the target fingerprint with additional non-destructive power/USB/audio continuity anchors;
5. preserve raw UART captures in the repository once uploaded;
6. once a read-only dump is obtained, move immediately into pi32v2 firmware analysis unless exact package naming is still electrically required.

## 16. Orientation-aware package fingerprinting — 2026-10-04 correction

The physical numbering used during continuity probing may be rotated relative to the real datasheet pin-1 marker, and a mirrored numbering can arise if a drawing/board view is interpreted from the opposite side. Therefore package identification now uses the full square-package orientation set instead of assuming the observed `12/13/36` are literal datasheet numbers.

For a 48-pin package with 12 pins per side, the observed anchors transform as follows:

| Hypothesis | Physical GND `12,13,36` -> datasheet pins | Physical runtime UART `23,24` -> datasheet pins |
|---|---|---|
| 0° | 12,13,36 | 23,24 |
| 90° | 24,25,48 | 35,36 |
| 180° | 12,36,37 | 47,48 |
| 270° | 1,24,48 | 11,12 |
| mirrored 0° | 14,37,38 | 26,27 |
| mirrored 90° | 1,2,26 | 38,39 |
| mirrored 180° | 13,14,38 | 2,3 |
| mirrored 270° | 2,25,26 | 14,15 |

A candidate is useful only if one single hypothesis simultaneously explains:
1. all three hard-ground observations as documented ground-family pins; and
2. the observed adjacent runtime-serial pair as pins that can plausibly carry the measured serial path in that firmware/package.

This replaces the older one-axis method of opening a datasheet and checking literal pins 12/13/36 only.

Candidate status after applying this correction is maintained only in the canonical ledger in section 5:
- **CLOSED:** AC6951B/B8, AC6951C/C8, AC6951G;
- **CHECKED/PARKED:** AC6921A, JL7031C, AC4601, AC6901A, AC6351B/D;
- **ACTIVE:** AC6951F8, AC6951T8.

Do not recompute closed or parked candidates with another manual one-PDF/one-pin pass. Orientation scoring should now be performed only when a genuinely new complete package table is recovered.


## 17. New marking and SDK evidence — 2026-10-04 continued search

Two higher-value evidence paths now supersede simple top-mark searching.

### Historical marking evidence — why the package text is ignored

Retail/teardown examples show AC6951C/C8 devices carrying production strings such as `AC23BP11419-51C8`, `AC24BP20882-51C8` and `AC21BP0H728-51C8` instead of a stable public model name. Other JieLi devices use the same general production-code style.

This is sufficient to remove package text from the identification logic: it is a trace/production artifact, not a reliable commercial-model key. A suffix may correlate with a model in one listing, but there is no stable decoding rule suitable for target identification. The target transcription `AK24 / BB24 / 230` must not influence candidate selection.

AC6951C itself is already **CLOSED** by the orientation-independent ground-count contradiction recorded in section 5.

### SDK 3.1.0 exposes multiple distinct UART roles

Public JieLi GitLab branch `feature_sdk_310_UART0_RX` confirms for `board_ac695x_demo`:
- debug UART0: TX=PA5, RX=PA6, 1,000,000 baud;
- optional `USER_UART_UPDATE_ENABLE` route: RX=PA2, TX=PA3.

This is important because the target's 115200 `UserUartInit success` path is therefore not the stock demo debug UART. Treat it as a product-specific UART initialization until its implementation is found. Candidate package scoring should check whether the physical runtime pair can map to plausible PA2/PA3, PA5/PA6, DP/DM, or another explicitly recovered custom pair under one orientation transform.

The official/public SDK lineage also confirms the exact 3.1.0 release tree and a dedicated `feature_sdk_310_UART0_RX` branch, so source-level recovery of update/testbox UART behavior is a viable route independent of exact package naming.


## 18. Source-tree correlation — 2026-10-04

Public JieLi GitLab API was used to enumerate the full `feature_sdk_310_UART0_RX` tree (1938 objects) and inspect the update/UART sources directly.

Confirmed source facts:
- `apps/common/update/uart_update.c` starts at 9600 baud and implements framed UART update commands `START/READ/END/UPDATE_LEN/KEEP_ALIVE/READY`; the update parameters persist both TX and RX GPIO numbers.
- `apps/common/update/testbox_update.c` emits the exact log family `[TEST-UPDATE] testbox msg handle reg` and registers the Bluetooth-controller testbox update callback. Therefore the target runtime log proves this stock update subsystem is present, not a product-specific printf.
- `feature_sdk_310_UART0_RX` board demo uses debug UART PA5/PA6 and a separate optional USER UART UPDATE path PA2/PA3.
- The public `LINEIN-IIS-INPUTE` branch configures soundbox-tool UART on `TX=DP, RX=DM`. Thus seeing UART traffic on package pins that another datasheet labels USB D+/D- is entirely plausible in this software lineage.
- That branch is **not** treated as the target source: its line-in path uses IIS input (48 kHz / WM8978-oriented configuration), whereas target runtime evidence shows stereo LADC line-in plus ALINK 44.1 kHz. It is a semantic/source-family oracle only.

A useful contradiction is now explicit for AC6951C under the literal orientation: its public pinout places USB DM/DP at 23/24, which fits a DP/DM UART role, but pin 12 is BT_RF rather than hard ground. Because the target physically has hard ground at observed position 12, AC6951C cannot be accepted without resolving that contradiction; matching UART alone is insufficient.

Public branch inventory also contains `AC695N_soundbox_sdk_release_3.1.0_HDMI_ARC`, confirming JieLi used branch names of the same `AC695N_soundbox_sdk_release_3.1.0_<feature>` form seen in the target build path. No currently public branch named exactly `...LineIn_IIS` was found; the target directory may correspond to a historical/private/deleted branch or a local project clone.


## 19. Historical direct top-mark sightings — negative identification evidence only

These sightings are retained only to document why top-mark decoding was abandoned:

- a modern generic S1 MP3 player teardown shows a 48-pin Jerry/JieLi chip marked `AK24BP2D054-51C8`;
- Alibaba listings sell AC6951C8 QFP48 with production mark `AC24BP20882-51C8`;
- repair material reports the same `AC24BP20882-51C8` string in an AC6951C8 replacement context;
- marking indexes contain neighboring `AK24BP...` codes without trustworthy model mappings.

Interpretation:
- `A?24BP...`-style strings behave as production/trace codes rather than stable public part numbers;
- individual suffix/model associations are listing-specific and cannot be generalized;
- the target transcription must not be reconstructed into a guessed commercial identifier;
- exact leading-code search must not be used to prioritize or reject candidates.

**This research path is closed for silicon identification.** Keep these sightings only as provenance for the package-marking policy in section 6.

## 20. F8/T8 narrowing and removed-document evidence — 2026-10-04

The current search ignores package marking for model identification and uses family/package/electrical evidence.

New findings:
- TOME's live product page for **AC6951F8** identifies it as **eLQFP48 (7x7x1.4), 8 Mbit flash, 4-channel DAC**. This materially distinguishes F8 from AC6951C8 and makes F8 a stronger board-class candidate for a multi-audio-interface design.
- TOME's Chinese product page renders a DOWNLOAD section without a usable F8 href, while the English AC6951F8 page still exposes a direct CMS download record for id 248. That record currently resolves to TOME's error path. This proves an F8 downloadable artifact existed even though the backing file is now removed/disabled.
- TOME does not currently expose AC6951T8 in its public AC695N product list even though independent BR23 family tables list AC6951T as LQFP48 / 8 Mbit. Treat T8 as a valid family candidate with weaker current public commercial-document coverage.
- TOME's older technical-document index still exposes working CMS downloads for AC6951G and AC6951C, confirming that historical CMS records can remain recoverable after product-page changes. No trustworthy F8 pinout has yet been recovered.
- Therefore F8/T8 remain the highest-value unresolved LQFP48 BR23 variants, while C/G have stronger public pinout evidence but conflict with the target physical fingerprint.

Next evidence path:
1. recover historical/removed F8/T8 documents via CDN filenames, archived product pages, reseller mirrors and schematic attachments;
2. compare full ground/power/USB/UART maps under the orientation matrix;
3. if public pinout recovery still fails, derive the missing package mapping from SDK I/O-function tables plus a minimal additional physical power-pin fingerprint rather than from top-mark text.


## 21. AC6951B exclusion and current BR23 shortlist — 2026-10-04

A complete AC6951B Datasheet V1.1 and the matching automotive reference schematic were recovered from Yunthinker mirrors.

AC6951B LQFP48 package evidence:
- pin 12 = BT_RF;
- pin 23 = USBDM;
- pin 24 = USBDP;
- package ground-class pins are VSSIO and DACVSS only (two explicit package grounds).

Because the target has three independent hard-ground physical positions, AC6951B cannot satisfy the orientation-aware three-ground fingerprint under any rotation/reflection: orientation transforms permute pin positions but cannot create a third ground-class package pin.

This closes AC6951B as a target candidate even though its USB/UART-adjacent layout is otherwise similar to the AC695N family.

Current BR23 LQFP48 status:
- AC6951B: excluded by ground-count/package fingerprint.
- AC6951C: excluded by ground-count/package fingerprint (two ground-class pins only).
- AC6951G: excluded by ground-count/package fingerprint (two ground-class pins only in recovered datasheet).
- AC6951F: unresolved; live TOME page confirms eLQFP48 7x7x1.4, 8 Mbit flash, 4-channel DAC; pinout document still missing.
- AC6951T: unresolved; family tables confirm LQFP48 / 8 Mbit, but no trustworthy full pinout recovered yet.

The active identification task is therefore no longer a broad AC695N search. It is specifically to recover F/T package maps or prove that neither can supply the target's three-ground physical fingerprint.
