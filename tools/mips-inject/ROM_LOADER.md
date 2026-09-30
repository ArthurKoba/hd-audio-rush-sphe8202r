# SPHE8202R headless ROM-loader

`tools/sphe_romloader.py` is a headless reconstruction of the UART loader
path used by STK 0.2.3 rev-8203R.

Current target split:
- firmware/image SDRAM descriptor: `8202 Non Share Mode` (selector 2);
- RomLoader flash-interface profile: `8202L_128_SPI` (selector 7);
- SDRAM width: 16 bit;
- helper flash mode word: `2` (SPI path);
- UART: 8N1;
- baud: 57600 / 115200 / 230400.

The distinction is material.  Selectors 2 and 7 use the same recovered
16-bit system/SDRAM register script, but STK maps them to different helper
mode words: selector 2 -> `0x18FEC=0` and enters the separate memory-mapped
29/39-series flash probe, while selector 7 -> `0x18FEC=2` and selects the
SPI path used by the physical P25D80SH board.  Do not derive the RomLoader
flash-interface profile directly from the firmware SDRAM descriptor.

The tool extracts the required target RAM-loader directly from the preserved
STK ZIP at runtime. No duplicate loader binary is stored in the repository.

Safe initial operations:

```sh
python3 tools/sphe_romloader.py info

python3 tools/sphe_romloader.py probe \
  --port COM3 --baud 115200

python3 tools/sphe_romloader.py read-flash \
  --port COM3 --baud 115200 dump-logical.bin

python3 tools/sphe_romloader.py read-full-flash \
  --port COM3 --baud 115200 dump-physical.bin

python3 tools/sphe_romloader.py monitor \
  --port COM3 --baud 115200
```

`upload-ram` transfers an image into the recovered RAM staging area at
`0x0001E000` but intentionally does not issue the final execution/system
switch sequence.

The first hardware session should use `probe` and read-only diagnostics.
Generic modified-image flash writing is not exposed.  The only write path is
`restore-stock`, which accepts the exact preserved stock image SHA-256 and
requires an explicit full-chip-erase acknowledgement.  Do not use it until
two independent full reads and repeatable boot-trap entry have been proven on
the target.

The factory-equivalent transport requires Windows and uses direct synchronous
Win32 serial I/O. `pyserial` is optional and is used only when
`--transport pyserial` is selected as a portable non-factory extension.


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
8. run `read-full-flash` for the preservation capture;
9. perform a second complete `read-full-flash`;
10. compare the two physical reads byte-for-byte and against the preserved canonical 1 MiB dump; use `read-flash` separately when validating the factory logical-read behavior.

Example:

```sh
python3 tools/sphe_romloader.py probe \
  --port COM3 --baud 115200

python3 tools/sphe_romloader.py read-full-flash \
  --port COM3 --baud 115200 dump-1.bin

python3 tools/sphe_romloader.py read-full-flash \
  --port COM3 --baud 115200 dump-2.bin
```

Only after the read/boot-trap recovery path has been hardware-proven, stock
rollback is available as:

```sh
python3 tools/sphe_romloader.py restore-stock \
  --port COM3 --baud 115200 \
  --confirm-chip-erase \
  firmware/P25D80SH@SOP8.BIN
```

`restore-stock` refuses any image whose size or SHA-256 differs from the
preserved canonical dump.

The vendor read patch is instruction-backed to jump around the erase/program
route. For the target `8202L_128_SPI` profile it must preserve the helper's
SPI word-read action; the direct-memory replacement is only for lower-numbered
non-SPI profiles.

Factory `read-flash` stops when the helper's running 16-bit checksum matches
flash word `+0x20`, yielding the logical encoded-container extent. The
project-specific full physical acquisition is intentionally separate:

`read-full-flash` extends the same SPI/UART route to the known 1 MiB physical
P25D80SH end and rejects any result whose size is not `0x100000`.

No generic `write-flash` command is exposed.  The recovered vendor write
helper performs a full chip erase before programming sequential words from
offset zero, so partial-image writes are not safe through this route.

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


## Factory serial-open compatibility details

The factory transport intentionally mirrors several STK behaviors that are
easy to “improve” accidentally:

- selected port text is limited to 15 characters before Win32 open;
- serial-open success depends only on a valid synchronous `CreateFileW`
  handle;
- configuration helper BOOL returns are ignored after the handle opens;
- status timeout uses integer seconds and expires only when
  `elapsed > limit`;
- every successfully received status byte resets the inactivity origin,
  including bytes ignored by the printable-status parser;
- NUL completion and UI cancellation use the same stop flag.

Portable `--transport pyserial` remains an extension and is not the reference
for one-to-one factory timing/error behavior.
