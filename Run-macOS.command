#!/bin/bash
set -e
cd "$(dirname "$0")"
if [ -d dist/ErezDraw.app ]; then
    open dist/ErezDraw.app
elif [ -x .venv-macos/bin/python ]; then
    .venv-macos/bin/python macos_app.py
else
    echo 'Run Build-macOS.command first.'
    read -r -p 'Press Return to close.'
    exit 1
fi
