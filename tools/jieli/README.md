# JieLi BR23 / AC695N firmware acquisition

This directory is for **read-only acquisition** of the secondary JieLi firmware.
The current target evidence identifies the controller as BR23 / AC695N-family.

## Safety boundary

The project does not use erase, flash-write, chip-key burning or OTP operations
for acquisition. The first goal is to preserve the existing firmware byte-for-byte.

There are two acquisition paths:

1. **USB UBOOT1.00 (preferred when available).**
   BR23 is supported by `kagaimiq/jl-uboot-tool`. Its loader path can identify
   the SPI NOR device and read the flash without erasing it.
2. **UART Boot ROM (fallback / bring-up path).**
   BR23 Boot ROM has a 9600-baud UART loader receiver, typically on PB5/LDO_IN.
   The public protocol is sufficient to construct and upload a RAM loader, but
   the post-loader flash-read transport is not documented strongly enough here
   to claim a complete UART dumper yet.

Do not send arbitrary commands to the normal runtime/debug UART and do not assume
that the board's exposed logging UART is the Boot-ROM UART until reset-time
behavior proves it.

## Windows: USB UBOOT1.00 dump

Requirements:

- Python 3.10+;
- Git;
- Administrator shell may be required for raw disk/SCSI access;
- the JieLi device must enumerate as something like `BR23 UBOOT1.00`.

Clone the upstream tool:

```powershell
git clone https://github.com/kagaimiq/jl-uboot-tool.git
cd jl-uboot-tool
py -m pip install -r requirements.txt
```

Run the upstream tool in read-only mode:

```powershell
py .\jluboottool.py --chip br23
```

Expected identification for this family is BR23 / AC635N / AC695N.

At the prompt, first run only:

```text
dump 0 256
```

If that succeeds, record the reported online-device ID. Its final JEDEC density
byte normally gives the flash size as `2^N` bytes. Example: density byte
`0x14` -> `2^20` -> 1 MiB.

Then read the complete flash:

```text
read 0 <SIZE> jieli_flash_read1.bin
exit
```

Power-cycle back into UBOOT and repeat into a second file:

```text
read 0 <SIZE> jieli_flash_read2.bin
exit
```

Verify both reads are identical before using the dump for analysis:

```powershell
Get-FileHash .\jieli_flash_read1.bin -Algorithm SHA256
Get-FileHash .\jieli_flash_read2.bin -Algorithm SHA256
fc /b .\jieli_flash_read1.bin .\jieli_flash_read2.bin
```

Do **not** use `write`, `erase`, `erasechip`, `burnchipkey` or OTP commands.

## WSL/Linux: USB UBOOT1.00 dump

When the controller appears as a SCSI generic device such as `/dev/sg0`:

```bash
git clone https://github.com/kagaimiq/jl-uboot-tool.git
cd jl-uboot-tool
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
sudo python3 ./jluboottool.py --device /dev/sg0 --chip br23
```

Use the same `dump` and `read` commands above. In WSL, passing a raw USB
device through to Linux usually requires USBIP/usbipd rather than merely mapping
a Windows COM port.

## UART path

The BR23 Boot ROM UART protocol is documented at 9600 baud. The loader header is
22 bytes and begins with `55 AA`. It carries:

- execution/load address;
- loader length;
- CRC16 of loader data;
- CRC16 of the address/length/data-CRC fields;
- flags, including optional MengLi/CrcDecode decryption;
- requested loader receive baud in 10 kbaud units.

The upstream BR23 UART-loader metadata uses a load address around `0x12000` and
MengLi encryption. The exact UART pin is typically PB5/LDO_IN for BR23-family
Boot ROM, which may be different from the board's normal debug TX/RX UART.

The local `jieli_uart_probe.py` is intentionally non-destructive. It only opens
a serial port, listens at reset-time baud rates and can send the documented sync
prefix when explicitly requested. It does not erase/program flash and does not
yet claim to dump flash over UART.

## Acquisition acceptance

A JieLi firmware dump is accepted only after:

- two independent reads match byte-for-byte;
- SHA-256 is recorded;
- file size matches the detected flash capacity;
- the original dump is kept immutable;
- analysis uses a copy.
