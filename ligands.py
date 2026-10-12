"""Editable ligand templates with real donor atoms and geometric haptic attachment sites."""
from rdkit import Chem
from structure_ops import from_smiles,uid

LIGANDS=[
 ('Haptic','Cp','[CH-]1C=CC=C1','cp'),
 ('Haptic','MeCp','C[C-]1C=CC=C1','cp'),
 ('Haptic','Cp* (pentamethyl-Cp)','C[C-]1C(C)=C(C)C(C)=C1C','cp'),
 ('Haptic','Indenyl','[CH-]1C=Cc2ccccc21','cp'),
 ('Haptic','Fluorenyl','[CH-]1c2ccccc2-c2ccccc21','cp'),
 ('Haptic','η²-Ethylene','C=C','alkene'),
 ('Haptic','η⁴-Butadiene','C=CC=C','diene'),
 ('Haptic','η³-Allyl','[CH2-]C=C','allyl'),
 ('Haptic','η⁶-Benzene','c1ccccc1','arene'),
 ('Haptic','η⁶-Mesitylene','Cc1cc(C)cc(C)c1','arene'),
 ('Anionic donors','Hydride','[H-]',''),
 ('Anionic donors','Methyl','[CH3-]',''),
 ('Anionic donors','Benzyl','[CH2-]c1ccccc1',''),
 ('Anionic donors','Chloride','[Cl-]',''),
 ('Anionic donors','Bromide','[Br-]',''),
 ('Anionic donors','Cyanide','[C-]#N',''),
 ('C / N donors','Carbonyl (CO)','[C-]#[O+]',''),
 ('C / N donors','Nitrosyl (NO)','[N]=O',''),
 ('C / N donors','Acetonitrile','CC#N',''),
 ('C / N donors','Pyridine','n1ccccc1',''),
 ('C / N donors','2,2′-Bipyridine','n1ccccc1-c1ccccn1',''),
 ('C / N donors','TMEDA','CN(C)CCN(C)C',''),
 ('C / N donors','NHC (1,3-dimethylimidazol-2-ylidene)','CN1C=CN(C)[C]1',''),
 ('P donors','Trimethylphosphine','P(C)(C)C',''),
 ('P donors','Triethylphosphine','P(CC)(CC)CC',''),
 ('P donors','Triphenylphosphine','P(c1ccccc1)(c1ccccc1)c1ccccc1',''),
 ('P donors','dppe','P(c1ccccc1)(c1ccccc1)CCP(c1ccccc1)c1ccccc1',''),
 ('O / N / S donors','HMDS (amide)','[N-]([Si](C)(C)C)[Si](C)(C)C',''),
 ('O / N / S donors','Dimethylamide','C[N-]C',''),
 ('O / N / S donors','tert-Butoxide','[O-]C(C)(C)C',''),
 ('O / N / S donors','Isopropoxide','[O-]C(C)C',''),
 ('O / N / S donors','Phenoxide','[O-]c1ccccc1',''),
 ('O / N / S donors','acac (acetylacetonate)','[O-]C(C)=CC(C)=O',''),
 ('O / N / S donors','tmhd / thd','[O-]C(C(C)(C)C)=CC(=O)C(C)(C)C',''),
 ('O / N / S donors','THF','C1CCOC1',''),
 ('O / N / S donors','Diethyl ether','CCOCC',''),
 ('O / N / S donors','Dimethyl sulfide','CSC',''),
]

def ligand_template(name):
    category,name,smiles,haptic=next(item for item in LIGANDS if item[1]==name)
    mol=Chem.MolFromSmiles(smiles);frag=from_smiles(smiles,center=(0,0));frag.update(annotations=[],groups=[],ligands=[])
    if name.startswith('NHC'):
        for i,atom in enumerate(mol.GetAtoms()):
            if atom.GetSymbol()=='C' and atom.GetDegree()==2 and atom.GetNumRadicalElectrons()==2:frag['atoms'][i]['radical']=0;frag['atoms'][i]['lonePairs']=1
    if haptic:
        size={'cp':5,'arene':6,'allyl':3,'alkene':2,'diene':4}[haptic]
        indices=list(range(size)) if haptic in ('allyl','alkene','diene') else list(next(r for r in mol.GetRingInfo().AtomRings() if len(r)==size))
        members=[frag['atoms'][i]['id'] for i in indices];atoms=[frag['atoms'][i] for i in indices];c={'id':uid('centroid'),'x':sum(a['x'] for a in atoms)/size,'y':sum(a['y'] for a in atoms)/size,'label':'','charge':0,'nodeType':'centroid','members':members};frag['atoms'].append(c)
        if haptic=='cp':frag['ligands'].append({'id':uid('cp'),'type':'cp-anion','atomIds':members,'centroidId':c['id']})
    frag['groups']=[{'id':uid('g'),'atoms':[a['id'] for a in frag['atoms']],'annotations':[],'integral':True}]
    return frag
