#!/usr/bin/env bash
set -euo pipefail

OUT="${OUT:-build/ram-log}"
mkdir -p "$OUT"

COMMON_FLAGS=(
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

clang "${COMMON_FLAGS[@]}" -c ram_entry.S -o "$OUT/ram_entry.o"
clang "${COMMON_FLAGS[@]}" -c ram_log_main.c -o "$OUT/ram_log_main.o"

ld.lld -m elf32ltsmip   --gc-sections   -T ram_exec.ld   "$OUT/ram_entry.o" "$OUT/ram_log_main.o"   -o "$OUT/ram_log_probe.elf"

llvm-objcopy -O binary "$OUT/ram_log_probe.elf" "$OUT/ram_log_probe.bin"

SIZE="$(wc -c < "$OUT/ram_log_probe.bin")"
MAX=$((0x4ffc))

echo "RAM execution image: $SIZE bytes (max $MAX)"
if (( SIZE > MAX )); then
  echo "ERROR: RAM image exceeds recovered safe execution window" >&2
  exit 2
fi

llvm-objdump -h "$OUT/ram_log_probe.elf"
llvm-objdump -d "$OUT/ram_log_probe.elf"

echo
echo "Run without touching SPI:"
echo "  python3 ../sphe_romloader.py run-ram --port /dev/ttyUSB0 --baud 115200 $OUT/ram_log_probe.bin"
