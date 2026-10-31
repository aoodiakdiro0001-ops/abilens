#!/usr/bin/env bash
# One-time font download for the cover art (OFL-licensed, free).
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p fonts
cd fonts

get() { curl -fsSL "$1" -o "$2" && echo "  ↓ $2"; }

get "https://github.com/google/fonts/raw/main/ofl/tajawal/Tajawal-Bold.ttf"      Tajawal-Bold.ttf
get "https://github.com/google/fonts/raw/main/ofl/tajawal/Tajawal-Regular.ttf"   Tajawal-Regular.ttf
get "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf"      Poppins-Bold.ttf
get "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-SemiBold.ttf"  Poppins-SemiBold.ttf
echo "fonts ready ✅"