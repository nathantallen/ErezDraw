"""Browser shell and same-origin chemistry API for the shared drawing engine."""
from pathlib import Path
import math
import os
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.exceptions import HTTPException
from chemistry import validate, cleanup
from structure_ops import properties, analysis, from_smiles, hydrogens
from web.desktop_api import run, catalog
from chemdraw_io import import_chemdraw

ROOT = Path(__file__).resolve().parents[1]
app = Flask(__name__, static_folder=None)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
if os.environ.get('EREZDRAW_TRUST_PROXY') == '1':
    # Behind an HTTPS reverse proxy, trust one hop of X-Forwarded-* so the same-origin check sees https://.
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

@app.after_request
def headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'same-origin'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    if request.path == '/' or request.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
    return response

@app.get('/')
def index():
    html = (ROOT / 'assets/editor.html').read_text(encoding='utf-8')
    html = html.replace('</head>', '<link rel="stylesheet" href="/web/style.css"></head>')
    html = html.replace('</body>', '<script src="/web/app.js"></script><script src="/web/templates.js"></script><script src="/web/desktop.js"></script><script src="/web/spectra.js"></script></body>')
    return html

@app.get('/health')
def health():
    return {'status': 'ok', 'application': 'ErezDraw Web'}

@app.get('/web/<path:name>')
def web_asset(name):
    return send_from_directory(ROOT / 'web', name) if name in ('app.js', 'style.css', 'templates.js', 'desktop.js', 'spectra.js', 'nmr-worker.js', 'catalog.json') or (name.startswith('icons/') and name.endswith('.svg')) else ('Not found', 404)

@app.get('/<path:name>')
def asset(name):
    return send_from_directory(ROOT / 'assets', name)

def integer(value, low, high):
    return type(value) is int and low <= value <= high

def graph_input(atoms, bonds, nested=False):
    """Validate atoms/bonds with the editor's document limits (see ChemCore.validate)."""
    if not isinstance(atoms, list) or not isinstance(bonds, list):
        raise ValueError('Invalid drawing or too many atoms/bonds.')
    ids = set()
    for atom in atoms:
        if not isinstance(atom, dict) or not isinstance(atom.get('id'), str) or atom['id'] in ids:
            raise ValueError('Atom identifiers must be unique strings.')
        ids.add(atom['id'])
        if not isinstance(atom.get('label'), str) or len(atom['label']) > 100:
            raise ValueError('Invalid atom label.')
        for axis in ('x', 'y'):
            if isinstance(atom.get(axis), bool) or not isinstance(atom.get(axis), (int, float)) or not math.isfinite(atom[axis]):
                raise ValueError('Invalid atom coordinates.')
        if 'charge' in atom and not integer(atom['charge'], -20, 20) or 'complexCharge' in atom and not integer(atom['complexCharge'], -20, 20):
            raise ValueError('Invalid atom charge.')
        if 'radical' in atom and not integer(atom['radical'], 0, 2):
            raise ValueError('Invalid radical count.')
        if 'explicitHs' in atom and not integer(atom['explicitHs'], 0, 8):
            raise ValueError('Invalid hydrogen specification.')
        if nested and (atom.get('abbreviation') or atom.get('nodeType')):
            raise ValueError('Invalid contracted fragment.')
    pairs = set()
    for bond in bonds:
        if not isinstance(bond, dict) or bond.get('a') not in ids or bond.get('b') not in ids or bond.get('order') not in (1, 2, 3, 4) or isinstance(bond.get('order'), bool):
            raise ValueError('Invalid bond.')
        pair = frozenset((bond['a'], bond['b']))
        if len(pair) != 2 or pair in pairs or not isinstance(bond.get('style', 'normal'), str):
            raise ValueError('Invalid bond.')
        pairs.add(pair)
    return ids

def drawing_input(data):
    drawing = data.get('drawing')
    if not isinstance(drawing, dict):
        raise ValueError('A drawing is required.')
    atoms, bonds = drawing.get('atoms'), drawing.get('bonds')
    if not isinstance(atoms, list) or not isinstance(bonds, list) or len(atoms) > 2000 or len(bonds) > 4000:
        raise ValueError('Invalid drawing or too many atoms/bonds.')
    ids = graph_input(atoms, bonds)
    total = len(atoms)
    for atom in atoms:
        if atom.get('nodeType') == 'centroid' and (not isinstance(atom.get('members'), list) or any(not isinstance(m, str) or m not in ids or m == atom['id'] for m in atom['members'])):
            raise ValueError('Invalid centroid attachment.')
        fragment = atom.get('abbreviation')
        if fragment:
            if not isinstance(fragment, dict):
                raise ValueError('Invalid contracted fragment.')
            inner = graph_input(fragment.get('atoms'), fragment.get('bonds'), nested=True)
            total += len(fragment['atoms'])
            if fragment.get('anchorId', atom['id']) not in inner or total > 2000 or len(fragment['bonds']) > 4000:
                raise ValueError('Invalid contracted fragment.')
    selected = data.get('selected', [])
    if not isinstance(selected, list) or any(x not in ids for x in selected):
        raise ValueError('Invalid selection.')
    return drawing, selected

@app.post('/api/<operation>')
def chemistry(operation):
    origin = request.headers.get('Origin')
    if origin and origin.rstrip('/') != request.host_url.rstrip('/'):
        return {'error': 'Cross-origin requests are not allowed.'}, 403
    data = request.get_json()
    if not isinstance(data, dict):
        raise ValueError('Expected a JSON object.')
    if operation == 'smiles':
        value = data.get('smiles', '')
        if not isinstance(value, str) or not 0 < len(value) <= 1000:
            raise ValueError('Enter a SMILES string of at most 1000 characters.')
        return jsonify(from_smiles(value))
    drawing, selected = drawing_input(data)
    if operation == 'validate': return jsonify(validate(drawing))
    if operation == 'cleanup': return jsonify(cleanup(drawing, bond_length=float(data.get('bondLength',40)), selected_ids=selected, preserve_metals=data.get('preserveMetals',True) is True))
    if operation == 'properties': return jsonify(properties(drawing, selected))
    if operation == 'analysis': return jsonify(analysis(drawing, selected))
    if operation in ('add-hydrogens', 'remove-hydrogens'):
        return jsonify({'drawing': hydrogens(drawing, selected, remove=operation == 'remove-hydrogens')})
    return jsonify(run(operation, drawing, selected, data))


@app.get('/api/catalog')
def desktop_catalog():
    return jsonify(catalog())

@app.post('/api/import-chemdraw')
def chemdraw():
    origin = request.headers.get('Origin')
    if origin and origin.rstrip('/') != request.host_url.rstrip('/'):
        return {'error': 'Cross-origin requests are not allowed.'}, 403
    if 'file' not in request.files: raise ValueError('Choose a CDX, CDXML, or CDXL file.')
    file = request.files['file']
    return jsonify(import_chemdraw(file.read(), Path(file.filename or 'Imported ChemDraw').stem))

@app.errorhandler(Exception)
def error(error):
    if isinstance(error, HTTPException): return {'error': error.description}, error.code
    if isinstance(error, (ValueError, KeyError, TypeError, IndexError)): return {'error': str(error)}, 400
    app.logger.exception('Chemistry request failed')
    return {'error': 'Unable to process this structure.'}, 500

