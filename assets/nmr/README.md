# Local NMR prediction

Compiled from nmr-predictor 1.2.0 (MIT) queryByHose, openchemlib-extended 4.0.1 (BSD-3-Clause), and its OpenChemLib dependency. Exact dependency versions are recorded in source/package-lock.json; license copies are in licenses/. ErezDraw’s wrapper generates the same HOSE codes directly, avoiding an incompatible legacy graph-distance dependency in normalization. The bundle has no remote fetch path.

Source databases are distributed intact in source/: h1.json is cheminfo-js’s in-house beta proton database; nmrshiftdb2-13c.json is cheminfo-js’s compiled NMRShiftDB2 carbon database. Original URLs: https://raw.githubusercontent.com/cheminfo-js/spectra/master/packages/nmr-predictor/data/h1.json and https://raw.githubusercontent.com/cheminfo-js/spectra/master/packages/nmr-predictor/data/nmrshiftdb2-13c.json . Retrieval: 2026-10-12. SHA-256 fingerprints are in source-sha256.json.

NMRShiftDB2 contributors and compilers retain attribution and database rights; the database remains available under its included nmrshiftdb2 Database License (derived from ODbL), independently of the application’s GPL license. Source: https://nmrshiftdb.nmr.uni-koeln.de/nmrshiftdbhtml/nmrshiftdb2datalicense.txt . The spectra project MIT license is included.

Rebuild: install Node/npm, run npm ci in source/, then npm run build. Node is not required to run ErezDraw or build its Windows executable; the browser bundle is already included.

Predictions use median matched shifts, falling back through five to two HOSE shells. Missing data remains unavailable. Proton coverage is limited; solvent, temperature, exchange, coupling and metal/paramagnetic behavior are not predicted. Reported min/max and standard deviations describe matched database records, not confidence intervals.
