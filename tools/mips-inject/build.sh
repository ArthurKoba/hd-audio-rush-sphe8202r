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
  -c probe.c -o "$OUT/probe.o"

ld.lld -m elf32ltsmip \
  --defsym=INJECT_BASE="$BASE" \
  --gc-sections \
  -T link.ld \
  "$OUT/probe.o" \
  -o "$OUT/probe.elf"

llvm-objcopy -O binary "$OUT/probe.elf" "$OUT/probe.bin"

echo "Built candidate MIPS injection at $BASE"
llvm-objdump -h "$OUT/probe.elf"
llvm-objdump -d "$OUT/probe.elf"
wc -c "$OUT/probe.bin"
