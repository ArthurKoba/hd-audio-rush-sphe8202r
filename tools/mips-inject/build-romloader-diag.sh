#!/usr/bin/env bash
set -euo pipefail

OUT="${OUT:-build}"
mkdir -p "$OUT"

COMMON_FLAGS=(
  --target=mipsel-none-elf
  -march=mips32 -mabi=32 -msoft-float
  -ffreestanding -fno-builtin -fno-pic -mno-abicalls -G0
)

clang "${COMMON_FLAGS[@]}" \
  -c romloader_diag_entry.S -o "$OUT/romloader_diag_entry.o"

clang "${COMMON_FLAGS[@]}" \
  -fno-stack-protector -fno-unwind-tables -fno-asynchronous-unwind-tables \
  -O2 -fomit-frame-pointer \
  -ffunction-sections -fdata-sections \
  -c romloader_diag.c -o "$OUT/romloader_diag.o"

ld.lld -m elf32ltsmip \
  --gc-sections \
  -T romloader_diag.ld \
  "$OUT/romloader_diag_entry.o" \
  "$OUT/romloader_diag.o" \
  -o "$OUT/romloader_diag.elf"

llvm-objcopy -O binary "$OUT/romloader_diag.elf" "$OUT/romloader_diag.bin"

echo "Built RAM-only diagnostic at 0x80019000"
llvm-objdump -h "$OUT/romloader_diag.elf"
llvm-objdump -d "$OUT/romloader_diag.elf"
wc -c "$OUT/romloader_diag.bin"
