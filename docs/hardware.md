# Hardware

## Platform

Product: **HD Audio Rush 5.1**  
PCB: **SPHE8202RD_SPDIF_V02**

| Part / area | Marking or observation | Identification / role | Evidence |
|---|---|---|---|
| Main SoC | `SUNPLUS SPHE8202R` | Sunplus multimedia/audio SoC | **CONFIRMED** physical marking |
| External SDRAM | reported as `PMS3064 / 16BTR-60N` | External SDRAM; exact manufacturer and capacity still unresolved | **LIKELY** transcription; STK independently reports `SDRAM 32M`, 16-bit, non-shared |
| SPI NOR | `P25D80SH` | Puya 8-Mbit / 1-MiB SPI NOR; raw dump is in `firmware/P25D80SH@SOP8.BIN` | **CONFIRMED** marking + dump size |
| Secondary controller | JieLi/JL logo; top text `AK24 / BB24 / 230` (line joining unresolved; **not a model identifier**) | Controller running JieLi AC695N/BR23-family software | package/logo + runtime lineage **CONFIRMED**; exact public SKU **UNKNOWN** |
| Analog switch | `HCF4052` family marking reported | HCF4052B is a dual 4-channel analog multiplexer/demultiplexer, not a shift register or inverter | part action node **CONFIRMED** by device documentation; exact board routing **UNKNOWN** |
| Logic IC | `74HC04D` marking reported | Six CMOS inverters in one package | part action node **CONFIRMED** by device documentation; exact board role **UNKNOWN** |
| Analog output ICs | `4558D` marking on 8-pin devices near outputs | 4558-family devices are dual operational amplifiers; likely used for analog buffering/filtering/preamplification | part family action node **CONFIRMED**; exact product-board circuit role **LIKELY** |

### SDRAM marking

The board marking still needs a clean macro photo/transcription. A web search found a reseller index entry spelled `306416BTR-6CN PM`, which is close to the reported marking, but no trustworthy datasheet was found that lets us claim the exact part or density. Do **not** silently convert STK's `32M` field into MB or Mbit until the physical part is confirmed.

## Connectors and service interfaces

### UART

The service jumper/header used for the captured boot log routes to the **secondary-controller side** according to the board trace already performed.

Confirmed behavior:
- UART TX produces the AC695N/BR23 boot/runtime log preserved in `evidence/ac695n-boot-excerpt.log`;
- the log includes `UserUartInit success`, `audio_dec_init`, `audio_dac_init`, `ALINK_SR = 44100`, `spdif_dec_start` and volume state;
- typing into the observed debug UART did not produce an interactive shell response.

The RX action node/protocol therefore remains **UNKNOWN**; `UserUartInit success` may refer to another user-UART path.

### SPHE UART candidates for inter-chip tracing

Reference-design evidence gives two multiplexed UART pin pairs on the SPHE8202R-128 GPIO map:

- package pin 11 / GPIO22: `HSYNC(1) / RX(1)`;
- package pin 12 / GPIO23: `VSYNC(1) / TX(1)`;
- package pin 33 / GPIO25: `HSYNC(2) / RX(2) / CARD_SENSE(1)`;
- package pin 45 / GPIO27: `VSYNC(2) / TX(2) / GAME_D1(1)`.

The Sunplus demo board exposes its UART connector using the `V_H_SYNC` / `V_V_SYNC` pair, consistent with the GPIO22/23 alternate UART action node.

The available SPHE8202R design guide documents UART, USB, internal 5.1 DAC, ADC and S/PDIF output, but its searchable text contains no `I2S` or `IIS` interface description. This is **not proof that the silicon lacks another digital-audio interface**; it only means the current reference documentation does not establish one.

For the target PCB, the decisive measurement is continuity from SPHE package pins 11/12 and 33/45 to the secondary controller/test pads. A match to either RX/TX pair would establish an inter-chip UART candidate. Until continuity or execution evidence exists, do not claim that either pair is used between the two processors.

Reference sources:
- Sunplus SPHE8202R Demo Board GPIO list / UART connector.
- Sunplus SPHE8202R Design Guide V2.0, sections 1.2 and 3.6.

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

## Current interface status

| Interface/domain | Current state | What is still missing |
|---|---|---|
| SPHE UART / ROM-loader | **Implementation proof:** factory serial/monitor protocol, RAM-loader, flash read and minimal runtime TX behavior are recovered. Reference pins/bootstrap are identified. | **Board/execution proof:** continuity to accessible pads, I/O voltage confirmation and a successful target session. |
| Secondary-controller UART | **Board proof for TX:** the observed header emits AC695N/BR23-family boot/runtime logs. | RX ownership, interactive command behavior and any control framing are unknown. |
| USB on SPHE | Routing toward SPHE is user-traced; reference design exposes USB DP/DM; target firmware metadata reports **Host USB 2.0 supported**. | Exact pad pinout plus any device/dual-role/UAC capability. Host support must not be promoted into device-mode support. |
| SPHE↔secondary-controller link | No transport is currently confirmed. SPHE UART mux candidates are known from the reference design. | PCB continuity/execution evidence identifying transport, direction, framing and message semantics. |
| Secondary firmware | AC695N/BR23-family identity is supported by runtime logs. | Raw firmware dump/preservation and pi32v2 analysis. |

The secondary UART log contains `ALINK_SR = 44100`, `spdif_dec_start`, DAC and Bluetooth/application activity. Those strings establish behavior inside the secondary firmware, but **do not by themselves identify the electrical/data link between the two processors**.

## Component references

- HCF4052B family: STMicroelectronics dual 4-channel analog multiplexer/demultiplexer.
- 74HC04D: Nexperia hex inverter — https://www.nexperia.com/product/74HC04D
- NJM4558/4558 family: dual operational amplifier — https://www.nisshinbo-microdevices.co.jp/en/products/operational-amplifier/spec/?product=njm4558


### SPHE8202R UART / ROM-loader reference

The Sunplus demo-board reference schematic exposes a dedicated four-pin `CN12 UART`:
- pin 1 = `P+5V`;
- pin 2 = `V_V_SYNC`;
- pin 3 = `V_H_SYNC`;
- pin 4 = `GND`.

Its GPIO list identifies:
- package pin 22: `HSYNC(1) / RX(1)`;
- package pin 23: `VSYNC(1) / TX(1)`.

Therefore the reference-board UART mapping is:
- CN12 pin 2 -> SPHE `TX(1)` through the `V_V_SYNC` multiplexed pin, package pin 23;
- CN12 pin 3 -> SPHE `RX(1)` through the `V_H_SYNC` multiplexed pin, package pin 22;
- CN12 pin 4 -> ground;
- CN12 pin 1 is a +5 V supply and must not be connected directly to a 3.3 V USB-UART signal input.

This is **reference-design evidence**, not continuity proof for PCB
`SPHE8202RD_SPDIF_V02`. The service UART already observed on the product board
routes to the secondary JieLi controller, so it must not be assumed to be the
SPHE ROM-loader UART. The next target-board measurement is continuity from
SPHE package pins 11/12 (GPIO22/23) to any unpopulated header/test pads and
verification of idle voltage before connection.


### SPHE8202R bootstrap / ROM-loader entry

The SPHE8202R-128 reference schematic and independent service practice now agree on the chip-level ROM-loader UART/strap mapping:

- physical package pin 1 = `VFD_CLK`; service practice uses this CLK pin as the bootstrap strap and holds it at GND during reset/power-up to enter boot-trap mode;
- physical package pin 11 = GPIO22 = `V_H_SYNC / RX(1)`;
- physical package pin 12 = GPIO23 = `V_V_SYNC / TX(1)`.

The demo-board `CN12 UART` routes UART1 as:
- connector pin 1 = +5 V supply;
- connector pin 2 = TX1 / `V_V_SYNC`;
- connector pin 3 = RX1 / `V_H_SYNC`;
- connector pin 4 = GND.

Evidence state:
- **CONFIRMED reference/chip mapping:** package pin identities and demo-board routing from the SPHE8202R reference schematic;
- **LIKELY bootstrap contract:** independent SPHE8202R-128 service reports use physical pin 1 / CLK-to-GND to enter boot-trap, consistent with the schematic's pin-1 `VFD_CLK` identity;
- **UNKNOWN target-board access:** the HD Audio Rush PCB has not yet been continuity-mapped from SPHE pins 1/11/12 to accessible pads.

Safe first target-board measurement is therefore continuity only:
1. locate SPHE package pin 1 and find any accessible pad/test point on that net;
2. locate pins 11/12 and identify accessible UART1 RX/TX pads;
3. confirm ground and I/O voltage before connecting an adapter;
4. use a 3.3 V TTL USB-UART for RX/TX; do not apply RS-232 levels and do not infer 5 V UART signaling from the demo connector's +5 V supply pin.

Do not strap pin 1 or power-cycle the target until continuity/pin orientation is independently confirmed on the actual PCB.

## Secondary JieLi package fingerprint — 2026-10-04

Physical continuity on the target PCB is now the authority for package identification. The secondary controller is a 48-pin quad flat package with JieLi/JL logo and top marking transcribed as `AK24 / BB24 / 230` (exact line joining remains uncertain).

Confirmed target-board ground pins by direct continuity to board ground with power removed:
- pin 12 = GND;
- pin 13 = GND;
- pin 36 = GND.

The currently exposed runtime/debug serial connection traces to target package pins 23 and 24 and produces coherent 115200-baud logs. This fact is **not** used to force an identification: pins 23/24 may be muxed GPIO/USB/UART on different JieLi families.

Candidate status is maintained centrally in `docs/jieli-secondary-controller-handoff-20261004.md`.

Closed and not to be re-checked:
- AC6951B/B8;
- AC6951C/C8;
- AC6951G.

Each is impossible against the target because its recovered LQFP48 package map cannot supply three independent ground-class pins under any orientation transform.

Already checked/parked comparison candidates include AC6921A, JL7031C, AC4601, AC6901A and AC6351B/D. Do not repeat their old literal-pin checks; only re-open one if new complete pin-table evidence enables a materially stronger orientation-aware test.

The active unresolved BR23/LQFP48 candidates are AC6951F8 and AC6951T8.

Package top text is not used for model identification. JieLi production/lot markings do not reliably encode the commercial SKU; the target text `AK24 / BB24 / 230` is retained only as a physical observation.


## Provisional three-wire secondary-controller -> SPHE audio link — 2026-10-04

New target-board continuity work indicates that the secondary JieLi device may have only **three signal connections** to the SPHE8202R. The user currently places the SPHE ends approximately at physical package pins **7/8/9**; this exact pin numbering is still **PROVISIONAL** until the three nets are individually recorded.

Reference-package mapping for SPHE8202R-128:
- package pin 7 = `IR / GPIO19`;
- package pin 8 = `GPIO20`;
- package pin 9 = `GPIO21`.

The reference schematic does **not** label these three pins as I2S/IIS/PCM, so the physical role is not proven from the datasheet alone.

However, this continuity observation aligns with independent runtime/static evidence:
- JieLi runtime initializes stereo line input on two LADC channels and reports `ALINK_SR = 44100`;
- the matching JieLi SDK lineage uses ALINK as a digital audio transport;
- SPHE firmware has a dedicated AUX decoder/profile path rather than treating AUX as its on-chip analog ADC path;
- visible SPHE MIPS code does not currently show GPIO19/20/21 being hard-coded as ordinary GPIO pins.

The leading integration hypothesis is therefore a permanently connected **three-wire synchronous stereo audio transport** from JieLi to SPHE, consistent with a `DATA + bit clock + frame/LR clock` topology. Exact signal-to-pin assignment is **not yet proven**.

Do not promote this to board proof until:
1. the three JieLi -> SPHE nets are individually recorded with exact package positions at both ends; and
2. at least one runtime electrical observation distinguishes a frame-rate line, a bit-clock line and a data line (logic analyzer/scope), or an SPHE register contract proves the receiver mapping.

If this model is confirmed, the secondary JieLi should be treated as a **source/audio front-end** (Bluetooth/A2DP, stereo AUX ADC, and possibly S/PDIF handling), while SPHE remains the main system/audio processor.
