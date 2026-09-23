#!/usr/bin/env bash
set -euo pipefail

OUT="${OUT:-build}"
mkdir -p "$OUT"

clang --target=mipsel-none-elf \
  -march=mips32 -mabi=32 -msoft-float \
  -ffreestanding -fno-builtin -fno-pic -mno-abicalls -G0 \
  -fno-stack-protector -fno-unwind-tables -fno-asynchronous-unwind-tables \
  -O2 -fomit-frame-pointer \
  -ffunction-sections -fdata-sections \
  -c surround_probe.c -o "$OUT/surround_probe.o"

ld.lld -m elf32ltsmip \
  -T surround_probe.ld \
  "$OUT/surround_probe.o" \
  -o "$OUT/surround_probe.elf"

llvm-objcopy \
  -O binary --only-section=.text \
  "$OUT/surround_probe.elf" \
  "$OUT/surround_probe.code.bin"

CODE_SIZE="$(wc -c < "$OUT/surround_probe.code.bin")"
if [ "$CODE_SIZE" -ne 36 ]; then
  echo "ERROR: compiled direct-JAL wrapper must remain exactly 36 bytes; got $CODE_SIZE" >&2
  exit 2
fi

cp "$OUT/surround_probe.code.bin" "$OUT/surround_probe.bin"

# Preserve the 44-byte stock wrapper window without moving the next action.
# The compiled function already returns at byte 36.  These final two stock
# epilogue instructions are unreachable and serve only as compression-friendly
# padding:
#   jr ra
#   addiu sp,sp,0x18
printf '\\x08\\x00\\xe0\\x03\\x18\\x00\\xbd\\x27' >> "$OUT/surround_probe.bin"

echo "Built in-place MIPS wrapper at 0x80702D0C"
llvm-objdump -h "$OUT/surround_probe.elf"
llvm-objdump -d "$OUT/surround_probe.elf"
wc -c "$OUT/surround_probe.bin"

if [ "$(wc -c < "$OUT/surround_probe.bin")" -ne 44 ]; then
  echo "ERROR: padded compiler probe must remain exactly 44 bytes" >&2
  exit 2
fi
