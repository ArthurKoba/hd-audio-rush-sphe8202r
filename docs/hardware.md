# Hardware notes

## Board identity

Product family: HD Audio Rush 5.1  
PCB silkscreen: `SPHE8202RD_SPDIF_V02`

### Confirmed marked parts

| Function | Marking / identity | Evidence |
|---|---|---|
| Main multimedia SoC | Sunplus `SPHE8202R` | physical package marking |
| External SPI NOR | Puya `P25D80SH` | physical marking + 1 MiB dump |
| Secondary controller | `AK24BP24230` | physical package marking |
| Board | `SPHE8202RD_SPDIF_V02` | PCB silkscreen |

## Do not assume the audio path

The SPHE8202R family has multichannel/audio capabilities, but this repository does **not** currently claim that six analog outputs are driven directly from SPHE pins on this PCB.

That requires one of:
- continuity evidence from output-stage inputs back to SPHE/external DAC pins;
- a board schematic;
- runtime probing showing analog/digital signals at the relevant nodes.

## USB pads

A four-pad unpopulated USB/service footprint is present. The user reports tracing those pads toward the SPHE side of the board rather than the secondary controller. No exact pin-level continuity measurement has yet been archived. D+/D-/VBUS/GND assignment and host/device behavior remain to be electrically confirmed and documented.

## Next physical evidence

1. Identify the external SDRAM marking and capacity.
2. Trace the output of the TOSLINK receiver to its first destination.
3. Trace the six analog output-stage inputs backward.
4. Identify the four USB/service pads by continuity to SoC pins and power rails.
5. Establish the physical UART TX/RX ownership.
