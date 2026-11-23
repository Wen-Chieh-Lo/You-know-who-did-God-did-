#!/usr/bin/env bash
set -euo pipefail

project_python="${PROJECT_PYTHON:-python}"
config_path="${1:-configs/full.yaml}"

if "$project_python" -c 'import torch' >/dev/null 2>&1; then
  exec "$project_python" -m twitch_recs.cli advanced --config "$config_path"
fi

itt_archive="/home/laurentlo/miniconda3/pkgs/ittapi-static-3.26.4-hecca717_0/lib/libittnotify.a"
if [[ ! -f "$itt_archive" ]]; then
  echo "PyTorch cannot load and the local Intel ITT compatibility archive is missing." >&2
  exit 1
fi

shim_dir="$(mktemp -d)"
trap 'rm -rf "$shim_dir"' EXIT
gcc -shared -o "$shim_dir/libittnotify.so" \
  -Wl,--whole-archive "$itt_archive" -Wl,--no-whole-archive -ldl -lpthread
LD_PRELOAD="$shim_dir/libittnotify.so${LD_PRELOAD:+:$LD_PRELOAD}" \
  "$project_python" -m twitch_recs.cli advanced --config "$config_path"
