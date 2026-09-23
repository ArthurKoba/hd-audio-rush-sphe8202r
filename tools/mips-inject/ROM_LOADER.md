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

python3 tools/sphe_romloader.py read32 \
  --port /dev/ttyUSB0 --baud 115200 0x1ffe8048

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
