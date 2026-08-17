#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
APPIMAGE="$SCRIPT_DIR/orca_image/OrcaSlicer_Linux_AppImage_Ubuntu2404_V2.4.2.AppImage"
EXPECTED_SHA256="d12fb8c8eac1aecd2dfb6377acd48f994f8fa439ed5292fa532dd82880f029fd"
MAX_INPUT_BYTES=${ORCA_MAX_INPUT_BYTES:-104857600}
TIMEOUT_SECONDS=${ORCA_TIMEOUT_SECONDS:-900}
CPU_SECONDS=${ORCA_CPU_SECONDS:-900}
VMEM_KB=${ORCA_VMEM_KB:-2097152}
ALLOW_UNSANDBOXED=${ORCA_ALLOW_UNSANDBOXED:-false}

usage() {
  printf 'Usage: %s <input.stl> [orca-slicer-args...]\n' "$(basename "$0")" >&2
}

if [ "$#" -lt 1 ]; then
  usage
  exit 64
fi

INPUT=$1
shift

if [ ! -f "$INPUT" ]; then
  printf 'Input file not found: %s\n' "$INPUT" >&2
  exit 66
fi

case "${INPUT,,}" in
  *.stl) ;;
  *) printf 'Only .stl input files are accepted.\n' >&2; exit 65 ;;
esac

input_size=$(stat -c '%s' -- "$INPUT")
if [ "$input_size" -gt "$MAX_INPUT_BYTES" ]; then
  printf 'Input file too large: %s bytes, max %s.\n' "$input_size" "$MAX_INPUT_BYTES" >&2
  exit 65
fi

actual_sha256=$(sha256sum -- "$APPIMAGE" | awk '{print $1}')
if [ "$actual_sha256" != "$EXPECTED_SHA256" ]; then
  printf 'OrcaSlicer AppImage checksum mismatch.\n' >&2
  printf 'Expected: %s\nActual:   %s\n' "$EXPECTED_SHA256" "$actual_sha256" >&2
  exit 70
fi

WORKDIR=$(mktemp -d)
cleanup() {
  rm -rf -- "$WORKDIR"
}
trap cleanup EXIT

cp -- "$INPUT" "$WORKDIR/input.stl"
ulimit -t "$CPU_SECONDS"
ulimit -v "$VMEM_KB"

if command -v bwrap >/dev/null 2>&1; then
  exec timeout --kill-after=10s "$TIMEOUT_SECONDS" \
    bwrap \
      --die-with-parent \
      --new-session \
      --unshare-all \
      --proc /proc \
      --dev /dev \
      --tmpfs /tmp \
      --tmpfs /run \
      --ro-bind /bin /bin \
      --ro-bind /lib /lib \
      --ro-bind /lib64 /lib64 \
      --ro-bind /usr /usr \
      --ro-bind /etc/ld.so.cache /etc/ld.so.cache \
      --ro-bind "$APPIMAGE" /app/OrcaSlicer.AppImage \
      --bind "$WORKDIR" /work \
      --setenv HOME /work \
      --setenv APPIMAGE_EXTRACT_AND_RUN 1 \
      --chdir /work \
      /app/OrcaSlicer.AppImage --export-gcode /work/input.stl "$@"
fi

if [ "$ALLOW_UNSANDBOXED" != "true" ] || [ "${ORCA_ENV:-production}" = "production" ]; then
  printf 'bubblewrap (bwrap) is required for slicer execution. Unsandboxed mode is blocked unless ORCA_ALLOW_UNSANDBOXED=true and ORCA_ENV is not production.\n' >&2
  exit 70
fi

printf 'WARNING: running OrcaSlicer without bubblewrap; use only for trusted local debugging.\n' >&2
exec timeout --kill-after=10s "$TIMEOUT_SECONDS" "$APPIMAGE" --export-gcode "$WORKDIR/input.stl" "$@"
