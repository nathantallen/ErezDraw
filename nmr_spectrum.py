"""Estimated first-order multiplets, with J in Hz and chemical shifts in ppm."""
import math

def estimate_couplings(mol,rows):
    for row in rows:
        row['couplings']=[]
        if not row.get('attachedAtoms'):continue
        atom=mol.GetAtomWithIdx(row['attachedAtoms'][0])
        # Exchangeable heteroatom protons are treated as uncoupled.
        if atom.GetSymbol()!='C':continue
        equivalent=set(row['attachedAtoms']);groups={}
        for neighbor in atom.GetNeighbors():
            if neighbor.GetIdx() in equivalent or neighbor.GetSymbol()!='C':continue
            n=neighbor.GetTotalNumHs()
            if not n:continue
            bond=mol.GetBondBetweenAtoms(atom.GetIdx(),neighbor.GetIdx())
            if bond.GetBondTypeAsDouble()!=1 and not bond.GetIsAromatic():continue
            j=8.0 if atom.GetIsAromatic() and neighbor.GetIsAromatic() else 7.0
            groups[j]=groups.get(j,0)+n
        row['couplings']=[{'j':j,'n':min(n,9)} for j,n in groups.items()]
    return rows

def multiplet_lines(row,mhz,nucleus='1H',coupled=True):
    if row['delta'] is None:return []
    if mhz<=0:raise ValueError('Frequency must be positive.')
    lines=[(row['delta'],float(row['count']))]
    if nucleus=='1H' and coupled:
        for coupling in row.get('couplings',[]):
            n=coupling['n'];j=coupling['j'];new=[]
            for delta,area in lines:
                for k in range(n+1):new.append((delta+(k-n/2)*j/mhz,area*math.comb(n,k)/2**n))
            lines=new
    return lines
