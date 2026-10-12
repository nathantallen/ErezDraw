"""Exact-mass single-bond-cleavage candidates; not an empirical intensity model."""
from collections import Counter
from rdkit import Chem
from structure_ops import interpreted
ELECTRON_MASS=0.000548579909065
MODES={'EI molecular radical cation':(0,1),'ESI [M+H]+':(1,1),'ESI [M-H]-':(-1,-1)}

def formula(counts,charge=0):
    keys=sorted(counts,key=lambda k:(0 if k=='C' else 1 if k=='H' else 2,k))
    text=''.join(k+(str(counts[k]) if counts[k]!=1 else '') for k in keys if counts[k])
    return text+('+' if charge==1 else '-' if charge==-1 else '')

def fragmentation(drawing,selected=(),mode='EI molecular radical cation'):
    if mode not in MODES:raise ValueError('Unsupported ionization mode.')
    fragment,graph,mol=interpreted(drawing,selected,organic=True)
    if mol.GetNumAtoms()>150:raise ValueError('Fragment enumeration is limited to 150 atoms.')
    if Chem.GetFormalCharge(mol):raise ValueError('Start with a neutral organic precursor; precharged ions require a charge-retention model.')
    table=Chem.GetPeriodicTable();delta,charge=MODES[mode];atom_counts=[]
    for atom in mol.GetAtoms():
        counts=Counter({atom.GetSymbol():1})
        if atom.GetSymbol()!='H':counts['H']+=atom.GetTotalNumHs(includeNeighbors=False)
        atom_counts.append(counts)
    def ion(indices,bond=None,complement=()):
        counts=Counter()
        for i in indices:counts.update(atom_counts[i])
        neutral=sum(table.GetMostCommonIsotopeMass(table.GetAtomicNumber(k))*n for k,n in counts.items())
        ion_counts=counts.copy();ion_counts['H']+=delta
        if ion_counts['H']<0:return None
        mass=neutral+delta*table.GetMostCommonIsotopeMass(1)-charge*ELECTRON_MASS
        return {'mz':mass,'formula':formula(ion_counts,charge),'drawingAtoms':[graph['atoms'][i]['id'] for i in sorted(indices)],'bond':bond,'neutralLoss':None if not complement else formula(sum((atom_counts[i] for i in complement),Counter())),'precursor':bond is None}
    all_ids=set(range(mol.GetNumAtoms()));rows=[ion(all_ids)];seen=set()
    # Ring opening alone does not separate an ion: enumerate only graph bridges.
    for bond in mol.GetBonds():
        if bond.GetBondType()!=Chem.BondType.SINGLE or bond.IsInRing() or bond.GetBeginAtom().GetSymbol()=='H' or bond.GetEndAtom().GetSymbol()=='H':continue
        a,b=bond.GetBeginAtomIdx(),bond.GetEndAtomIdx();visited=set();todo=[a]
        while todo:
            i=todo.pop()
            if i in visited:continue
            visited.add(i)
            for neighbor in mol.GetAtomWithIdx(i).GetNeighbors():
                j=neighbor.GetIdx()
                if {i,j}!={a,b}:todo.append(j)
        if b in visited:continue
        for ids in (visited,all_ids-visited):
            key=tuple(sorted(ids))
            if key in seen:continue
            seen.add(key);row=ion(ids,[graph['atoms'][a]['id'],graph['atoms'][b]['id']],all_ids-ids)
            if row:rows.append(row)
    return {'mode':mode,'rows':sorted(rows,key=lambda r:r['mz']),'atoms':graph['atoms'],'bonds':graph['bonds']}
