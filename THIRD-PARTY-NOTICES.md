# ErezDraw source licensing and attribution

This source distribution is licensed under GPL-3.0-or-later. See COPYING.

The geometry adaptations in `assets/chemgeometry.js` and the associated rendering decisions in `assets/editor.html` are derived in part from ChemCanvas:

- Repository: https://github.com/ksharindam/chemcanvas
- Inspected revision: b0ca821f705a8e39f41e903837af7f91dac997ac
- Sources: chemcanvas/bond.py, chemcanvas/atom.py, chemcanvas/geometry.py
- Copyright (C) 2022–2026 Arindam Chaudhuri
- Upstream license: GPL-3.0-or-later (package metadata); source headers identify GPLv3.

The adaptations translate selected geometric and placement techniques to JavaScript and connect them to ErezDraw's SVG renderer. They are modified implementations, not unmodified ChemCanvas modules. ErezDraw is independent software and is not affiliated with ChemCanvas, ChemDraw or ACD/ChemSketch.

Other installed/bundled dependencies retain their own licenses, including PySide6/Qt, RDKit and PyInstaller. Their notices and licensing terms remain applicable.

## Offline NMR engine and databases

See assets/nmr/README.md for provenance, source data, rebuild instructions and all included dependency/database licenses. nmr-predictor uses MIT, openchemlib-extended uses BSD-3-Clause, and OpenChemLib uses BSD-3-Clause. NMRShiftDB2 data retains its separately included database license. The full bundled input databases are supplied alongside the compiled bundle.
