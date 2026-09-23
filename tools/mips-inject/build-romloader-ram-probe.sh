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
)

clang "${COMMON[@]}"   -c romloader_ram_start.S   -o "$OUT/romloader_ram_start.o"

clang "${COMMON[@]}"   -fno-stack-protector   -fno-unwind-tables   -fno-asynchronous-unwind-tables   -fno-exceptions   -O2   -ffunction-sections   -fdata-sections   -c romloader_ram_probe.c   -o "$OUT/romloader_ram_probe.o"

ld.lld -m elf32ltsmip   --gc-sections   -T romloader_ram_probe.ld   "$OUT/romloader_ram_start.o"   "$OUT/romloader_ram_probe.o"   -o "$OUT/romloader_ram_probe.elf"

llvm-objcopy   -O binary   --only-section=.text   "$OUT/romloader_ram_probe.elf"   "$OUT/romloader_ram_probe.bin"

SIZE="$(wc -c < "$OUT/romloader_ram_probe.bin")"
MAX=$((0x1DFFC - 0x19000))

printf 'ROM-loader RAM probe: %d bytes (max %d)\n' "$SIZE" "$MAX"
if (( SIZE > MAX )); then
  echo "ERROR: RAM probe exceeds recovered loader-safe window" >&2
  exit 2
fi

llvm-objdump -h "$OUT/romloader_ram_probe.elf"
llvm-objdump -d "$OUT/romloader_ram_probe.elf"
