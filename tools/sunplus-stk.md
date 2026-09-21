# Sunplus STK

Sunplus STK was used successfully to recognize and unpack the target stock SPI image.

## Known useful package

A historical package named `STK Sunplus Tools.rar` contains:

- `stk_0.2.3.rar`
- `stk_0.2.3_rev_090811.rar`
- `STK Sunplus Tool Kit 0.2.3 (rev 8203R) English.exe`

The rev-8203R build successfully recognizes the target firmware container.

## Observed target metadata

When opening the stock image, STK reports:

- version: `02R-D-02`
- ROM required: `1M`
- customer ID: `SUNPLUS`
- SoC profile: `SPHE8203R`
- SDRAM: `32M`
- SDRAM bus: `16 BITS`
- shared SDRAM: no
- Host USB 2.0: supported
- password: `5168`
- 18 module slots

The displayed `SPHE8203R` profile conflicts with the physical `SPHE8202R` package marking and is tracked as a contradiction.

## Repository policy

The STK executable/archive is not required in source control. If a future decision is made to preserve it in the repository, keep it under `tools/vendor/` with source URL, hash and licensing/provenance notes. Do not mix vendor binaries with project-owned tooling.
