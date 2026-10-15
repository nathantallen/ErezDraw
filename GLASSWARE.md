# Glassware & Pilot Equipment

31 editable schematic templates for organometallic apparatus drawings.

## Use the template document with an existing ErezDraw installation

Open `examples/Glassware-and-Pilot-Equipment.chemjson` with File → Open.
Use View → Fit to Window to see the entire sheet. Select a part, copy it,
and paste it into your working document. Each piece is an integral group;
its caption is separate so equipment names need not appear in your drawing.
Keep an unchanged copy of the sheet to reuse.

## Use the built-in palette in a new build

Choose View → Show Glassware Templates. The macOS/browser palette also has a
Glassware button. Search by name or category, choose a symbol, press on the
canvas, drag to position the preview, and release to place it. Escape cancels.
Use the selection tool to rotate or resize the placed group. Undo removes the
entire placement in one step. Object → Ungroup makes individual strokes editable.

Parts are native pen annotations, never chemical atoms, so they do not add
atoms or change formula/MW calculations. Native `.chemjson` saves and graphical
SVG/clipboard exports retain them. Chemical-only MOL/SMILES exports cannot
represent apparatus drawings. These symbols do not model port connectivity,
flow, equipment ratings, physical dimensions, or pressure/vacuum suitability.

## Contents

- Schlenk and round-bottom flasks, three-neck flask, Schlenk tube, valved storage
  ampoule and J. Young NMR tube.
- Septum, cannula, syringe, stopper, stopcock and bent vacuum adapter.
- Fritted Schlenk filter, filter stick, Hirsch/Büchner funnel, dropping funnel
  and pressure-equalizing addition funnel.
- Liebig and cold-finger condensers, vacuum cold trap, bubbler, vacuum-transfer
  receiver and dual vacuum/inert-gas manifold.
- Jacketed stirred reactor, jacketed glass filter reactor, pilot reactor with
  overhead condenser and jacketed receiver/hold vessel.
- Pressure Nutsche filter, agitated Nutsche filter dryer, large glass fritted
  filter funnel and cartridge/bag pressure-filter housing.

## Maintenance

Original geometry is in `glassware.py`. Run `python glassware.py` after edits
to regenerate `assets/glassware.json`. Qt and the local macOS/web API use the
same catalog. `node verify-glassware.cjs` checks every template using the editor's
pointer handlers; `python -m unittest test_glassware` checks catalog consistency
and API availability. `examples/Glassware-template-sheet.svg` previews the set.
