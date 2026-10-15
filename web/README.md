# ErezDraw Web

Build and run on a Docker host:

```sh
docker compose up -d --build
```

Open http://HOST:8080/ (port 8080 by default). To use another port:

```sh
EREZDRAW_PORT=8080 docker compose up -d --build
```

The web editor reuses the desktop drawing engine and chemistry modules. It includes
all desktop tool families and variants, ligand templates, periodic table, rich text,
curves, tables, grouping, alignment, rotation/scaling, atom/bond properties,
structure cleanup, abbreviation expansion/contraction, SMILES/name entry,
chemical properties/analysis panels, and local 1H/13C NMR and mass spectra with
assignments and CSV/SVG/PNG exports. Appearance is saved as System/Light/Dark,
with System as the default and a white drawing canvas.

Open editable JSON, MOL/SDF, binary ChemDraw CDX, or ChemDraw XML with either
`.cdxml` or `.cdxl` extensions. ChemDraw import maps supported objects into
editable drawings and reports unsupported content; it is not a lossless round trip.
Download drawings as JSON/MOL/SVG/PNG. Browser autosave and undo/redo are included.
Native windows are replaced with browser dialogs and floating panels. On HTTP,
copy/paste uses the editor clipboard and image/Word transfers use PNG downloads;
system clipboard integration is available where the browser permits it (HTTPS).

Each browser maintains its own local autosave; drawings are not shared or saved
on the server. Download editable .chemjson files for durable backups.
Chemistry requests send a drawing to the service for processing in memory.
HTTP LAN hosting supports file downloads and internal editor copy/paste;
system clipboard APIs require HTTPS in most browsers.

This is a LAN service without authentication. Keep access restricted to the
intended network. Use an authenticated HTTPS reverse proxy before public exposure. Behind such a proxy,
set `EREZDRAW_TRUST_PROXY=1` (and have the proxy send `X-Forwarded-Proto`/`X-Forwarded-Host`)
so the same-origin check accepts the `https://` origin; leave it unset for direct LAN access.
The container runs as a non-root user, with a read-only filesystem and temporary
in-memory scratch space. No document database or server volume is required.

Checks:

```sh
docker compose exec erezdraw python -m unittest web.test_server -v
docker compose ps
docker compose logs --tail 50
```

Document Settings groups Drawing, Text, Page and Ruler preferences. New drawings
use ACS Document 1996: fixed length 14.4 pt, line width 0.6 pt, bold width 2 pt,
margin width 1.6 pt, hash spacing 2.5 pt, bond spacing 18%, chain angle 120°,
Arial 10 pt labels/captions, US Letter with 0.5 in margins. Existing documents
retain their settings; Apply ACS Document 1996 resets the settings without moving
existing atoms. Rulers use mm/cm/in/pt and a fixed document origin. These settings
are included in editable JSON saves. Save asks for a filename before downloading.

Chemical Properties queries PubChem by structure when opened, checks the matched
formula/charge/connectivity, and displays computed and reported physical properties
with source names. The selected molecule is sent to PubChem. The separate Calculated
Properties panel provides offline RDKit estimates. Removed menu commands are absent
from Structure, and Object operations have buttons in the Object actions toolbar.

ACS reference: https://support.revvitysignals.com/hc/en-us/articles/4408234173332
PubChem APIs: https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest
