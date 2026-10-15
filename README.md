## Current macOS build from the Docker application

The current Apple-silicon Mac package is `dist/ErezDraw-macOS.zip`. It packages the deployed Docker editor and chemistry engine with native Mac menus and file dialogs, including the latest charge, hover, appearance and export changes. Docker, Python and the hosted server are not needed to run it. See [MACOS.md](MACOS.md) for build instructions, architecture and signing details. The older desktop prototype documentation follows below.

> **Development checkpoint, not a feature-complete release.** Read DEVELOPMENT-STATUS.md for current fixes and limitations.

# ErezDraw — Desktop prototype 0.11 — Windows and macOS

This package contains source and Windows build scripts, not a precompiled executable.

## Build and run

1. Install 64-bit Python 3.12 and the Python Launcher. If needed, run `py install 3.12`.
2. Extract the ZIP into a writable folder.
3. Run **Build-Windows.bat**. It creates `.venv`, installs the pinned dependencies, and builds the application.
4. Open **dist\ErezDraw\ErezDraw.exe**. Keep the entire `dist\ErezDraw` folder together when moving the application.

For development, run **Run-Development.bat** instead. The editor requires no external browser or local server. Dependencies require an internet connection during installation; drawing works offline.

## Interface

The classic interface follows the ChemDraw 8 Macintosh manual's illustrated layout: General and Object toolbars, a Text Style row, and a compact 36-position two-column Main Tools palette. Tool families have icon-grid popouts and tear-off menus. Every toolbar icon is original SVG geometry rather than emoji or platform stock icons. Native Windows window borders and file dialogs remain Windows controls.

- **Selection:** Marquee or Lasso; Shift toggles items; Alt swaps selection tools; double-click selects a connected structure or stored group. Drag within a selection to move it. The upper-right hatched handle rotates; the lower-right handle scales. Shift during resizing allows distortion. The rotation cursor uses a curved-arrow graphic. Arrow keys nudge selections.
- **Object tools:** Group, Ungroup and Make Group Integral; six alignment modes; horizontal/vertical equal-gap distribution; Center on Page; horizontal/vertical flips. Alignment treats a connected molecule as one object. Explicit groups combine their selected members into one alignment unit.
- **Rotate Objects:** enter degrees, choose CW/CCW, optionally Rotate Atom Labels. Ctrl/Command while dragging rotates labels too. A single unselected atom can act as the pivot. Edit > Repeat Rotate reuses the previous angle.
- **Scale Objects:** scale to the configured fixed bond length, a chosen median bond length, or a percentage. Optional Scale Atom Labels changes font size. Double-click the resize handle opens this dialog.
- **Text Style:** font, size, bold, italic, underline, Plain and text color. Changes apply to selected atoms/captions and persist in the editable drawing. Rich runs, scripts and paragraph alignment remain unavailable.
- **Navigation:** magnification control, Magnify/Reduce, Fit Drawing, Actual Size and horizontal/vertical scrollbars. Main Tools and toolbars can be hidden or moved. Right-click opens native object/edit commands.

Gray tools and commands are unavailable. They are not working features. **Complete visual and functional ChemDraw parity is not achieved.** See UI-PARITY.md and FEATURE-AUDIT.md.

## Drawing and files

Draw single/double/triple, solid/hashed wedge and coordination bonds; rings 3–8 and benzene; reaction arrows; atom labels and captions. Click a bond to change its order/type. Ring placement supports centered, atom-attached and fused rings. Text tools edit atom labels. Arbitrary labels such as Y, La and HMDS are permitted.

Save/open `.chemjson` for editable drawings. Import/export MOL V2000; export SVG/PNG. MOL excludes annotations and converts coordination bonds to single bonds. Basic CDX/CDXML import is now implemented in the development checkpoint; see DEVELOPMENT-STATUS.md for limitations. Legacy internal drawing/clipboard identifiers remain supported so existing files are readable. Save operations use atomic replacement and native unsaved-change prompts.

## Chemistry checks and cleanup

Structure > Check Structure runs warning-only RDKit valence/aromaticity checks. Metal/coordination and unsupported-label coverage is explicitly incomplete. No problems detected does not establish stability or synthesizability.

Structure > Clean Up Structure generates consistent 2D coordinates. Selected atoms expand to connected molecules for cleanup; otherwise all molecules are considered. Metal/coordination geometry is protected by default; wedge/hashed components remain unchanged. Cleanup changes coordinates only and supports Undo. Known aliases and stored contracted fragments are expanded for chemical interpretation; unsupported labels remain unchecked.

## Verification

- `node verify-engine.cjs`: drawing, serialization, rotation, resizing-related controls, alignment/distribution, text styling, label transforms, grouping, clipboard and Undo regressions.
- `python -m unittest discover`: chemistry and atomic file-save tests.
- `python verify-desktop-ui.py`: native offscreen Qt controls and live Rotate/Scale dialogs. On Linux, Qt system libraries must also be available.

The release passed those checks in Linux with Qt offscreen rendering. A Windows executable and Windows display/DPI behavior have not been tested here.

ErezDraw is independent software, unaffiliated with ChemDraw or ACD/ChemSketch. RDKit provides chemistry checks and cleanup; PySide6 provides native desktop controls and an embedded offline JavaScript/SVG canvas.

## ChemCanvas adaptations and Cp centroid tool

This development checkpoint incorporates attributed GPL-3.0-or-later adaptations of ChemCanvas's bond geometry and electron-mark placement techniques. See COPYING and THIRD-PARTY-NOTICES.md. The interface remains ErezDraw's classic desktop layout.

Bond clipping, selection bounds, hit testing, Fit and vector export use measured browser font bounds. Ring and substituted double-bond side placement uses topology and nearby atoms; clicking an existing normal double bond with the Double tool cycles left/right/center alignment. Electron symbols are placed in available bond-direction gaps. Atomic label digits are displayed as chemical subscripts.

Choose the **Cp Ring** palette tool, then click the canvas. This creates five carbon atoms, net charge −1, a delocalization circle, and a centroid attachment node. The minus sign is hidden in the drawing; the chemical model retains the formal charge. Switch to **Single Bond** or **Coordination Bond**, drag from the center crosshair to a metal atom, and the bond is attached to the ring centroid. The center follows ring transformations. The Cp ligand is an integral group, and duplication preserves its member/centroid identities.

Centroids are geometric attachment points, not chemical atoms. Standard valence checks do not interpret hapticity or validate metal coordination. Cleanup preserves Cp geometry. **Save .chemjson** to retain the complete drawing. SVG/PNG preserve visible centroid bonds but exclude editing guides. MOL V2000 exports the real atoms and omits centroid attachments, with an explicit notice.

New checks: `node verify-engine.cjs`, `python -m unittest discover`, `python verify-desktop-ui.py`, and `python verify-transfer-ui.py`. The last check exercises real browser metrics inside native Qt and a Cp3Y drawing. Exact ChemDraw parity and Windows rendering remain unverified.

An editable **examples/Cp3Y_centroid.chemjson** drawing is included. Open it from File > Open to inspect three independently attached Cp ligands.

### Perspective Cp rings

Open the Cp palette button’s popup and choose a 30°, 60°, or 75° perspective tilt. Tilt is measured from a face-on ring (0°); larger values produce a narrower projected pentagon. Click to place horizontally, or press at the desired centroid and drag along the major-axis direction to orient the ring. The complete projected ring previews before mouse-up. Draw a bond from its center to a metal using the Single or Coordination Bond tool. Selection rotation changes its orientation on the page.

The five carbon atoms, aromatic decoration, anionic charge and centroid remain tied together through transforms, copy/paste and native saving. These are drawing projections, not calculated 3D structures. Save as .chemjson to preserve centroid attachments; MOL omits the nonchemical centroid and its attachments.

### Arrow palette and chair correction

The arrow popup provides 23 choices: reaction, solid/hollow head, bold/dashed, resonance, equal and unequal equilibrium, opposing full-head arrows, retrosynthetic, no-go, straight/curved half-head, curved full-head, and 90°/120°/180°/270° arc arrows. Equilibrium arrows have two opposing shafts with outward-facing half heads; resonance has two full heads on one shaft. Hold Alt (Option on a Mac keyboard) while drawing to reverse direction, or Alt-click an existing arrow with an arrow tool to reverse it on release. Reversal survives save/open and copy/paste, and Undo restores it. Shapes are not direction-sensitive.

Both cyclohexane chair templates and their palette icons now use the conventional projection with three pairs of opposite parallel bonds. Existing drawings are not silently altered; redraw previously placed malformed chairs with the corrected tools.

Reference: ChemDraw 8 User Guide, chapter 5, arrow drawing/editing and arc tools (https://studylib.net/doc/28511758/chemdraw8). Alt reversal is implemented as requested; this update does not claim every ChemDraw arrow-editing feature. Chair projection checked against the public-domain ChemDraw-created structural formula at https://commons.wikimedia.org/wiki/File:Chair_conformation_of_cyclohexane.svg.

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

Additional text controls: new captions wrap within a 220-unit text box; explicit line breaks are retained. More Colors opens the native custom color picker. Atom labels are limited to 40 characters and captions to 500.

## Release 0.11 — delivered corrections

This revision contains the changes absent from 0.10. Confirm Help > About reports 0.11 after rebuilding and launching the new executable.

- Metal formal charges are rendered as a fixed right superscript within the measured atom label. Bond-direction gaps no longer relocate metal charges. The chemical element and charge remain separate model fields.
- Both NMR spectrum/structure and spectrum/table dividers are real draggable Qt splitters. Mass-fragment windows also use draggable splitters.
- Proton prediction rejects broad, low-detail HOSE matches as precise shifts and uses explicitly labeled approximate environment estimates where supported. The former toluene aromatic fallback at 3.81 ppm is no longer plotted. The monoalkylbenzene estimate gives a methyl singlet near 2.34 ppm and five aromatic protons near 7.16–7.24 ppm. This is an environment estimate, not an experimental or solvent-specific spectrum. Other environments can still be inaccurate or unavailable.
- Small coupled proton components (up to eight spins) use a full isotropic spin Hamiltonian, including estimated aromatic ortho/meta/para couplings; larger components use the existing first-order approximation. Changing MHz changes the coupled spectrum. Lorentzian display integrates each pixel bin so narrow lines are not missed. Provenance is shown in the Shift source column; raw database statistics remain available in CSV.
- Apple-silicon macOS build support is included: native Cocoa controls/global menu bar, Build-macOS.command and Run-macOS.command, producing dist/ErezDraw.app locally on a Mac. Install native Python 3.12, then run Build-macOS.command (or bash Build-macOS.command in Terminal from this folder). This source targets macOS 27; no compiled/notarized Mac binary or Mac runtime verification is provided here. Windows continues to use Build-Windows.bat and dist/ErezDraw/ErezDraw.exe.

Validation: 49 Python tests passed. Native Qt tests exercised actual mouse dragging of both NMR divider handles, live bundled toluene prediction, singlet/coupled aromatic assignments, metal superscript placement, rich text/clipboard and spectrum integration. Drawing-engine regressions passed. A Linux PyInstaller build passed its packaged native-runtime and proton-model check. Actual Windows/Mac execution and Word clipboard behavior still require platform testing.

Useful verification commands: python -m unittest discover; node verify-engine.cjs; python verify-revision-011.py; python verify-expanded-ui.py.

### Appearance

Use **View → Appearance → System, Light, or Dark**. The choice is saved across launches. System is the default on first launch and follows Windows or macOS appearance changes while the app is open. Drawing paper, chemical previews, and spectrum plots stay white; tool icons use light backgrounds for contrast.

Windows appearance fix: rebuild from current source using Build-Windows.bat. The build runs appearance checks and produces dist/ErezDraw-Windows-x64.zip. Older precompiled Windows ZIPs do not contain these changes.


## Glassware & Pilot Equipment

View → Show Glassware Templates opens 31 grouped apparatus symbols, including
Schlenk equipment, vacuum/inert-gas manifolds, jacketed pilot reactors and
Nutsche filters. See [GLASSWARE.md](GLASSWARE.md) for use and the ready-to-open
[template document](examples/Glassware-and-Pilot-Equipment.chemjson).
