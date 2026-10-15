"""Web adapters for the chemistry operations used by the desktop shell."""
import copy, math, urllib.error
from functools import lru_cache
from rdkit import Chem
from rdkit.Chem.Draw import rdMolDraw2D
import structure_ops as ops
from ligands import LIGANDS, ligand_template
from glassware import glassware_catalog
from mass_spec import fragmentation, MODES
from nmr_models import refine_proton_shifts, quantum_lines
from nmr_spectrum import estimate_couplings, multiplet_lines


def nmr_molecule(drawing, selected):
    _, graph, mol = ops.interpreted(drawing, selected, organic=True)
    if mol.GetNumAtoms() > 200:
        raise ValueError('Local NMR prediction is limited to 200 atoms per molecule.')
    if any(b['style'] in ('wedge', 'hash', 'hollowWedge') for b in graph['bonds']):
        raise ValueError('Stereochemical NMR assignments are not supported. Wedge/hash stereo must be unspecified for this model.')
    if any(a.get('radical') for a in graph['atoms']):
        raise ValueError('Radical NMR prediction is outside the model.')
    return Chem.RemoveHs(mol), [a['id'] for a in graph['atoms'] if a['label'] != 'H']


def number(value, low, high, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError('Invalid ' + label)
    return value


def run(operation, drawing, selected, data):
    if operation == 'pubchem-properties': return ops.lookup_structure_properties(drawing, selected)
    if operation == 'expand': return {'drawing': ops.expand(drawing, selected)}
    if operation == 'contract':
        label = data.get('label', '')
        label = label.strip() if isinstance(label, str) else ''
        if not label or len(label) > 40: raise ValueError('Enter an abbreviation of at most 40 characters.')
        return {'drawing': ops.contract(drawing, selected, label)}
    if operation == 'name-to-structure':
        value = data.get('value', '')
        if not isinstance(value, str) or not 0 < len(value) <= 1000: raise ValueError('Enter a chemical name or SMILES.')
        smiles = value if data.get('isSmiles') else ops.name_to_smiles(value, data.get('online') is True)
        return ops.from_smiles(smiles)
    if operation == 'lookup-name':
        if data.get('online') is not True: raise ValueError('Confirm PubChem lookup before sending this structure.')
        try: return ops.lookup_structure_name(drawing, selected)
        except urllib.error.HTTPError as error: raise ValueError('PubChem is temporarily unavailable. Please try again later.') from error
        except (urllib.error.URLError, TimeoutError) as error: raise ValueError('Could not reach PubChem. Check the server internet connection and try again.') from error
    if operation == 'mass':
        mode = data.get('mode', next(iter(MODES)))
        if mode not in MODES: raise ValueError('Invalid ionization mode.')
        result = fragmentation(drawing, selected, mode)
        result['modes'] = list(MODES)
        return result
    if operation == 'nmr-prepare':
        mol, ids = nmr_molecule(drawing, selected)
        return {'molfile': Chem.MolToMolBlock(mol), 'ids': ids}
    if operation == 'nmr-simulate':
        mol, ids = nmr_molecule(drawing, selected)
        nucleus = data.get('nucleus')
        if nucleus not in ('1H', '13C'): raise ValueError('Invalid nucleus.')
        mhz = number(data.get('mhz', 400), 40, 1200, 'frequency')
        if nucleus == '13C': mhz *= .25144953
        rows = copy.deepcopy(data.get('rows'))
        if not isinstance(rows, list) or len(rows) > 1000: raise ValueError('Invalid prediction rows.')
        for row in rows:
            if not isinstance(row, dict): raise ValueError('Invalid prediction row.')
            if row.get('delta') is not None: number(row['delta'], -1000, 2000, 'chemical shift')
            number(row.get('count'), 1, 600, 'nuclei count')
            attached = row.get('attachedAtoms')
            if not isinstance(attached, list) or not attached or any(type(i) is not int or not 0 <= i < len(ids) for i in attached):
                raise ValueError('Invalid atom assignment.')
            for key in ('matches', 'level', 'std'):
                if key in row and row[key] is not None: number(row[key], 0, 1e12, key)
        if nucleus == '1H':
            refine_proton_shifts(mol, rows)
            estimate_couplings(mol, rows)
        coupled = data.get('coupled', True) is True
        lines = quantum_lines(mol, rows, mhz) if nucleus == '1H' and coupled else None
        quantum = lines is not None
        if lines is None: lines = [multiplet_lines(r, mhz, nucleus, coupled) for r in rows]
        for row in rows: row['drawingAtoms'] = [ids[i] for i in row['attachedAtoms']]
        return {'rows': rows, 'lines': lines, 'ids': ids, 'quantum': quantum, 'mhz': mhz}
    raise ValueError('Unknown operation: ' + operation)


@lru_cache(maxsize=1)
def catalog():
    ligands = []
    for category, name, smiles, haptic in LIGANDS:
        mol = Chem.MolFromSmiles(smiles)
        draw = rdMolDraw2D.MolDraw2DSVG(140, 80)
        draw.drawOptions().noAtomLabels = haptic == 'cp'
        draw.DrawMolecule(mol); draw.FinishDrawing()
        ligands.append({'category': category, 'name': name, 'svg': draw.GetDrawingText(), 'template': ligand_template(name)})
    table = Chem.GetPeriodicTable()
    return {'glassware': glassware_catalog(), 'ligands': ligands, 'elements': [{'number': i, 'symbol': table.GetElementSymbol(i), 'name': table.GetElementName(i), 'weight': table.GetAtomicWeight(i)} for i in range(1, 119)]}

