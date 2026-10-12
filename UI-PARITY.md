# Interface comparison — ErezDraw 0.9 development

Reference: CambridgeSoft ChemDraw 8 User's Guide, Macintosh interface on printed page 6, selection/transforms on pages 101–104. Text: https://studylib.net/doc/28511758/chemdraw8 . Illustrated page: https://img.yumpu.com/3581527/26/1800x2304/chemdraw-80-users-manual-cambridgesoft.jpg . The reference images were inspected for development; their artwork is not redistributed in this package.

| Interface area | Result | Remaining difference |
|---|---|---|
| Main Tools | Compact 36-position two-column ordering based on the pictured Mac palette | Original vector recreations; unavailable tools gray |
| Tool families | Icon-grid popouts, default variant selection and tear-off menus | Several variants not implemented |
| General toolbar | Compact original vector file/edit icons, magnification, zoom and chemistry controls | Pixel-level original artwork not claimed |
| Object toolbar | Group/Ungroup, front/back capability indicators and arrangement controls | Layer ordering unavailable |
| Text Style | Font/size and style controls in a separate row | Paragraph alignment and rich scripts unavailable |
| Selection | One dotted enclosure, hatched upper-right/lower-right handles, curved rotation cursor, move cursor | Independent bond selection and exact historical shimmer effects differ |
| Rotate dialog | Degrees CW/CCW, Rotate Atom Labels, Rotate/Cancel | Native Qt control metrics differ |
| Scale dialog | Fixed/median bond-length and percentage choices, Scale Atom Labels | Native Qt control metrics differ |
| Menus | File/Edit/View/Object/Structure/Text/Curves/Color/Window/Help, capability states | Not every edition-specific submenu or advanced dialog exists |
| Document viewport | White canvas with working native scrollbars | Fixed drawing area; no multipage Mac document chrome |
| OS chrome | Native Windows title bar, file dialogs, window management | Historical Aqua title bars, global Mac menu placement and original fonts are not reproduced |

Acceptance: rendered offscreen UI inspected at 1200 × 800. Native palette/capability state tests passed; actual native Rotate/Scale dialogs were exercised. JavaScript model regressions verify that enabled styling/transform/group controls change saved document data and support Undo. Windows appearance, DPI scaling and pixel-by-pixel historical comparison remain unverified. This release does not certify complete UI parity.

Latest development update: the bond/label/mark geometry described in DEVELOPMENT-STATUS.md supersedes the old fixed-margin behavior. A custom Cp centroid tool extends the reference palette. It does not establish complete ChemDraw feature or pixel parity.

The latest update removes TLC and Online, adds a 37-template ligand dock, and implements the current Structure and View menu actions. Arrow full-head/half-head rows increase in arc angle left to right. Native dock layouts and chemistry models differ from ChemDraw.

The Structure Perspective globe icon is now active. It uses a chemical-only marquee enclosure and X/Y drag tilting with Shift constraints; Object > Flatten removes depth.

0.10 adds below-icon family selectors, active Pen/Table/Orbital/Mass Fragmentation controls, rich inline text and an active Text Style bar. Query was removed by request. Spectrum panels and chemistry models are ErezDraw implementations rather than identical ChemDraw dialogs.

0.11 fixes metal charge placement, adds actual draggable spectrum splitters, and provides native macOS build scripts. It does not certify full ChemDraw parity.
