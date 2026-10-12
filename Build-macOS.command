#!/bin/bash
set -e
cd "$(dirname "$0")"
trap 'echo "Build failed. Review the error above."; read -r -p "Press Return to close."' ERR
if command -v python3.12 >/dev/null 2>&1; then
    runtime=$(command -v python3.12)
elif [ -x /Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12 ]; then
    runtime=/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12
else
    echo 'Install native Apple-silicon Python 3.12 from python.org, then retry.'
    read -r -p 'Press Return to close.'
    exit 1
fi
if [ ! -x .venv-macos/bin/python ]; then "$runtime" -m venv .venv-macos; fi
.venv-macos/bin/python -m pip install -r requirements-macos.txt
.venv-macos/bin/python build_macos.py
open dist/ErezDraw.app
