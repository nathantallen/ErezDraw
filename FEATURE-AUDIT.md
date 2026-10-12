# ChemDraw manual audit — prototype 0.9 development

**Verdict: full ChemDraw functionality is NOT implemented.** This is an audit of feature areas across the manual, not a certification of command-by-command parity. The source manual covers several editions. No edition-specific feature is treated as implemented merely because a similar-looking button exists.

Reference: CambridgeSoft ChemDraw 8 manual, https://studylib.net/doc/28511758/chemdraw8 . Reviewed its contents across chapters 1–12 and the detailed selection/rotation instructions on printed pages 101–104. Desktop add-ins are tracked separately because the original project excluded ChemOffice functionality.

Status describes this app. **Implemented** means the stated app capability exists; it does not mean identical ChemDraw behavior. **Partial** means restrictions or differences remain. **Missing** means no usable implementation. **Untested** identifies runtime verification still needed.

| Area | Status | Current app / concrete gap |
|---|---|---|
| Menus/toolbars | Implemented | Native Qt menus and dockable toolbar/palette. |
| Preferences | Partial | Few settings; no complete preference system. |
| Documents | Partial | One document per window; JSON save/open; no document tab manager. |
| Printing | Partial / untested | Native print dialog; current viewport rather than document pagination. |
| Drawing settings | Partial | Length/angle constraints; no full per-object style controls. |
| Bond drawing | Implemented | Single/double/triple, wedge/hash and directed coordination lines. |
| Bond variants | Partial | Dashed, hashed, bold, hollow wedge, wavy and crossed double; mixed/quadruple tools incomplete. |
| Bond alignment | Implemented | Topology-aware internal ring double bonds and left/right/center cycling. |
| Ring drawing | Partial | Regular 3–8 rings, benzene, atom attachment and fusion. |
| Ring variants | Partial | Chair, cyclopentadiene and projected Cp templates; not every historical template. |
| Chain tool | Implemented | Zigzag chain drawing. |
| Bond editing | Partial | Change order/style and reverse wedge/coordination direction. |
| Atom merging | Missing | Overlapping vertices are not automatically merged on drag. |
| Bond layering | Missing | No crossing/layer ordering controls. |
| Warnings | Partial | Manual RDKit check; no automatic live checks. |
| Name conversion | Partial | Local common-name dictionary, SMILES insertion, optional explicit PubChem lookup; no general offline IUPAC naming. |
| Labels | Partial | Plain labels and a limited set of chemically interpreted aliases. |
| Rich text | Implemented / partial | Inline rich runs, scripts, font/style/color and paragraph controls; historical/imported rich text parity incomplete. |
| Label alignment | Missing | No chemistry-aware label positioning. |
| Hotkeys | Partial | Limited selection-label shortcuts, not complete hover/custom mapping. |
| Atom numbering | Missing | No numbering indicators or editing. |
| Orbitals | Partial | s/p/dxy/dz2/hybrid graphical symbols, three fill styles; not all historical projections. |
| Symbols | Partial | Charges/radicals/lone pairs; recognized automatic valence and single-metal ionic charge balancing; ambiguous chemistry requires manual assignment. |
| Arrows | Partial | 23 variants, full/half-head arc rows, Alt reversal; advanced editing differs. |
| Shapes/brackets | Partial | Rectangles, ellipses and bracket pairs; no full graphics model. |
| Arcs/curves | Partial | Preset arrow arcs/curves; no general Bezier editor. |
| TLC | Removed by request | No TLC tool. |
| Selection | Partial | Marquee/lasso; atoms and annotations, not independent bond objects. |
| Movement | Implemented | Drag, axis constraint and keyboard nudge. |
| Clipboard | Implemented / partial | Editable fragment plus SVG/PNG/native bitmap for Word; no ChemDraw OLE, Windows Word unverified. |
| Duplication | Partial | Copy/paste; no modifier-drag duplication. |
| Rotation | Implemented / partial | Upper-right drag handle, exact angle, repeat and single-fixed-atom pivot. Optional label glyph rotation is implemented. |
| Perspective | Implemented / partial | X/Y trackball, Shift axis constraint, retained depth and Flatten; no optimized 3D model, arbitrary bond-axis controls or depth-dependent layering. |
| Reflection | Implemented | Horizontal and vertical geometry reflection; text remains readable. |
| Scaling | Partial | Resize handle, fixed/median bond length and percentage scaling, optional font scaling, Shift distortion. |
| Joining/grouping | Partial | Persistent Group/Ungroup/integral groups; Join and nested/inherited groups unavailable. |
| Nicknames | Partial | Known alias expansion and lossless stored fragment contraction; no full nickname library. |
| Multicenter bonds | Partial | Geometric centroid attachments for haptic ligands; no full multicenter chemical semantics. |
| Cleanup | Partial | RDKit 2D layout, preserving sensitive geometry by default. |
| Colors | Partial | Text colors; no per-bond/object color or custom palette. |
| Templates | Partial | Rings plus 37 organometallic ligand templates; no general user template library. |
| Chemistry checking | Partial | Organic valence/aromaticity; metal/unknown chemistry remains unchecked. |
| Analysis | Implemented / partial | Formula, molecular/exact mass, composition and approximate isotope envelope; metal interpretation limited. |
| Stereochemistry | Partial | Draws wedge/hash; no R/S/E/Z assignment or stereo-safe cleanup. |
| Properties/3D | Partial | RDKit descriptor panel; no ChemProp physical-property model or 3D conversion. |
| Spectra/NMR | Partial | Local shifts, estimated first-order 1H multiplets/MHz/linewidth and decoupled 13C, linked hover; exact J/strong coupling and metal prediction absent. |
| Query structures | Missing | No query atoms/bonds, alternative groups or generic match rules. |
| Polymers/mapping | Missing | No repeat-unit model or atom-to-atom reaction maps. |
| Page layout | Missing | No multipage/poster setup, headers, footers or stationery. |
| Zoom/fit | Implemented | Wheel navigation, zoom control, fit and actual size. |
| Rulers/guides | Implemented | Zoom-aware rulers, movable crosshair and grid; fixed document area. |
| Alignment/distribution | Partial | Six alignment commands and two equal-gap distributions; front/back ordering unavailable. |
| Tables | Partial | Editable text and embedded drawing cells, row/column controls; no spreadsheet calculations or nested tables. |
| String exchange | Partial | SMILES input through name/structure dialog; no SMIRKS or SLN UI. |
| Drag/drop/OLE | Missing | No file drag/drop or Office object embedding. |
| File exchange | Partial | JSON, MOL V2000, SVG/PNG and basic CDX/CDXML import; no lossless ChemDraw round-trip. |
| Online/SDK | Removed / partial | Online menu removed; explicit optional PubChem lookup; no legacy SDK integration. |
| Office add-ins | Outside original scope | Not implemented. |

## Rotation acceptance and evidence

Selection tools expose a hatched upper-right handle. Dragging rotates about the selection rectangle center; a single unselected atom in the connected structure becomes a fixed pivot. Labels stay upright. Object → Rotate and double-clicking the handle open the native exact-angle dialog with clockwise/counterclockwise choices. Edit → Repeat Rotate reuses the previous angle. Rotation is one undoable operation. Shift snapping is an additional editor convenience, not a claimed manual-equivalent shortcut.

Passed: graph harness tests for handle rotation, clockwise/counterclockwise numeric rotation, single-atom pivot, reaction-arrow endpoint rotation, Undo/Redo and dialog request; live Qt offscreen tests for the native dialog, angle application, native Undo and handle-to-dialog request. Windows packaging and visible Windows interaction remain untested. Caption positions rotate, while their glyphs remain upright; optional label-glyph rotation is now supported.

## Remaining daily-use priorities

Remaining priorities include independent bond selection, rich text, complete object styling, broader document layout and lossless ChemDraw interchange. Haptic templates and local NMR do not provide a complete organometallic chemical model.

### Revision 0.7

Implemented six alignment commands, two equal-gap distribution commands, centering within the fixed drawing area, vertical flipping, numeric geometry scaling and lower-right drag resizing. Selection outlines/handles use monochrome styling. Group/Ungroup, integral groups, label scaling, arbitrary page dimensions, full object styling and exact visual parity remain missing. Existing selection of bond endpoints also remains a known limitation. Full ChemDraw parity is not achieved.

### Revision 0.8 — current state

The 0.7 paragraph above records historical gaps. This revision adds Group/Ungroup and integral group selection, label-glyph rotation and label/font scaling, persisted text styling, icon-grid popouts, classic toolbars and palette order, selection cursors/hatched handles and document scrollbars. Grouping remains partial: nested groups and inherited membership for newly attached atoms are unavailable. Full UI parity remains unverified and incomplete: some tool families and advanced dialogs are unavailable, and operating-system controls differ.

Pen Bézier anchors/tangents and curve styles are now available. Mass fragmentation enumerates exact-mass cleavage candidates rather than predicting empirical spectra.
