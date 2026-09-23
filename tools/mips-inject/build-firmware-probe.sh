#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="${OUT:-$ROOT/build/compiler-probe}"
STOCK="${STOCK:-$ROOT/firmware/P25D80SH@SOP8.BIN}"
AP1="${AP1:-$ROOT/firmware/modules/ap1.bin}"

mkdir -p "$OUT"

(
  cd "$ROOT/tools/mips-inject"
  OUT="$OUT/mips" ./build-surround-probe.sh
)

python3 "$ROOT/tools/mips-inject/patch_ap1.py" \
  "$AP1" \
  "$OUT/mips/surround_probe.bin" \
  "$OUT/ap1.compiler-probe.bin"

python3 "$ROOT/tools/sunplus_container.py" repack \
  "$STOCK" \
  -o "$OUT/P25D80SH.compiler-probe.bin" \
  --fixed-slot \
  --replace "ap1=$OUT/ap1.compiler-probe.bin"

python3 "$ROOT/tools/sunplus_container.py" inspect \
  "$OUT/P25D80SH.compiler-probe.bin"

echo
echo "Compiler probe image: $OUT/P25D80SH.compiler-probe.bin"
echo "STATIC/REOPEN VALIDATION ONLY — not hardware-accepted yet."
