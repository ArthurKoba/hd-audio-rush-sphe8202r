#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

cat <<'EOF'

Ready.

UART example (only when the serial adapter is visible inside WSL):
  .venv/bin/python jieli_uart_probe.py --port /dev/ttyUSB0 --baud 9600 --seconds 10 --out reset_9600.bin

For a Windows COM port, running the probe directly under Windows is usually
simpler. USB UBOOT raw-device access under WSL requires USB passthrough
(typically usbipd-win); a COM mapping alone is not enough.

Do not run erase/write operations against the target.
EOF
