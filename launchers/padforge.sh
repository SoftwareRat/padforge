#!/bin/sh
# PadForge for Linux. Run ./padforge.sh (needs Python 3.9+ and Git).
cd "$(dirname "$0")" || exit 1
exec python3 -m padforge "$@"
