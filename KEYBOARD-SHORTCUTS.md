# ChemDraw shortcut compatibility

Reference: manufacturer-authored ChemDraw 17.0 User Guide, chapter 5, printed pages 51–61:
https://library.columbia.edu/content/dam/libraryweb/locations/dsc/Software%20Subpages/ChemDraw_17_manual.pdf

This is a tested compatibility subset, not full ChemDraw keyboard parity. Version 17 explicitly repurposes several hotkeys from earlier releases; these mappings follow its published tables rather than guessing a mixture of versions.

## Implemented

Native desktop menu commands: New/Open/Save/Save As, Print/Page Setup/Close, Undo/Redo, cut/copy/paste/select all; F5 actual size, F6 fit page, F7 magnify, F8 reduce, F11 rulers; fixed lengths/angles; group/ungroup; horizontal/vertical flips; Rotate/Scale dialogs; all six alignment commands; cleanup and name conversions; text alignment, plain/bold/italic/underline/formula, F9 subscript and F10 superscript. Ctrl+Shift+V now flips vertically and no longer validates. Ctrl+Shift+Z redoes. Ctrl+Y repeats supported keyboard flips (not arbitrary mouse edits).

The shared canvas resolves modifier combinations exactly, protects ordinary typing in fields and dialogs, and uses Ctrl on Windows / Command on macOS. Text formatting remains available while a label is being edited. Native Qt menu bindings avoid double dispatch.

Hover atom label hotkeys: f/F, p/P, A, h, b/B, i, r, k, s/S, m, n/w/N, c/C/l, x, o/q, d, e/E. Enter edits an atom label. Space/Delete/Backspace removes a hovered label while retaining its atom and bonds. +/- changes formal charge. Basic single, wedge, hashed-wedge, double, triple and dimethyl sprouting is available, with undo. Basic attached phenyl and five/six-member ring placement is available.

Hover bond hotkeys: 1/2/3 order, d dashed, b/B bold single/double, y wavy, w wedge, h hashed-wedge, H hashed bond, l/c/r double-bond alignment, a benzene fusion, v cyclopropane and 4–8 member ring fusion. Each edit has undo.

Away from hotspots: Space marquee, x solid bond, X chain, t text, T brackets, e arrow, E positive-charge symbol, j benzene, J cyclopentadiene, u cyclohexane, U cyclopentane, G orbitals, l pen, L drawing elements. k opens fragmentation in the web/macOS shell; the legacy Windows shell directs users to its Structure menu. Ctrl+Alt+Tab swaps lasso and the preceding tool. Existing Escape cancellation, arrow direction reversal with Alt, selection nudging and constrained transforms remain.

## Still missing or only partially compatible

Do not interpret a shortcut mapping as the implementation of an unsupported ChemDraw feature. Remaining gaps include Copy as CDXML/SMILES/MOL text and paste-format chords, Join, true bond/object stacking F2/F3, 3D 180-degree horizontal/vertical rotations, automatic text justification, arbitrary Repeat Last Command, atom numbering/attachment-point shortcuts, nickname picker, keyboard hotspot traversal, reaction-copy arrow keys, context-dependent acetyl/carbonyl/spiro/phenyl sprouting rules, distinct cyclic versus linear sprouting, full fused cyclopentadiene/chair hotkeys, properties hotkeys, and all modifier-plus-mouse conventions. The removed TLC/query tools intentionally have no tool shortcuts. Native macOS Alt-numpad degree entry is not portable; use Character Map.

The newer Mac shell and the legacy Windows shell have different command adapters. The web shell provides its own save/settings/name/cleanup dialogs; browser-controlled Close and print-page setup remain native-host operations. This change does not claim the full manual's functionality is implemented.
