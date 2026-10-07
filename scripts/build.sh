#!/usr/bin/env bash
# Rebuild all JSON indexes and the static website.
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd -- "$script_dir/.."

for generator in titles first_lines words lyrics composers lyric_dates composition_dates meters site; do
    uv run "scripts/$generator.py"
done

printf 'Build complete: JSON indexes in indexes/, website in docs/.\n'
