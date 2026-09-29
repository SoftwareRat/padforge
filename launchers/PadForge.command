#!/bin/bash
# PadForge for macOS. Double-click to start.
cd "$(dirname "$0")" || exit 1
if python3 -c 'import sys; sys.exit(sys.version_info < (3, 9))' 2>/dev/null; then
  python3 -m padforge "$@"
else
  echo "PadForge needs Python 3.9 or newer. Apple's command line tools include it (and Git):"
  echo "  xcode-select --install"
fi
echo
read -r -p "Press Enter to close this window. "
