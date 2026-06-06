#!/usr/bin/env bash
set -euo pipefail

file="${1:-./xyz-10mm-calibration-cube.stl}"
K1C_preset="${2:-./prusa-k1c-config.ini}"


prusa-slicer \
     --load "$K1C_preset" \
     -s \
     "$file"

    # --export-gcode -o /tmp/cube.gcode \
    # --print-settings "0.2mm QUALITY" \
    # --filament-settings "PLA" \
    # --printer-settings "Original Prusa i3 MK3S+" \
    # "$file"