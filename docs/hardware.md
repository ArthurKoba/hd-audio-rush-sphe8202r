# Hardware

## Platform

Product: **HD Audio Rush 5.1**  
PCB: **SPHE8202RD_SPDIF_V02**

| Part / area | Marking or observation | Identification / role | Evidence |
|---|---|---|---|
| Main SoC | `SUNPLUS SPHE8202R` | Sunplus multimedia/audio SoC | **CONFIRMED** physical marking |
| External SDRAM | reported as `PMS3064 / 16BTR-60N` | External SDRAM; exact manufacturer and capacity still unresolved | **LIKELY** transcription; STK independently reports `SDRAM 32M`, 16-bit, non-shared |
| SPI NOR | `P25D80SH` | Puya 8-Mbit / 1-MiB SPI NOR; raw dump is in `firmware/P25D80SH@SOP8.BIN` | **CONFIRMED** marking + dump size |
| Secondary controller | `AK24BP24230` | Controller running JieLi AC695N/BR23-family software | physical marking **CONFIRMED**; exact public SKU **UNKNOWN** |
| Analog switch | `HCF4052` family marking reported | HCF4052B is a dual 4-channel analog multiplexer/demultiplexer, not a shift register or inverter | part function **CONFIRMED** by device documentation; exact board routing **UNKNOWN** |
| Logic IC | `74HC04D` marking reported | Six CMOS inverters in one package | part function **CONFIRMED** by device documentation; exact board role **UNKNOWN** |
| Analog output ICs | `4558D` marking on 8-pin devices near outputs | 4558-family devices are dual operational amplifiers; likely used for analog buffering/filtering/preamplification | part family function **CONFIRMED**; exact product-board circuit role **LIKELY** |

### SDRAM marking

The board marking still needs a clean macro photo/transcription. A web search found a reseller index entry spelled `306416BTR-6CN PM`, which is close to the reported marking, but no trustworthy datasheet was found that lets us claim the exact part or density. Do **not** silently convert STK's `32M` field into MB or Mbit until the physical part is confirmed.

## Connectors and service interfaces

### UART

The service jumper/header used for the captured boot log routes to the **secondary-controller side** according to the board trace already performed.

Confirmed behavior:
- UART TX produces the AC695N/BR23 boot/runtime log preserved in `evidence/ac695n-boot-excerpt.log`;
- the log includes `UserUartInit success`, `audio_dec_init`, `audio_dac_init`, `ALINK_SR = 44100`, `spdif_dec_start` and volume state;
- typing into the observed debug UART did not produce an interactive shell response.

The RX function/protocol therefore remains **UNKNOWN**; `UserUartInit success` may refer to another user-UART path.

### USB footprint

There is a four-pad unpopulated USB/service footprint. The user traced it toward the **main SPHE8202R**, not the secondary controller.

Current evidence:
- routing toward SPHE: **user-reported board trace**;
- exact D+/D-/VBUS/GND pad assignment: **UNKNOWN** until continuity is archived;
- STK reports `Host USB 2.0 supported` for this firmware profile;
- the Sunplus SPHE8202R demo-board reference schematic exposes `USB_DP` and `USB_DM` directly from the SPHE8202R and routes them to the USB connector;
- USB device/UAC capability of this exact product board/firmware is **UNKNOWN**.

## Audio I/O and path

Observed product I/O includes:
- optical TOSLINK S/PDIF;
- coaxial S/PDIF;
- AUX analog input;
- six analog outputs: FL, FR, SL, SR, CEN, SUB.

### SPHE8202R reference-design audio contract

The Sunplus **SPHE8202R Demo Board 8202R-16-SY-128-0-CZ** reference schematic provides strong architecture evidence for the SoC and its intended analog path:

- SPHE8202R exposes dedicated analog outputs `AOUT_R`, `AOUT_L`, `AOUT_RS`, `AOUT_LS`, `AOUT_SUBW`, and `AOUT_CENTER`;
- the demo-board AUDIO sheet routes these as `AOUT_FR/FL/SR/SL/SUB/C` through per-channel analog filter/buffer stages built around NJM4558 op-amps to `A_FR/A_FL/A_SR/A_SL/A_SUB/A_C`;
- all six output stages share an `A_MUTE` net;
- the demo board implements `A_MUTE` as a distinct **Power ON / OFF Mute** analog circuit, separate from the six DAC signals;
- `SPDIF_OUT` is routed separately to coaxial and optical-output circuitry;
- the reference design also exposes `AIN_R`/MIC input circuitry.

This reference design resolves an earlier architectural uncertainty: **SPHE8202R itself is capable of directly supplying all six 5.1 analog DAC channels.** It also provides a plausible reference topology for the 4558-family devices observed on the product board.

However, this is **reference-design evidence, not continuity proof for PCB SPHE8202RD_SPDIF_V02**. Do not silently claim that the product board copies the demo-board routing exactly.

### Firmware-to-output contract

Current firmware analysis independently establishes:
- speaker topology is packed and applied through the SPHE audio-service path;
- master volume is encoded as command family `0x1100|gain`;
- software master mute is implemented through the master-gain/audio-service state and is distinct from the demo-board reference `A_MUTE` analog power-mute net;
- S/PDIF RAW/PCM/output-mode control is handled separately from the six analog DAC channel topology;
- speaker CENTER/REAR delay, FRONT/CENTER/REAR/SUB topology, EQ, surround, echo and microphone controls all converge on the SPHE audio-service layer.

The exact mapping from runtime service internals to physical product-board nets still requires either:
1. product-board continuity/scope tracing, or
2. matching Sunplus 8202R SDK/source material.

Do not currently claim:
- that the product-board TOSLINK receiver enters SPHE first;
- that the secondary controller performs or does not perform compressed decode;
- that PCB SPHE8202RD_SPDIF_V02 copies the demo-board analog output circuit component-for-component;
- that the product-board `4558D` devices are definitely the final channel buffers until continuity is archived.

## Component references

- HCF4052B family: STMicroelectronics dual 4-channel analog multiplexer/demultiplexer.
- 74HC04D: Nexperia hex inverter — https://www.nexperia.com/product/74HC04D
- NJM4558/4558 family: dual operational amplifier — https://www.nisshinbo-microdevices.co.jp/en/products/operational-amplifier/spec/?product=njm4558
