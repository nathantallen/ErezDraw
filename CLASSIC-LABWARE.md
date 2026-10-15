# Classic labware for ErezDraw

This is an original editable vector collection based on the equipment coverage and modular presentation documented for ChemDraw's Clipware, part 1 and Clipware, part 2.

The original ChemDraw .ctp files were not obtained. This is not a conversion of ChemDraw assets, a 90-item replica, or verified identical artwork.

## Use now
Download examples/Classic-Labware.chemjson, open it in ErezDraw, and use Fit to Window. Select a part and copy/paste it into a working drawing. Each apparatus is an integral group. Captions remain separate. Rotate or resize with the selection handles. Save as .chemjson to retain editable strokes.

37 new drawings cover jointed flasks, separatory/addition/filter funnels, condensers, distillation/extraction apparatus, measuring glassware, stands, clamps, heating equipment and accessories. Curved strokes retain Bézier handles rather than raster image outlines.

The combined template sheet and palette contain these 37 plus the existing 31 organometallic/pilot symbols (68 total). The existing new-build palette automatically reads this collection; currently installed apps can use the standalone template document without rebuilding.

## Reference material found
- Revvity's China partner: https://www.chemdraw.com.cn/ruheshiyong/hzzzt-jqmh.html
  Shows the two Clipware panels and describes 90 common apparatus templates and an assembled vacuum-distillation layout.
- Clipware examples: https://cchemdraw.mairuan.com/zhishichubei/clipwarepart-muban.html
- Palette reference image: https://pic.mairuan.com/WebSource/chemdraw/news/images/image%2869%29.png

These references establish the target collection and apparatus categories. They do not establish pixel-identical rendering. No screenshots or ChemDraw template files are redistributed in this collection.

## Source and checks
assets/classic-labware.json holds the original vector definitions and matching SVG thumbnails.
glassware.py prepends these to the prior organometallic/pilot catalog.
Run python glassware.py to regenerate assets/glassware.json.
The validation workflow checks all template pointer interactions, Undo/cancel/copy/rotate/scale and schema roundtrips, catalog consistency, API availability, and SVG XML.
