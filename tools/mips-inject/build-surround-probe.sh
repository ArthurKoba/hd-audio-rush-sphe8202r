#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-0x80723000}"
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
  -Ttext="$BASE" \
  -e injected_apply_surround \
  "$OUT/surround_probe.o" \
  -o "$OUT/surround_probe.elf"

llvm-objcopy \
  -O binary --only-section=.text \
  "$OUT/surround_probe.elf" \
  "$OUT/surround_probe.bin"

echo "Built MIPS wrapper at $BASE"
llvm-objdump -d "$OUT/surround_probe.elf"
wc -c "$OUT/surround_probe.bin"

if [ "$(wc -c < "$OUT/surround_probe.bin")" -ne 44 ]; then
  echo "ERROR: compiler probe must remain exactly 44 bytes" >&2
  exit 2
fi
