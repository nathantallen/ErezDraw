"""Exercise native chemistry dependencies inside the packaged executable."""
from pathlib import Path


def check_runtime(root):
    import numpy as np
    from rdkit import Chem, rdBase
    from rdkit.Chem import Descriptors, rdDepictor
    from structure_ops import from_smiles, properties, analysis

    if not np.isclose(np.linalg.det(np.eye(3)), 1):
        raise RuntimeError('NumPy native linear algebra failed')
    mol = Chem.MolFromSmiles('CCO')
    rdDepictor.Compute2DCoords(mol)
    if not 46 < Descriptors.MolWt(mol) < 47:
        raise RuntimeError('RDKit molecular weight failed')
    drawing = from_smiles('CCO')
    if properties(drawing, [])['formula'] != 'C2H6O':
        raise RuntimeError('Structure interpretation failed')
    analysis(drawing, [])
    from mass_spec import fragmentation
    from nmr_spectrum import multiplet_lines
    if not fragmentation(drawing)['rows'] or len(multiplet_lines({'delta':1,'count':1,'couplings':[{'j':7,'n':2}]},400))!=3:
        raise RuntimeError('Spectrum modules failed')
    from nmr_models import refine_proton_shifts,quantum_lines
    benzene=Chem.MolFromSmiles('c1ccccc1');rows=[{'delta':3.81,'count':6,'attachedAtoms':list(range(6)),'level':2,'std':2.4}]
    refine_proton_shifts(benzene,rows)
    if rows[0]['delta']<6 or len(quantum_lines(benzene,rows,400)[0])!=1:
        raise RuntimeError('Proton model/quantum simulation failed')
    for asset in ('assets/editor.html', 'assets/chemgeometry.js', 'assets/graphics.js', 'assets/text.js', 'assets/charges.js', 'assets/nmr/predictor.js'):
        if not (Path(root) / asset).is_file():
            raise RuntimeError('Missing packaged asset: ' + asset)
    return {'status': 'passed', 'numpy': np.__version__, 'rdkit': rdBase.rdkitVersion,
            'checks': ['NumPy native runtime', 'RDKit coordinates/descriptors',
                       'Structure interpretation/analysis', 'drawing/NMR assets']}
