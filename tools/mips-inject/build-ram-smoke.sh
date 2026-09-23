#!/usr/bin/env bash
set -euo pipefail

OUT="${OUT:-build}"
mkdir -p "$OUT"

COMMON=(
  --target=mipsel-none-elf
  -march=mips32
  -mabi=32
  -msoft-float
  -ffreestanding
  -fno-builtin
  -fno-pic
  -mno-abicalls
  -G0
  -fno-stack-protector
  -fno-unwind-tables
  -fno-asynchronous-unwind-tables
  -O2
  -fomit-frame-pointer
  -ffunction-sections
  -fdata-sections
)

clang "${COMMON[@]}" -c ram_start.S -o "$OUT/ram_start.o"
clang "${COMMON[@]}" -c ram_smoke.c -o "$OUT/ram_smoke.o"

ld.lld -m elf32ltsmip \
  --gc-sections \
  -T ram_smoke.ld \
  "$OUT/ram_start.o" "$OUT/ram_smoke.o" \
  -o "$OUT/ram_smoke.elf"

llvm-objcopy -O binary "$OUT/ram_smoke.elf" "$OUT/ram_smoke.bin"

size="$(wc -c < "$OUT/ram_smoke.bin")"
if [ $((size % 4)) -ne 0 ]; then
  echo "ERROR: RAM image is not dword aligned: $size bytes" >&2
  exit 2
fi

echo "Built RAM smoke test at 0x80019000"
llvm-objdump -h "$OUT/ram_smoke.elf"
llvm-objdump -d "$OUT/ram_smoke.elf"
echo "raw_size=$size"
