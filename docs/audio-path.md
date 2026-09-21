# Audio path — evidence ledger

The exact audio path is intentionally unresolved.

## Confirmed software capabilities in the stock image

The main Sunplus application includes S/PDIF OFF/RAW/PCM and S/PDIF input UI strings, plus AC3/DTS/PCM and audio setup/output strings.

A separate AC695N/BR23 runtime log includes `spdif_dec_start`, ALINK sample-rate output and volume state.

## Not yet proven on this board

Do not currently claim any of the following as fact:
- TOSLINK enters SPHE first;
- TOSLINK enters the secondary controller first;
- SPHE directly drives all six analog channels;
- an external six-channel DAC is present;
- volume is implemented in SPHE, the secondary controller, or external analog circuitry.

## Required proof

Trace/probe:
1. TOSLINK receiver digital output;
2. six output-stage inputs;
3. digital audio links between both processors;
4. control-bus links between both processors;
5. behavior while switching PCM/RAW and changing volume.

Static reverse should then be correlated with the measured route.
