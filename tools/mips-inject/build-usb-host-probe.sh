#!/usr/bin/env bash
set -euo pipefail

OUT="${OUT:-build/usb-host}"
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
clang "${COMMON_FLAGS[@]}" -c usb_host_probe.c -o "$OUT/usb_host_probe.o"

ld.lld -m elf32ltsmip \
  --gc-sections \
  -T ram_exec.ld \
  "$OUT/ram_entry.o" "$OUT/usb_host_probe.o" \
  -o "$OUT/usb_host_probe.elf"

llvm-objcopy -O binary \
  "$OUT/usb_host_probe.elf" \
  "$OUT/usb_host_probe.bin"

SIZE="$(wc -c < "$OUT/usb_host_probe.bin")"
MAX=$((0x4ffc))

echo "USB host RAM probe: $SIZE bytes (max $MAX)"
if (( SIZE > MAX )); then
  echo "ERROR: RAM image exceeds recovered safe execution window" >&2
  exit 2
fi

llvm-objdump -h "$OUT/usb_host_probe.elf"
