# ErezDraw for macOS

This application packages the source extracted from the deployed ErezDraw Docker image in a native PySide6 Mac shell. `macos-source.json` identifies the image and records the original source hashes. The application includes the same drawing tools, ACS document settings, chemical analysis tables, PubChem lookup, ligand templates, NMR/mass tools, CDX/CDXML/CDXL import, transparent exports, atom typing and hover highlights as the deployed website.

The app runs its bundled chemistry service on an automatically selected **127.0.0.1** port, accessible only on the Mac. Docker, a Python installation, an external browser, and the hosted website are not required. PubChem and online name lookups require an internet connection.

Native integration provides the macOS menu bar, Command-key shortcuts, file open/save/export dialogs, printing, saved System/Light/Dark appearance, and local autosave independent of the service port. Drawing canvas and print backgrounds remain white; exported backgrounds are transparent. Autosave is separate from drawings saved in the website and the older desktop shell.

## Build

On Apple silicon with Python 3.12, double-click `Build-macOS.command`. It installs `requirements-macos.txt`, builds `macos_app.py`, signs locally, verifies the signature, creates `dist/ErezDraw-macOS.zip`, and runs the packaged editor/chemistry checks. `Run-macOS.command` runs the app from source.

Outputs: `dist/ErezDraw.app` and `dist/ErezDraw-macOS.zip`.

This build is arm64 (Apple silicon). It is locally ad-hoc signed, not Developer ID signed or Apple notarized. The build report is `build/macos-startup-check.json`.

## Source layout

- `assets/`, `web/`, and the chemistry modules: application source from the running Docker image.
- `macos_app.py`: native app, private local service, menus, file dialogs and autosave.
- `macos/native.js`: integration with the unchanged shared editor.
- `build_macos.py`: application packaging, signing, ZIP and packaged launch check.

GPL-3.0-or-later; third-party notices accompany the application.
