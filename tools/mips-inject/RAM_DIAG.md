# SPHE8202R RAM diagnostic

This is a minimal flash-independent execution probe for the recovered UART
ROM-loader path.

It is linked for the KSEG0 execution alias at `0x80019000`; the ROM-loader
uploads the raw bytes at physical `0x00019000`. The recovered start sequence
installs jump word `0x08006400`, which transfers control to that RAM location.

The probe initializes only its own stack and uses the recovered UART MMIO
contract from `sphe_rom_uart.h`. It does not erase or program SPI flash.

Build:

```sh
cd tools/mips-inject
bash build-ram-diag.sh
```

Run through the headless loader:

```sh
python3 ../sphe_romloader.py run-ram \
  --port /dev/ttyUSB0 --baud 115200 \
  build/ram_diag.bin
```

The command stays attached to the UART monitor until interrupted with `Ctrl-C`. Expected first console output is `SPHE8202R RAM DIAG`. Commands are:
`?` for help, `p` for `PONG`, and `e` followed by one byte for an
RX/TX echo check.

Validation state: implementation/build harness only until observed on the
target board.
