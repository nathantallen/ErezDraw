"""Confidence-filtered proton environments and small-system spin simulation.
All rule shifts and J constants are estimates; no exact solvent model is implied.
"""
import numpy as np
from rdkit import Chem


def environment_shift(atom):
    neighbors=list(atom.GetNeighbors());h=atom.GetTotalNumHs()
    if atom.GetSymbol()!='C':return None
    if atom.GetIsAromatic():return 7.2
    if h==4 and not neighbors:return .23
    if atom.GetHybridization()==Chem.HybridizationType.SP:
        return 2.5
    carbonyl=any(n.GetSymbol()=='O' and atom.GetOwningMol().GetBondBetweenAtoms(atom.GetIdx(),n.GetIdx()).GetBondTypeAsDouble()==2 for n in neighbors)
    if carbonyl:return 9.7 if h else None
    if atom.GetHybridization()==Chem.HybridizationType.SP2:return 5.4
    if any(n.GetSymbol()=='O' for n in neighbors):return 3.35 if h==3 else 3.6
    if any(n.GetSymbol()=='N' for n in neighbors):return 2.3 if h==3 else 2.7
    if any(n.GetSymbol() in ('F','Cl','Br','I') for n in neighbors):return 3.1 if h==3 else 3.4
    if any(n.GetSymbol()=='S' for n in neighbors):return 2.2
    if any(n.GetIsAromatic() for n in neighbors):return 2.34 if h==3 else 2.65
    if any(any(nn.GetSymbol()=='O' and n.GetOwningMol().GetBondBetweenAtoms(n.GetIdx(),nn.GetIdx()).GetBondTypeAsDouble()==2 for nn in n.GetNeighbors()) for n in neighbors):return 2.1 if h==3 else 2.4
    return .9 if h==3 else 1.35 if h==2 else 1.7


def refine_proton_shifts(mol,rows):
    distances=Chem.GetDistanceMatrix(mol);monoalkyl=[]
    for ring_ids in mol.GetRingInfo().AtomRings():
        ring=set(ring_ids)
        if len(ring)!=6 or not all(mol.GetAtomWithIdx(i).GetIsAromatic() and mol.GetAtomWithIdx(i).GetSymbol()=='C' for i in ring):continue
        external=[(i,n) for i in ring for n in mol.GetAtomWithIdx(i).GetNeighbors() if n.GetIdx() not in ring and n.GetSymbol()!='H']
        if len(external)==1 and external[0][1].GetSymbol()=='C' and external[0][1].GetHybridization()==Chem.HybridizationType.SP3:monoalkyl.append((ring,external[0][0]))
    for row in rows:
        row['rawDelta']=row['delta'];row['source']='HOSE database';row['confidence']='database estimate'
        parents=row.get('attachedAtoms') or []
        if not parents:continue
        atom=mol.GetAtomWithIdx(parents[0]);special=None
        for ring,ipso in monoalkyl:
            if atom.GetIdx() in ring:special={1:7.16,2:7.24,3:7.16}.get(int(distances[atom.GetIdx(),ipso]))
        broad=row['delta'] is None or (row.get('level') or 0)<=2 or (row.get('std') or 0)>.5
        impossible=atom.GetIsAromatic() and atom.GetSymbol()=='C' and row['delta'] is not None and not 5.5<row['delta']<10
        if special is not None or broad or impossible:
            estimate=special if special is not None else environment_shift(atom)
            row['delta']=estimate;row['source']='Monoalkylbenzene environment estimate' if special is not None else 'Environment estimate' if estimate is not None else 'Unavailable: broad/missing database match';row['confidence']='approximate environment model' if estimate is not None else 'unavailable'
    return rows


def coupling(mol,a,b):
    if a==b:return 0.0
    aa,bb=mol.GetAtomWithIdx(a),mol.GetAtomWithIdx(b)
    if aa.GetSymbol()!='C' or bb.GetSymbol()!='C':return 0.0
    path=Chem.GetShortestPath(mol,a,b);distance=len(path)-1
    if aa.GetIsAromatic() and bb.GetIsAromatic() and all(mol.GetAtomWithIdx(i).GetIsAromatic() for i in path):return {1:7.8,2:1.5,3:.4}.get(distance,0)
    return 7.0 if distance==1 and not aa.GetIsAromatic() and not bb.GetIsAromatic() else 0.0


def quantum_lines(mol,rows,mhz,max_component=8):
    if mhz<=0:raise ValueError('Frequency must be positive.')
    spins=[];remaining={a.GetIdx():a.GetTotalNumHs() for a in mol.GetAtoms()}
    for group,row in enumerate(rows):
        if row['delta'] is None:continue
        left=int(row['count'])
        for parent in row.get('attachedAtoms',[]):
            count=min(left,remaining.get(parent,0));spins.extend((group,parent,row['delta']) for _ in range(count));remaining[parent]-=count;left-=count
        if left:return None
    adjacency={i:set() for i in range(len(spins))};jvalues={}
    # Couplings depend only on the parent carbons and vanish beyond three bonds;
    # cache per atom pair instead of re-running a shortest-path search per spin pair.
    distances=Chem.GetDistanceMatrix(mol);pair_couplings={}
    def pair_coupling(a,b):
        key=(a,b) if a<b else (b,a)
        if key not in pair_couplings:pair_couplings[key]=0.0 if distances[a,b]>3 else coupling(mol,a,b)
        return pair_couplings[key]
    for i in range(len(spins)):
        for j in range(i):
            value=pair_coupling(spins[i][1],spins[j][1])
            if value:jvalues[i,j]=value;adjacency[i].add(j);adjacency[j].add(i)
    components=[];unseen=set(adjacency)
    while unseen:
        start=unseen.pop();component={start};todo=[start]
        while todo:
            for j in adjacency[todo.pop()]&unseen:unseen.remove(j);component.add(j);todo.append(j)
        if len(component)>max_component:return None
        components.append(sorted(component))
    output=[{} for _ in rows]
    for component in components:
        n=len(component);size=1<<n;states=np.arange(size,dtype=np.int64);mag=np.stack([.5-((states>>i)&1) for i in range(n)])
        h=np.diag(sum(spins[spin][2]*mhz*mag[i] for i,spin in enumerate(component)))
        for i,spin in enumerate(component):
            for j in range(i):
                other=component[j];value=jvalues.get((max(spin,other),min(spin,other)),0)
                if not value:continue
                h[np.diag_indices(size)]+=value*mag[i]*mag[j]
                opposite=states[((states>>i)&1)!=((states>>j)&1)];h[opposite^(1<<i)^(1<<j),opposite]+=value*.5
        energy,vectors=np.linalg.eigh(h);operators={}
        for i,spin in enumerate(component):
            group=spins[spin][0]
            if group not in operators:operators[group]=np.zeros((size,size))
            lower=states[((states>>i)&1)==1];operators[group][lower^(1<<i),lower]+=1
        # numpy 2.x matmul leaks BLAS floating-point flags even for finite operands,
        # so ignore them here rather than print spurious warnings on every simulation.
        with np.errstate(all='ignore'):transformed={g:vectors.T@op@vectors for g,op in operators.items()}
        total=sum(transformed.values());strength=total*total;weight=sum(x*x for x in transformed.values());valid=(strength>1e-8)&(weight>1e-10)
        for dest,source in zip(*np.where(valid)):
            delta=round(float((energy[dest]-energy[source])/mhz),8)
            for group,amplitude in transformed.items():
                area=float(strength[dest,source]*amplitude[dest,source]**2/weight[dest,source]);output[group][delta]=output[group].get(delta,0)+area
    result=[]
    for row,lines in zip(rows,output):
        total=sum(lines.values());result.append([(delta,value*row['count']/total) for delta,value in sorted(lines.items()) if value>1e-7] if total else [])
    return result
