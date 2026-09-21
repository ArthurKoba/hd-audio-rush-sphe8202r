# Next actions

Ordered by evidence value.

## Static reverse

1. Validate provisional image bases for `wma.bin`, `cdrom.bin`, and `drv_other.bin` using multiple independent absolute references.
2. Recover `gp` and global-data addressing for `ap1.bin`.
3. Define string/data regions so UI anchors gain proper xrefs.
4. Locate handlers for:
   - S/PDIF OFF / RAW / PCM;
   - S/PDIF input selection;
   - AC3/DTS stream detection/routing;
   - volume and mute;
   - USB host initialization and class handling.
5. Resolve cross-module calls between `ap1`, `drv_other`, `cdrom`, and `wma`.

## Hardware evidence

1. Read external SDRAM marking.
2. Trace TOSLINK receiver output.
3. Trace six analog output-stage inputs backward.
4. Identify the four SPHE-side USB/service pads electrically.
5. Confirm ownership and direction of the observed UART pins.

## Secondary controller

1. Identify exact public part behind marking `AK24BP24230`.
2. Obtain its firmware dump if possible.
3. Correlate its AC695N/BR23 runtime log with physical inter-chip links.

## Safety gate before firmware modification

Do not write modified images until:
- stock flash recovery is proven;
- exact packing/repacking behavior is understood;
- image integrity/checksum behavior is reproduced;
- rollback is tested;
- modification scope is isolated.
