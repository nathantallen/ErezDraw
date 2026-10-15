# Template selection interaction

Reference: https://www.youtube.com/shorts/dNOwUdyyJOA
Title: ChemDraw Templates Explained: Speed Up Your Chemical Drawings!

The video's auto-generated Hindi transcript was retrieved. The description at
1:35–1:56 explains holding the Templates control, moving to a category, moving
right into its palette, releasing on a template, then clicking the drawing to
place it. Playback was unavailable in this environment, so this update matches
the narrated interaction; identical visual layout is not claimed.

## Use

Press and hold Templates in Main Tools. Hover a category, move across to an
icon, and release to select it. Click the canvas to place it. A normal click
also opens the picker, allowing click-to-select. Escape dismisses it without
changing the document. Keyboard users can open the web picker with Enter,
Space, or Down, use Up/Down between categories, Right into a palette, Tab
between icons, and Enter/Space to select. The Windows native menu also accepts
normal menu navigation and Tab/Enter on icon cells.

The picker includes existing ring tools, all 37 ligands, and all 68 labware /
pilot templates, grouped by their existing categories. The separate searchable
ligand and glassware panels remain available as alternate browsing views.
Choosing an icon changes only the active placement tool. Placement retains the
existing mouse-down preview, mouse-up commit, cancellation, Undo, save/open,
copy/paste and transform behavior.

Benzene already supports Shift to change the alternating bond arrangement,
as described at 0:44–1:03. Existing ring tools still attach or fuse at atoms
and bonds. Arbitrary ligand or labware templates are not fused into molecules.

## Implementation and verification

- template_catalog.py supplies a shared category model.
- template_ui.py implements the native Qt menu and release-to-select cells.
- web/templates.js supplies the Mac/browser cascade with keyboard support.
- test_template_picker.py verifies category coverage, release without a cell
  press, choosing a graphic template, cancellation and keyboard selection.
- verify-template-web.py drives real Qt pointer events through the native
  Mac/web shell: press Templates, hover a category, release on a cell, then
  click the canvas. It also checks that the picker does not consume Escape
  needed to cancel an in-progress drawing gesture.
