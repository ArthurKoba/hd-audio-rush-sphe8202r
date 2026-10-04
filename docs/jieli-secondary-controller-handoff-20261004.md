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

## 5. Rejected LQFP48 / 48-pin candidates

Historical candidate rejections below used the initial literal numbering assumption. They remain useful only where the candidate also fails the new orientation-aware test. From 2026-10-04 onward, candidates are checked against all square-package orientation transforms using both anchors: hard-ground physical positions `12/13/36` and runtime-serial physical positions `23/24`.

### AC6951C
Rejected.
- public pinout: pin 13 = VSSIO, pin 36 = DACVSS;
- but pin 12 = BT_RF, not ground.
Therefore it cannot be used as the target package pinout.

### AC6921A
Rejected.
- pin 12 = VSSIO;
- pin 13 = BT_OSCI;
- pin 36 = DACR.
Does not match.

### JL7031C
Rejected.
- pin 13 = VSS;
- pin 12 = BTRF.
Does not match.

### AC4601
Rejected.
- pin 12 = FMVSS;
- pin 13 = USBDM;
- pin 36 = PA9.
Does not match.

Any older statement assigning a target boot pin from one of these candidates is withdrawn.

## 6. Marking-code research

The exact literal `AK24BP24230` has not been found in a trustworthy public datasheet or model mapping.

However, multiple real marking/top-code strings with the same `AK24BP...` shape were found in marking-code/search databases, including:

- `AK24BP24178-51C8`
- `AK24BP24220-C8` / `AK24BP24220-51C8`
- `AK24BP0H003`
- `AK24BP0K599`
- `AK24BP21078`
- `AK24BP27485-51C8`

Related JieLi-looking contemporary marks also occur as `AC24BP...`, `AB24BP...`, `AS24BP...`, `AG24BP...`.

What this supports:
- `AK24...` is plausibly a production/top-mark family, not a normal public model name.

What it does **not** support:
- a direct mapping from the target mark to one specific retail model;
- any exact target pinout.

## 7. External sources / sites inspected

### Primary / technically useful

1. **kagaimiq/jl-uboot-tool**
   - https://github.com/kagaimiq/jl-uboot-tool
   - https://github.com/kagaimiq/jl-uboot-tool/blob/main/README.md
   - https://github.com/kagaimiq/jl-uboot-tool/blob/main/docs/uart-protocol.md
   - https://github.com/kagaimiq/jl-uboot-tool/blob/main/data/uart-loaders.yaml
   - https://github.com/kagaimiq/jl-uboot-tool/blob/main/docs/what-is-uboot.md

   Useful findings:
   - BR23/AC695N is supported by the project in its established UBOOT workflow;
   - public BR23 Boot-ROM UART-loader framing exists;
   - upstream metadata includes a BR23 UART loader and a RAM-load address/encryption description.

   Limitation:
   - the project's normal complete flash-reading flow is centered on UBOOT/USB;
   - the post-RAM-loader UART flash-return/read transport is not sufficiently established in our project to invent a complete UART dumper safely.

2. **Official JieLi documentation / repositories**
   - https://doc.zh-jieli.com/
   - https://doc.zh-jieli.com/AW33/zh-cn/master/update/testbox_update/testbox_update.html
   - https://doc.zh-jieli.com/AC63/zh-cn/release_v2.3.0/module_demo/ota/ota_introduce.html
   - https://github.com/Jieli-Tech
   - https://github.com/Jieli-Tech/fw-Bootloader
   - https://github.com/Jieli-Tech/AD24N

   Useful findings:
   - confirms JieLi update/testbox/boot infrastructure as a real platform concept;
   - supports treating the runtime `[TEST-UPDATE]` string as meaningful software infrastructure rather than random application text.

   Limitation:
   - no public document inspected so far maps target top mark `AK24 / BB24 / 230` to an exact 48-pin model/pinout.

3. **Yunthinker JieLi document archive**
   - https://www.yunthinker.com/
   - https://www.yunthinker.net/
   - example archive PDF opened during research:
     https://www.yunthinker.com/static/upload/file/20250104/1735974520457924.pdf

   Useful:
   - large collection of JieLi datasheets/reference material;
   - used to search/compare 48-pin candidates and ground/power layouts.

   Limitation:
   - no exact target fingerprint match was obtained in the current pass.

4. **Shenzhen Guanrong marking-code database**
   - https://www.tvs-gr.com/code/
   - https://www.tvs-gr.com/en/code/

   Useful:
   - search/index pages expose many `AK24BP...` / `AC24BP...` style strings;
   - supports the top-mark-family hypothesis.

   Important negative result:
   - direct exact lookup for `AK24BP24220` returned no structured model row even though the string is indexed in the site's popular/search corpus;
   - therefore these strings must not be treated as proven model mappings.

### Search engines / discovery surfaces

- Google Search and Google Images: many query variants for exact mark, Chinese JieLi terms, LQFP48, GND/VSS fingerprint, adjacent AK24BP codes.
- Bing: exact/variant marking queries; no useful exact model mapping found.
- Baidu: attempted through the MCP browser; repeated upstream timeout, no usable result from this pass.
- Google searches scoped to GitHub, Gitee and GitCode for `AK24BP`: no useful source-code mapping found.

These search-engine summaries are discovery aids only, not evidence for a part-number claim.

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

Do not resurrect these without new evidence:

- AC6951B/AC6951C identification by package appearance: not accepted. Earlier literal-number rejection is no longer sufficient by itself; any reconsideration must pass the orientation-aware ground+runtime-serial transform test.
- Pins 23/24 = USB D-/D+ because one AC6951C datasheet says so: invalid for this target; target pins 23/24 are observed as runtime serial at 115200.
- One `0x0C` byte at 9600 = Boot ROM: not proven.
- 196 binary bytes after BR23-style sync = successful Boot ROM: not proven.
- AC695N/BR23 build path = exact chip model: false; software lineage only.
- `AK24/BB24/230` = literal `AK24BP24230` public model: not proven.
- USB as immediate acquisition route: deferred because actual target USB pins are unknown; physically accessible interface is UART.
- Guessing PB5/LDO_IN from a different BR23 package: prohibited until matching pinout is found.

## 14. Research methods with little/no value

- Exact English search for `AK24BP24230`: no authoritative hit.
- `AK24BB24230` and spacing variants: no authoritative hit.
- Google-scoped GitHub/Gitee/GitCode searches for `AK24BP`: no useful model-to-pinout source.
- Bing exact queries: no useful model mapping.
- Baidu through MCP browser: repeated timeout.
- Marking-code databases: useful only to prove similar AK24BP marks exist; no target model mapping.
- Google AI/search summaries: discovery-only, not evidence.
- Searching only old public AC695N family: too narrow because physical fingerprint contradicts known AC6951C layout.

## 15. Best next evidence paths

1. retain a clear macro photo of entire top mark and pin-1 indicator;
2. search Chinese board/schematic/service material by visual top mark and adjacent AK24BP codes;
3. if public mapping remains absent, build a stronger non-destructive package fingerprint from additional GND/power/known-UART continuity;
4. identify second serial/test/update pads only after pinout evidence, not by energizing unknown pins;
5. preserve raw UART captures in repository once uploaded;
6. once a read-only dump is obtained, move immediately into pi32v2 firmware analysis unless exact package naming is still needed electrically.


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

Newly checked with this method:
- **AC6951G**: authentic datasheet obtained; literal pin 12=VSS, 13=OSCI, 36=MIC, 37=AGND. It fails the literal mapping, and remains under orientation-aware scoring rather than being rejected solely from literal numbering.
- **AC6901A / AC6921A / AC4601 / AC6951C**: retained as comparison corpus; their full ground/power/serial maps should be scored under the same transform matrix before any final exclusion statement is reused.

Research should now prefer collecting complete pin tables into a small comparison corpus and scoring transforms mechanically, instead of repeating manual one-PDF/one-pin checks.


## 17. New marking and SDK evidence — 2026-10-04 continued search

Two higher-value evidence paths now supersede simple top-mark searching.

### Production-mark format is proven on AC6951C8

A retail AC6951C8 LQFP48 has been photographed/listed with top mark `AC23BP11419-51C8`; another listing identifies `AC24BP20882-51C8` as AC6951C8. Independent teardown material identifies `AC21BP0H728-51C8` as AC6951C. This proves that the leading `AC/AKyyBP...` string is not the public model name and that the suffix such as `-51C8` can encode the actual AC6951C8 variant.

Implication for target mark `AK24 / BB24 / 230`: do not try to derive the exact silicon from the leading production code alone. A missing/worn/unread suffix remains a plausible explanation and should be checked on a macro photo, but package electrical fingerprint still outranks marking inference.

AC6951C itself still does **not** fit the target ground fingerprint because its documented LQFP48 package exposes only VSSIO pin 13 and DACVSS pin 36 as ground-class pins; three independent hard-ground positions cannot be produced by orientation alone.

### SDK 3.1.0 exposes multiple distinct UART roles

Public JieLi GitLab branch `feature_sdk_310_UART0_RX` confirms for `board_ac695x_demo`:
- debug UART0: TX=PA5, RX=PA6, 1,000,000 baud;
- optional `USER_UART_UPDATE_ENABLE` route: RX=PA2, TX=PA3.

This is important because the target's 115200 `UserUartInit success` path is therefore not the stock demo debug UART. Treat it as a product-specific UART initialization until its implementation is found. Candidate package scoring should check whether the physical runtime pair can map to plausible PA2/PA3, PA5/PA6, DP/DM, or another explicitly recovered custom pair under one orientation transform.

The official/public SDK lineage also confirms the exact 3.1.0 release tree and a dedicated `feature_sdk_310_UART0_RX` branch, so source-level recovery of update/testbox UART behavior is a viable route independent of exact package naming.
