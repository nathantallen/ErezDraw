# Development checkpoint — not a feature-complete release

The next release is being held to the user's feature-completeness requirement. This checkpoint preserves the current fixes; it is not that release and does not certify identical ChemDraw rendering.

Implemented and verified since 0.8:

- Ring double bonds now preserve full outer edges and use shortened internal lines. Acyclic doubles retain their centered presentation. Explicit imported left/right/center positions are supported.
- Dashed, hashed, bold, hollow wedge, wavy and crossed double bonds; zigzag chains; chair and cyclopentadiene templates.
- Basic equilibrium/curved/fishhook arrows, rectangles, ellipses and bracket pairs. These do not provide the full ChemDraw graphics/curve model.
- Charge/radical/unshared-pair tools activate placement mode and operate on clicked atoms. Blank-space clicks create standalone symbols. Radical and lone-pair counts persist in editable files. RDKit receives radical-electron counts; manually placed unshared pairs are graphical annotations rather than a complete electronic-structure model.
- Native File > Open recognizes binary `.cdx` and XML `.cdxml`. Coordinates, standard elements/labels, charges, supported bond styles, double-bond positions, captions and basic graphics are imported. Drawing width/spacing and fonts are imported where supported. Conversion is not lossless. Query atoms, nested fragments, rich text, spectra, TLC, multipage layout and unsupported graphics remain limited or unavailable. Save creates ErezDraw JSON rather than overwriting the source ChemDraw file.

Verification:

- Drawing-engine regressions passed for bond geometry, added tools, symbols, serialization, clipboard and Undo.
- 17 Python tests passed, including CDX/CDXML parsing, signed charge, radical, explicit bond side, malformed/truncated data and XML entity rejection.
- Live native Qt imports passed for six public CDX/CDXML examples, including CambridgeSoft SDK dimethylamine examples and Open Babel ethanol/acetate/methanol/alanine fixtures. Those external fixtures were used for verification and are not bundled here.
- Rendered benzene was visually inspected and has a continuous outer hexagon with the second lines inside.
- Existing live native UI/Rotate/Scale regression passed.

Known gaps still block a feature-complete release. See FEATURE-AUDIT.md and UI-PARITY.md; the historical 0.8 descriptions in those files must be read together with this checkpoint. Exact output equality requires broader reference-file and rendering comparisons, including Windows font/DPI testing.

Potential established engines evaluated by documentation:

- Ketcher: https://github.com/epam/ketcher — offline standalone mode, CDX/CDXML, cleanup, stereochemistry, reaction/query tools. Not incorporated into this checkpoint.
- ChemCanvas: https://github.com/ksharindam/chemcanvas — Python/Qt Windows/Linux desktop editor, CDXML, drawing styles and multipage support. Not incorporated into this checkpoint.

Format references:
https://iupac.github.io/IUPAC-FAIRSpec/cdx_sdk/General.htm
https://iupac.github.io/IUPAC-FAIRSpec/cdx_sdk/IntroCDX.htm
https://iupac.github.io/IUPAC-FAIRSpec/cdx_sdk/properties/Bond_Display.htm

## Latest implemented transfers and Cp tool

Added `assets/chemgeometry.js`, adapted from ChemCanvas with GPL notices. Enabled measured label clipping/selection/export bounds, automatic double-bond side placement and alignment cycling, and neighbor-aware charge/radical/lone-pair placement. ErezDraw's selection/rotation controls remain in use. This implements the first recommended transfer batch; native scene replacement, complete rich text and the remaining drawing/document features in the evaluation are still outstanding.

Added a Cp anion tool with a tied geometric centroid for metal attachments, integral grouping, copy/paste and serialization. The chemical graph contains five carbon atoms with formal charge −1; the centroid is explicitly nonchemical. SVG exports omit editor guides. MOL omits the centroid connections instead of emitting a fake atom. Chemistry validation reports multicenter/metal limitations and cleanup protects ligand geometry.

Passed 20 Python tests, expanded drawing-engine regressions, live Qt transform-dialog tests, and live browser-metrics/Cp3Y integration. The Cp3Y rendering was visually inspected. No feature-complete release is claimed.

## Arrow and creation gesture fix

Native popup QAction checked signals no longer replace tool names with Boolean values. All enabled popup variants are tested through native controls. New bonds, arrows/shapes, rings, chains, Cp templates, atoms and electron symbols preview on mouse-down without changing the document; mouse-up commits once, and cancellation discards the preview. New text opens its editor on release. Verified by verify-arrow-ui.py, verify-engine.cjs, verify-desktop-ui.py and the 20 Python unit tests. Windows packaging still requires a Windows host.

## Perspective Cp tool

Added 30°, 60° and 75° projected Cp anion templates to the Cp palette popup (the Structure menu entries were subsequently removed), with distinct vector icons. Drag sets the in-plane major-axis direction. Inner aromatic decoration derives from the actual ring vertices, so projection follows rotation, scale and mirroring. Retains five-carbon chemistry, centroid attachment, integral selection and native serialization. Engine regressions cover all three tilts, preview/commit, projected decoration, orientation, centroid bonding, round-trip validation, rotation, copy/paste and Undo. Native popup activation and the 20 Python tests pass.

## Structure, View and organometallic update (0.9 development)

- The Cp minus sign is hidden. Cp and increase/decrease-charge entries have been removed from Structure; the Online menu and TLC tool have been removed.
- Structure commands now include molecule name/MW labels, explicit hydrogen addition/removal, abbreviation expansion/contraction, name/SMILES insertion, atom/bond properties and local 1H/13C shift prediction. Labels are editable snapshots, not live calculations. A small offline common-name dictionary is included; PubChem lookup is optional and explicitly sends the entered name or structure when requested.
- NMR uses bundled nmr-predictor HOSE lookup data. Results show shifts, atom assignments, database match counts and ranges and can be exported as CSV. The proton database is small and experimental; unmatched environments show unavailable. Metal complexes and unsupported stereochemistry are rejected. Solvent effects, coupling constants and full spectral simulation are not implemented. This is not ChemDraw's prediction model.
- View provides Analysis, Chemical Properties, Info, Periodic Table, Character Map and Ligand Templates panels, rulers, a movable crosshair, grid and zoom/fit controls. Analysis includes formula, mass, composition and an approximate isotope envelope. Chemical Properties uses RDKit descriptors, not ChemDraw's proprietary physical-property estimates. Multipage layout remains unavailable.
- Open **View > Show Ligand Templates**, or use the ligand palette icon. The 37 templates cover Cp/MeCp/Cp*, indenyl/fluorenyl, haptic alkenes/allyl/arenes, hydride/alkyl/halide, carbonyl/nitrosyl, nitrogen donors and NHC, phosphines, amides, alkoxides, acetylacetonates, ethers and sulfide. Select a template, then press in the canvas to preview and release to place. Connect a donor atom or haptic centroid using the bond tools. Haptic electron counting and metal geometry optimization are not implemented. Save .chemjson to retain centroid attachments.
- The arrow popup places full-head and half-head choices in separate rows, each progressing from straight to 90°, 120°, 180° and 270° left to right, followed by other arrow types.

Verification: 32 Python tests and drawing-engine regressions passed. Live offscreen Qt checks passed for Structure dialogs, hydrogen edits, labels, local NMR assignments, View panels and export-safe guides, all 37 ligand previews/serialization/copy-paste, and arrow ordering. Windows execution and DPI rendering still require a Windows host. The package contains source and Windows launch/build scripts, not a precompiled EXE.

## Windows startup packaging correction

NumPy is now pinned to 2.2.6 and PyInstaller hooks to 2025.2, alongside PyInstaller 6.12.0 and RDKit 2025.3.6. Previously NumPy was an unpinned transitive dependency, so installations could receive a newer native runtime. NumPy is imported before RDKit to surface initial loading errors. Build-Windows.bat now runs a native chemistry/asset self-test inside the generated executable and reports failure before declaring the build ready. This check does not open the editor or verify Windows display behavior.

Extract into a fresh folder and run Build-Windows.bat; a previously built EXE must be rebuilt. Run-Development.bat also installs the pinned versions. The self-test report is build/startup-check.json.

Verification for the startup correction: 32 chemistry tests and the live Structure/View integration checks passed with the pinned NumPy. A Linux PyInstaller onedir build using the same collection/exclusion options successfully ran its packaged native-runtime self-test. Windows-specific DLL loading remains unverified here; the Windows build now executes that test locally before reporting success.

## Structure Perspective tool

Choose the globe/trackball icon near the top of Main Tools. Drag a marquee around atoms, then drag inside its dotted selection rectangle to tilt around X and Y. Hold Shift while dragging to constrain to one axis. Existing atom selections can be used; a single unselected atom in the connected component acts as the fixed pivot. Captions, arrows and shapes do not tilt, and atom labels stay upright. Release commits one Undo operation; Escape, pointer cancellation or switching tools discards an unfinished tilt.

Perspective depth persists in .chemjson, clipboard fragments and MOL V2000 coordinates. Cp/haptic centroids follow the transformed member atoms. Object > Flatten removes stored depth while retaining the displayed XY projection; use Undo to restore the tilt, or cleanup after Flatten to generate a fresh 2D layout. Cleanup protects components with nonzero depth. This is an orthographic drawing manipulation, not conformer generation or metal geometry optimization; wedge/hashed styles remain unchanged. Arbitrary bond-axis rotation controls and depth-dependent bond layering are not provided.

Reference: ChemDraw 8 User Guide, chapter 6, Structure Perspective and Flatten (printed page 102): https://studylib.net/doc/28511758/chemdraw8 . Native Qt pointer tests and drawing-engine regressions passed, including marquee selection, previews, Shift constraints, one Undo, centroid depth, validation and JSON/MOL/clipboard roundtrips. 33 Python tests passed. Windows display behavior remains unverified here.

## Graphics, text, spectra and charge update (0.10 development)

### Drawing and text

The Pen tool places Bézier anchors: click for a corner, or drag at each new anchor to define a tangent. Press Escape to finish. Select an existing curve with Pen to edit anchors and tangent handles. Curves provides open/closed, plain/bold/dashed, black/gray fill, endpoint arrows and point insertion/deletion. Curves retain editable geometry, support selection transforms, saving and copy/paste.

The Table tool previews a grid while dragging; release opens its editor. Change row/column counts and cell text; double-click to edit again. Copy an ErezDraw selection, then use Paste ErezDraw selection into cell to embed a drawing. Nested tables are rejected. Embedded drawings are cell contents rather than independent document chemistry objects.

The Orbital popup supplies s, p, dxy, dz2 and hybrid symbols with outline, gray and opposite-phase fills. Drag from the intended center/node to set size and orientation. These are graphical symbols, not computed wavefunctions.

The Text tool edits atom labels or captions inline. Captions accept newlines; Ctrl+Enter commits, and atom-label Enter commits. Escape cancels; clicking elsewhere or selecting a different tool commits. Select a substring to apply font, size, bold/italic/underline, subscript, superscript, Plain or color. Paragraph controls provide left/center/right/justify and line spacing. Formula applies subscript formatting to formula digits. Rich runs persist through native save and copy/paste. Native Ctrl+B/I/U and text Copy/Cut/Paste are supported. Historical ChemDraw pixel-level typography, rich imported CDX text and all label-positioning rules remain incomplete.

Tool-family selectors now appear below their icons. The Query tool has been removed from Main Tools.

### Predicted NMR and fragment masses

NMR dialogs now show spectra and a linked structure preview. Hover a peak or click its table row to highlight associated atoms. For implicit protons, the parent atom receives an H indicator; explicitly drawn H neighbors are highlighted when available. Frequency is entered as the spectrometer's 1H MHz (40–1200); 13C uses the corresponding carbon frequency. Linewidth is in Hz. Wheel over the plot to zoom; double-click to reset. Copy Spectrum copies the plot as graphics. CSV shift export remains available.

The 1H spectrum uses first-order multiplets with estimated vicinal couplings: 7 Hz for aliphatic carbon neighbors and 8 Hz for aromatic neighbors. Exchangeable O/N protons are uncoupled. Frequency controls J/MHz splitting and linewidth in ppm. These are estimates, not experimentally fitted J values: strong coupling, stereochemistry-dependent J, long-range coupling, solvent and temperature effects are not modeled. 13C is shown proton-decoupled. The underlying proton shift database remains small and some environments have no match.

Mass Fragmentation is active in Main Tools and Structure. It enumerates organic single-bond-cleavage candidates and the precursor, calculates exact singly charged EI or ESI [M+H]+/[M-H]- masses, and links peak hover to fragment atoms. CSV and Copy Spectrum are available. Equal-height candidate markers do not predict observed abundances. Ring-opening/rearrangement, sequential fragmentation, collision energy and metal complexes are unsupported.

### Charges, PubChem and Word

Recognized main-group valence changes update formal charges. Single-metal complexes balance recognized ionic ligand charges against the specified total complex charge. Metal labels show formal charge, including zero. Atom Properties provides automatic/manual control and total complex charge; editing the charge field or using a charge tool selects manual assignment. Multimetal and ambiguous redox cases require manual assignment; this is not a general oxidation-state solver.

PubChem name lookup for a centroid complex uses the real Cp atoms and charged metal/ligand ionic components, excludes virtual centroids, and checks returned canonical structure/formula/charge. It never substitutes a formula/name search when an exact match fails. Cp3Y was verified online as C15H15Y, three Cp anions plus Y3+, CID 16052389. Multimetal centroid queries are rejected as ambiguous. Lookup remains explicit and sends the structure to PubChem.

Copy/Cut provide the editable ErezDraw fragment, SVG, PNG and a high-resolution native bitmap. Word can receive the graphic through the Windows image clipboard; JSON is no longer offered as plain text for drawing copies. NMR and mass plots have Copy Spectrum. Actual Word/Windows clipboard behavior still needs verification on Windows; native Linux clipboard image/SVG tests passed. This does not add ChemDraw OLE editing in Word.

Combined update verification: 43 Python tests passed; expanded drawing-engine tests and live Qt tests passed for rich substring formatting, text clipboard behavior, graphic clipboard formats, table editing, NMR MHz controls and peak assignments, and mass-fragment hover/copy. Native popup tests passed for every enabled family variant. A Linux frozen startup check passed. Native renderings of the tools and spectra were inspected. Windows execution, Word paste and historical ChemDraw pixel parity are not certified.

## Release 0.11 — delivered corrections

This revision contains the changes absent from 0.10. Confirm Help > About reports 0.11 after rebuilding and launching the new executable.

- Metal formal charges are rendered as a fixed right superscript within the measured atom label. Bond-direction gaps no longer relocate metal charges. The chemical element and charge remain separate model fields.
- Both NMR spectrum/structure and spectrum/table dividers are real draggable Qt splitters. Mass-fragment windows also use draggable splitters.
- Proton prediction rejects broad, low-detail HOSE matches as precise shifts and uses explicitly labeled approximate environment estimates where supported. The former toluene aromatic fallback at 3.81 ppm is no longer plotted. The monoalkylbenzene estimate gives a methyl singlet near 2.34 ppm and five aromatic protons near 7.16–7.24 ppm. This is an environment estimate, not an experimental or solvent-specific spectrum. Other environments can still be inaccurate or unavailable.
- Small coupled proton components (up to eight spins) use a full isotropic spin Hamiltonian, including estimated aromatic ortho/meta/para couplings; larger components use the existing first-order approximation. Changing MHz changes the coupled spectrum. Lorentzian display integrates each pixel bin so narrow lines are not missed. Provenance is shown in the Shift source column; raw database statistics remain available in CSV.
- Apple-silicon macOS build support is included: native Cocoa controls/global menu bar, Build-macOS.command and Run-macOS.command, producing dist/ErezDraw.app locally on a Mac. Install native Python 3.12, then run Build-macOS.command (or bash Build-macOS.command in Terminal from this folder). This source targets macOS 27; no compiled/notarized Mac binary or Mac runtime verification is provided here. Windows continues to use Build-Windows.bat and dist/ErezDraw/ErezDraw.exe.

Validation: 49 Python tests passed. Native Qt tests exercised actual mouse dragging of both NMR divider handles, live bundled toluene prediction, singlet/coupled aromatic assignments, metal superscript placement, rich text/clipboard and spectrum integration. Drawing-engine regressions passed. A Linux PyInstaller build passed its packaged native-runtime and proton-model check. Actual Windows/Mac execution and Word clipboard behavior still require platform testing.

Useful verification commands: python -m unittest discover; node verify-engine.cjs; python verify-revision-011.py; python verify-expanded-ui.py.
