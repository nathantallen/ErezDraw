# ChemDraw shortcut compatibility

Reference: manufacturer-authored ChemDraw 17.0 User Guide, chapter 5, printed pages 51–61:
https://library.columbia.edu/content/dam/libraryweb/locations/dsc/Software%20Subpages/ChemDraw_17_manual.pdf

This is a tested compatibility subset, not full ChemDraw keyboard parity. Version 17 explicitly repurposes several hotkeys from earlier releases; these mappings follow its published tables rather than guessing a mixture of versions.

## Implemented

Native desktop menu commands: New/Open/Save/Save As, Print/Page Setup/Close, Undo/Redo, cut/copy/paste/select all; F5 actual size, F6 fit page, F7 magnify, F8 reduce, F11 rulers; fixed lengths/angles; group/ungroup; horizontal/vertical flips; Rotate/Scale dialogs; all six alignment commands; cleanup and name conversions; text alignment, plain/bold/italic/underline/formula, F9 subscript and F10 superscript. Ctrl+Shift+V now flips vertically and no longer validates. Ctrl+Shift+Z redoes. Ctrl+Y repeats supported keyboard flips (not arbitrary mouse edits).

The shared canvas resolves modifier combinations exactly, protects ordinary typing in fields and dialogs, and uses Ctrl on Windows / Command on macOS. Text formatting remains available while a label is being edited. Native Qt menu bindings avoid double dispatch.

Hover atom label hotkeys: f/F, p/P, A, h, b/B, i, r, k, s/S, m, n/w/N, c/C/l, x, o/q, d, e/E. Enter edits an atom label. Space/Delete/Backspace removes a hovered label while retaining its atom and bonds. +/- changes formal charge. Basic single, wedge, hashed-wedge, double, triple and dimethyl sprouting is available, with undo. Basic attached phenyl and five/six-member ring placement is available.

Hover bond hotkeys: 1/2/3 order, d dashed, b/B bold single/double, y wavy, w wedge, h hashed-wedge, H hashed bond, l/c/r double-bond alignment, a benzene fusion, v cyclopropane and 4–8 member ring fusion. Each edit has undo.

Away from hotspots: Space marquee, x solid bond, X chain, t text, T brackets, e arrow, E positive-charge symbol, j benzene, J cyclopentadiene, u cyclohexane, U cyclopentane, G orbitals, l pen, L drawing elements. k opens fragmentation in the web/macOS shell and the native Windows shell. Ctrl+Alt+Tab swaps lasso and the preceding tool. Existing Escape cancellation, arrow direction reversal with Alt, selection nudging and constrained transforms remain.

## Still missing or only partially compatible

Do not interpret a shortcut mapping as the implementation of an unsupported ChemDraw feature. Remaining gaps include Copy as CDXML/SMILES/MOL text and paste-format chords, Join, true bond/object stacking F2/F3, 3D 180-degree horizontal/vertical rotations, automatic text justification, arbitrary Repeat Last Command, atom numbering/attachment-point shortcuts, nickname picker, keyboard hotspot traversal, reaction-copy arrow keys, context-dependent acetyl/carbonyl/spiro/phenyl sprouting rules, distinct cyclic versus linear sprouting, full fused cyclopentadiene/chair hotkeys, some modifier-plus-mouse conventions. The removed TLC/query tools intentionally have no tool shortcuts. Native macOS Alt-numpad degree entry is not portable; use Character Map.

The newer Mac shell and the legacy Windows shell have different command adapters. The web shell provides its own save/settings/name/cleanup dialogs; browser-controlled Close and print-page setup remain native-host operations. This change does not claim the full manual's functionality is implemented.

## Copy/drag follow-up audit (2026-10-14)

The shared canvas could handle Copy in its internal clipboard even when the system clipboard was needed. A native WebChannel command adapter now routes canvas commands to the Windows shell. Copy/Cut/Paste/Select All also handle WebEngine shortcut overrides at the focused view, while preserving ordinary text fields and inline rich labels. Native operations are dispatched once, with tests for the system fragment, SVG and PNG MIME data, cut/paste, native Save As and flip/repeat.

Ctrl-drag and Ctrl+Shift-drag now duplicate a selection (Shift constrains X/Y), preserve originals, create independent atom/bond/annotation/group/ligand IDs, retain centroid membership, preserve the existing clipboard, and commit one undo step on release. Drag cancellation restores the document. A Ctrl-click or tiny pointer movement does not duplicate or move the selection. Mac Option-drag is accepted as well. Tests cover molecules, captions/arrows, groups and Cp centroids; a native Qt mouse test covers preview, commit and undo.

Selected-object Delete/Backspace now takes priority over the hovered-atom label-removal hotkey. Slash or question mark opens existing atom/bond properties dialogs, and `k` reaches the native fragmentation dialog. The latter and properties bindings were previously missing native routes.

### Remaining keyboard gaps

| Keyboard input | Current limitation |
| --- | --- |
| Ctrl+D | Copy as CDXML is not implemented. |
| Ctrl+Alt+C | Copy as SMILES has no shortcut/clipboard command. |
| Ctrl+Alt+Shift+O | Copy as MOL text has no shortcut/clipboard command. |
| Ctrl+Alt+P; Ctrl+Alt+Shift+P | Paste as SMILES / MOL / CDXML has no format-specific shortcut. File imports remain available. |
| Ctrl+J | Join is not implemented. |
| F2 / F3 | True object/bond front/back stacking is not implemented. |
| Ctrl+Alt+Shift+H / V | 180-degree 3D rotations around horizontal/vertical axes are not implemented. These differ from ordinary flips. |
| Ctrl+Shift+M | Automatic text justification is not implemented. |
| Ctrl+Y | Repeats supported keyboard flips, not arbitrary last edits. |
| Atom apostrophe, period, equals | Atom numbering, attachment-point and nickname-picker shortcuts remain missing. |
| Arrow / Shift+Arrow hotspot navigation | Arrow keys currently nudge a selection; hotspot traversal is missing. |
| Ctrl+Arrow reaction-copy | Automatic reaction-arrow/duplicate layout is missing. |
| Atom 2, 0/1, 3/a, 4/5, 6/7, 9, z | Several context-dependent carbonyl, spacer, sprouting and linear/cyclic rules remain partial or missing. |
| Bond z, 9/0, f | Fused cyclopentadiene/chair variants and individual bond-front hotkeys remain missing. |
| Ring Ctrl-click, chain Ctrl-drag | Delocalized-ring and chain-direction modifier behavior is missing. |
| Other modifier/mouse combinations | Not all manual conventions have a native integration regression test. Ctrl+Alt+Tab can also be intercepted by the OS. |

TLC/query tool shortcuts remain intentionally absent because those tools were removed by request. Native macOS/Word execution is not implied by Linux or Windows runner checks.
