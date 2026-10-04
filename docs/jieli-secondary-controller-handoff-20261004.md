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
