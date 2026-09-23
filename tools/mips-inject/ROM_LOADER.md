# SPHE8202R headless ROM-loader

`tools/sphe_romloader.py` is a headless reconstruction of the UART loader
path used by STK 0.2.3 rev-8203R.

Current target profile:
- system configuration: `8202 Non Share Mode` (selector 2);
- SDRAM width: 16 bit;
- UART: 8N1;
- baud: 57600 / 115200 / 230400.

The tool extracts the required target RAM-loader directly from the preserved
STK ZIP at runtime. No duplicate loader binary is stored in the repository.

Safe initial operations:

```sh
python3 tools/sphe_romloader.py info

python3 tools/sphe_romloader.py probe \
  --port /dev/ttyUSB0 --baud 115200

python3 tools/sphe_romloader.py read-flash \
  --port /dev/ttyUSB0 --baud 115200 dump-1.bin

python3 tools/sphe_romloader.py monitor \
  --port /dev/ttyUSB0 --baud 115200
```

`upload-ram` transfers an image into the recovered RAM staging area at
`0x0001E000` but intentionally does not issue the final execution/system
switch sequence.

The first hardware session should use `probe` and read-only diagnostics.
No flash-writing command is exposed yet. The final execution/flash route is
being kept separate until rollback/recovery is proven.

Requires Python 3 and `pyserial`.


## Reference UART pins

Sunplus demo-board reference `CN12 UART`:
- pin 1: +5 V supply;
- pin 2: UART1 TX via `V_V_SYNC`;
- pin 3: UART1 RX via `V_H_SYNC`;
- pin 4: GND.

SPHE8202R package mapping from the reference GPIO table:
- package pin 11 = GPIO22 = RX1;
- package pin 12 = GPIO23 = TX1.

Use 3.3 V TTL signaling for TX/RX. Do not drive the logic pins with 5 V merely because the connector also exposes a +5 V supply pin.

On the target HD Audio Rush board this pin route must still be confirmed by continuity. The already observed external UART header is on the secondary controller side.


## Safe first hardware session

Chip-level bootstrap/UART mapping for SPHE8202R-128:
- physical pin 1 = `VFD_CLK` and is used as the boot-trap strap in independent service practice;
- physical pin 11 = UART1 RX / `V_H_SYNC`;
- physical pin 12 = UART1 TX / `V_V_SYNC`.

Before applying the bootstrap strap on the HD Audio Rush PCB, continuity-map those three package pins to accessible pads and confirm package orientation.

Recommended first session:
1. board powered off: continuity-map pin 1, pin 11, pin 12 and GND;
2. connect only GND, adapter RX and adapter TX using a 3.3 V TTL adapter;
3. do not connect the adapter's VCC pin to the board;
4. hold the confirmed pin-1/VFD_CLK bootstrap net at GND;
5. power/reset the board into boot-trap;
6. start with 115200; if communication is unstable, retry 57600;
7. run `probe` first;
8. run `read-flash`;
9. perform a second complete `read-flash`;
10. compare the two reads byte-for-byte and against the preserved canonical 1 MiB dump.

Example:

```sh
python3 tools/sphe_romloader.py probe \
  --port /dev/ttyUSB0 --baud 115200

python3 tools/sphe_romloader.py read-flash \
  --port /dev/ttyUSB0 --baud 115200 dump-1.bin

python3 tools/sphe_romloader.py read-flash \
  --port /dev/ttyUSB0 --baud 115200 dump-2.bin
```

The read-mode RAM stub is instruction-backed to jump around the erase/program route. No `write-flash` command is exposed.

### Logging

The same UART remains usable as a textual console after the ROM-loader/system-switch sequence. The recovered direct UART registers are:
- data: `0xBFFE8900`;
- status: `0xBFFE8904`;
- TX-ready bit: 0;
- RX-ready bit: 1.

`tools/mips-inject/sphe_uart.h` provides freestanding `putc`, `puts`, RX helpers and hexadecimal logging for custom MIPS code without libc.


The low-level `R + address_le32` read transaction is confirmed in the
post-`S` transition, but pre-start Boot-ROM `read32` is not independently
proven.  Therefore the current CLI does not expose a pre-start `read32`
command.  `write32` exists as a recovered low-level primitive but is not part
of the recommended first hardware session.

For a flash-independent custom-code test, build the RAM log probe described in
`RAM_EXEC.md` and use `run-ram`; it executes at `0x80019000` and does not
erase or program SPI flash.


## Recovery implications

The recovered session establishment does not execute the SPI firmware before
the host obtains control.  UART synchronization, system/SDRAM setup, RAM-helper
upload and the `S` transition all occur before the READ/WRITE helper accesses
SPI.  Therefore the implementation model does not depend on a valid user
firmware image in SPI in order to reach the ROM-loader/RAM-helper path.

This makes the chip-level boot strap + UART route a strong recovery candidate
for a corrupted SPI image.  It is not yet board proof: on the HD Audio Rush
PCB we still need to continuity-map physical SPHE pins 1/11/12, enter the
strap successfully, run `probe`, and complete two matching `read-flash`
captures.  Flash writing remains disabled until those recovery prerequisites
are demonstrated on the target.
