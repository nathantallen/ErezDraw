# Manual compatibility checklist

Reference: CambridgeSoft *ChemDraw 8 User's Manual*, Chapters 3, 4 and 6, reproduced at https://studylib.net/doc/28511758/chemdraw8 . This review covers implemented drawing tools, not the entire manual.

| Interaction | Prototype result |
|---|---|
| Fixed angles / Alt override (pp. 53–54) | 15° snapping; Alt releases angle and length |
| Wedge/dative direction (pp. 54, 59) | Same-tool click reverses direction |
| Ring attachment (pp. 55–56) | Centered, vertex-attached, bond-fused; drag orientation |
| Eraser (pp. 61, 73) | Reduces order; removes labels while retaining bonds |
| Text-tool atom editing (p. 73) | Supported |
| Selection (pp. 97–99) | Lasso, marquee, Shift toggle, connected-structure selection |

The regression suite exercises these implemented behaviors. Passing logic checks is not equivalent to testing the Windows GUI or proving complete ChemDraw compatibility.

## Remaining differences in implemented features

- Labels are literal strings. Automatic chemical subscripts, automatic label alignment, implicit hydrogen interpretation and nickname expansion are not implemented.
- Double bonds render centered. ChemDraw's above/below/center alignment cycling is not implemented. Quadruple and mixed-style multiple bonds are not implemented.
- Selection is primarily atom-based. Clicking a bond selects its endpoint atoms for manipulation; this is not ChemDraw's independent object selection. Deletion of a selected bond therefore has different semantics. Eraser-based bond deletion avoids this difference.
- Freehand selection uses atom coordinates. It does not require the complete rendered text bounding box to lie inside the loop. Marquee selection checks both arrow endpoints but not every glyph of text.
- Ring geometry covers regular 3–8-membered rings and alternating benzene. Chair templates, cyclopentadiene templates, resonance circles and editable template libraries are absent. Atom merging/ring contraction after dragging one atom onto another is absent.
- Bond-tool double-click edits atom labels; selection-tool double-click selects the connected graph. Double-click bond layering is absent. Hover highlight boxes, adjustable pick tolerance and all documented keyboard mappings are not implemented.
- Rotation now has an interactive handle and exact-angle dialog. Resizing and label-glyph rotation remain absent.
- Captions are single-line plain text. Formatting, sub/superscripts and multiline editing are absent.
- Native clipboard fragments and SVG are supported; proprietary ChemDraw clipboard data and Microsoft Office round-trip editing are absent.
- Print uses the embedded document's current view rather than a full multi-page document layout.
- Native file operations are available, but CDX/CDXML files, page-layout styles and ChemDraw document stationery are not supported.

## Features outside the current prototype

Chemical analysis/formula calculation, SMILES, reaction interpretation, multi-center attachments, bracket groups, radicals/isotopes, query structures, orbitals, curves, TLC plates, tables, object grouping, object ordering, text styling and advanced page layout require further implementation. No unavailable feature is represented as completed.

## Chemistry backend update (0.5)

Warning-only RDKit checks and undoable 2D coordinate cleanup are now implemented. Their behavior is described in README.md. This does not establish equivalence to ChemDraw’s chemical perception or cleanup algorithm. Metal/coordination validation, abbreviation expansion and stereochemical cleanup remain incomplete.

The broader manual feature-area audit is in FEATURE-AUDIT.md. Its verdict is incomplete functionality, not certification.
