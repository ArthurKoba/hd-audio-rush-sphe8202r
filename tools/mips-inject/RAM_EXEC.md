# RAM-only diagnostic execution

This probe is the preferred first custom-code test because it does not modify
SPI flash.

The recovered STK flow uploads its own MIPS RAM loader at physical
`0x00019000` and executes it through cached VA `0x80019000`. The same route
can execute a small custom freestanding image.

Build:

```sh
cd tools/mips-inject
./build-ram-log-probe.sh
```

After the target has been put into SPHE boot-trap mode:

```sh
python3 ../sphe_romloader.py run-ram \
  --port /dev/ttyUSB0 --baud 115200 \
  build/ram-log/ram_log_probe.bin
```

Expected console output:

```text
[sphe] RAM execution OK
[sphe] status=0x........
```

The probe then emits the recovered NUL end marker and remains in an infinite
loop until reset/power-cycle.

Execution environment copied from the stock RAM loader:
- `$s6 = 0xBFFE8000`;
- `$sp = 0x80001000`;
- image link address `0x80019000`;
- no `$gp` dependency (`-G0`);
- soft-float, o32, no PIC/no ABICALLS.

Current recovered safe image window is bounded below the firmware staging
metadata at physical `0x0001DFFC`, so the tool rejects RAM executables larger
than `0x4FFC` bytes.

This is execution proof only after it is actually run on hardware. A successful
build is still only implementation proof.
