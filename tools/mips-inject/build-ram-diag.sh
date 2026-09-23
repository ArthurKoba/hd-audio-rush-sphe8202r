#!/usr/bin/env bash
set -euo pipefail

OUT="${OUT:-build}"
mkdir -p "$OUT"

COMMON=(
  --target=mipsel-none-elf
  -march=mips32 -mabi=32 -msoft-float
  -ffreestanding -fno-builtin -fno-pic -mno-abicalls -G0
  -fno-stack-protector -fno-unwind-tables -fno-asynchronous-unwind-tables
  -Os -fomit-frame-pointer
  -ffunction-sections -fdata-sections
  -I.
)

clang "${COMMON[@]}" -c ram_diag_start.S -o "$OUT/ram_diag_start.o"
clang "${COMMON[@]}" -c ram_diag.c -o "$OUT/ram_diag.o"

ld.lld -m elf32ltsmip -T ram_diag.ld   "$OUT/ram_diag_start.o" "$OUT/ram_diag.o"   --gc-sections -o "$OUT/ram_diag.elf"

llvm-objcopy -O binary "$OUT/ram_diag.elf" "$OUT/ram_diag.bin"

size="$(wc -c < "$OUT/ram_diag.bin")"
printf 'RAM diagnostic size: %d bytes (0x%x)\n' "$size" "$size"

# 0x1DFFC - 0x19000: recovered RAM-stub/staging boundary.
if [ "$size" -gt $((0x4ffc)) ]; then
  echo "ERROR: RAM diagnostic exceeds recovered execution window" >&2
  exit 2
fi

llvm-objdump -h "$OUT/ram_diag.elf"
llvm-objdump -d "$OUT/ram_diag.elf"
