"""Warning-only RDKit validation and coordinate-only cleanup; graph data stays intact."""
from __future__ import annotations
import copy
import math
from rdkit import Chem, rdBase
from rdkit.Chem import rdDepictor

# Labels that denote one chemically interpretable atom with explicit hydrogens.
ALIASES={'Me':('C',3),'CH3':('C',3),'CH2':('C',2),'CH':('C',1),'OH':('O',1),'NH2':('N',2),'NH':('N',1),'SH':('S',1)}
NONMETALS={1,2,5,6,7,8,9,10,14,15,16,17,18,32,33,34,35,36,51,52,53,54,85,86,117,118}
ELEMENTS={Chem.GetPeriodicTable().GetElementSymbol(n):n for n in range(1,119)}


def components(drawing):
    atoms={a['id']:a for a in drawing['atoms']}
    adjacency={key:set() for key in atoms}
    for b in drawing['bonds']:
        if b['a'] not in atoms or b['b'] not in atoms:
            raise ValueError('Bond references a missing atom.')
        adjacency[b['a']].add(b['b']);adjacency[b['b']].add(b['a'])
    unseen=set(atoms)
    output=[]
    for a in drawing['atoms']:
        if a['id'] not in unseen:continue
        ids={a['id']};pending=[a['id']];unseen.remove(a['id'])
        while pending:
            for neighbor in adjacency[pending.pop()]:
                if neighbor in unseen:unseen.remove(neighbor);ids.add(neighbor);pending.append(neighbor)
        output.append(([x for x in drawing['atoms'] if x['id'] in ids],[b for b in drawing['bonds'] if b['a'] in ids and b['b'] in ids]))
    return output


def is_metal(a):
    return a['label'] in ELEMENTS and ELEMENTS[a['label']] not in NONMETALS


def molecule(atoms,bonds):
    rw=Chem.RWMol();indices={};unknown=[]
    for a in atoms:
        label=a['label'];explicit=None
        if label in ALIASES:label,explicit=ALIASES[label]
        number=ELEMENTS.get(label,0)
        atom=Chem.Atom(number)
        if is_metal(a) or a.get('noImplicit'):atom.SetNoImplicit(True)
        if 'explicitHs' in a:atom.SetNumExplicitHs(a['explicitHs'])
        if number==0:
            unknown.append(a);atom.SetNoImplicit(True)
        if explicit is not None:atom.SetNumExplicitHs(explicit);atom.SetNoImplicit(True)
        atom.SetFormalCharge(a.get('charge',0))
        atom.SetNumRadicalElectrons(a.get('radical',0))
        indices[a['id']]=rw.AddAtom(atom)
    types={1:Chem.BondType.SINGLE,2:Chem.BondType.DOUBLE,3:Chem.BondType.TRIPLE,4:Chem.BondType.AROMATIC}
    for b in bonds:
        kind=Chem.BondType.DATIVE if b.get('style')=='coord' else types[b['order']]
        rw.AddBond(indices[b['a']],indices[b['b']],kind)
        if kind==Chem.BondType.AROMATIC:
            rw.GetAtomWithIdx(indices[b['a']]).SetIsAromatic(True)
            rw.GetAtomWithIdx(indices[b['b']]).SetIsAromatic(True)
    mol=rw.GetMol();mol.UpdatePropertyCache(strict=False)
    conformer=Chem.Conformer(len(atoms));conformer.Set3D(False)
    for i,a in enumerate(atoms):conformer.SetAtomPosition(i,(a['x']/40,-a['y']/40,0))
    mol.AddConformer(conformer)
    for b in bonds:
        # Wedge/hash directions are only meaningful on single bonds; RDKit's stereo
        # perception can hit internal precondition failures for wedged multiple bonds.
        if b.get('style') in ('wedge','hash','hollowWedge') and b['order']==1:
            mol.GetBondBetweenAtoms(indices[b['a']],indices[b['b']]).SetBondDir(Chem.BondDir.BEGINDASH if b['style']=='hash' else Chem.BondDir.BEGINWEDGE)
    try:Chem.AssignChiralTypesFromBondDirs(mol)
    except RuntimeError as e:raise ValueError('Wedge/hash stereo bonds could not be interpreted.') from e
    return mol,unknown


def chemical_graph(drawing):
    if any(a.get('abbreviation') for a in drawing['atoms']):
        from structure_ops import expand
        drawing=expand(drawing,[a['id'] for a in drawing['atoms'] if a.get('abbreviation')])
    virtual={a['id'] for a in drawing['atoms'] if a.get('nodeType')=='centroid'}
    return {**drawing,'atoms':[a for a in drawing['atoms'] if a['id'] not in virtual],
            'bonds':[b for b in drawing['bonds'] if b['a'] not in virtual and b['b'] not in virtual]},virtual


def validate(drawing):
    drawing,virtual=chemical_graph(drawing)
    issues=[];checked=0;partial=bool(virtual)
    def issue(severity,message,ids=()):issues.append({'severity':severity,'message':message,'atom_ids':list(ids)})
    if virtual:issue('info','Centroid attachment points are geometric objects, not atoms. Metal hapticity and multicenter bonding are not chemically validated.',virtual)
    with rdBase.BlockLogs():
        for atoms,bonds in components(drawing):
            metal=any(is_metal(a) for a in atoms) or any(b.get('style')=='coord' for b in bonds)
            if metal:
                partial=True
                issue('info','Metal/coordination component: standard organic valence validation skipped; this is not a validated structure.',[a['id'] for a in atoms if is_metal(a)])
                for a in atoms:
                    if a['label'] not in ELEMENTS and a['label'] not in ALIASES:
                        issue('warning',f"Label '{a['label']}' is not chemically interpreted.",[a['id']])
                continue
            try:
                mol,unknown=molecule(atoms,bonds)
                checked+=len(atoms)-len(unknown)
                for a in unknown:
                    partial=True;issue('warning',f"Label '{a['label']}' is a placeholder; its chemistry is not validated.",[a['id']])
                problems=Chem.DetectChemistryProblems(mol)
                for problem in problems:
                    inds=[problem.GetAtomIdx()] if hasattr(problem,'GetAtomIdx') else list(problem.GetAtomIndices()) if hasattr(problem,'GetAtomIndices') else []
                    issue('warning',problem.Message(),[atoms[i]['id'] for i in inds])
                if not problems:
                    flag=Chem.SanitizeMol(mol,catchErrors=True)
                    if flag!=Chem.SanitizeFlags.SANITIZE_NONE:issue('warning','Sanitization failed: '+str(flag),[a['id'] for a in atoms])
            except Exception as e:
                partial=True;issue('warning','Could not interpret component: '+str(e),[a['id'] for a in atoms])
    if not drawing['atoms']:
        return {'summary':'No atoms to validate.','issues':[],'checked_atoms':0,'complete':False}
    warnings=sum(i['severity']=='warning' for i in issues)
    summary=f'{warnings} chemistry warning(s); {checked} atom(s) checked.' if warnings else f'No problems detected in {checked} interpreted atom(s).'
    if partial:summary+=' Validation is partial; unparsed labels, centroid attachments or metal/coordination components remain unchecked.'
    return {'summary':summary,'issues':issues,'checked_atoms':checked,'complete':not partial}


def cleanup(drawing,bond_length=40,selected_ids=None,preserve_metals=True):
    if not 8<=bond_length<=200:raise ValueError('Bond length must be between 8 and 200.')
    result=copy.deepcopy(drawing);by_id={a['id']:a for a in result['atoms']}
    selection=set(selected_ids or []);notes=[];cleaned=0
    chemical,virtual=chemical_graph(drawing)
    protected_cp={id for ligand in drawing.get('ligands',[]) for id in ligand['atomIds']}
    for atoms,bonds in components(chemical):
        if any(a['id'] not in by_id for a in atoms):
            notes.append('Contracted fragment geometry preserved; expand its label before cleanup.');continue
        if any(a['id'] in protected_cp for a in atoms):
            notes.append('Cp ligand geometry preserved so its centroid attachment stays fixed.');continue
        # Process entire connected components touched by selection. Other molecules stay put.
        if selection and not any(a['id'] in selection for a in atoms):continue
        metal=any(is_metal(a) for a in atoms) or any(b.get('style')=='coord' for b in bonds)
        if preserve_metals and metal:
            notes.append('Metal/coordination component left unchanged to preserve its geometry.');continue
        if any(b.get('style') in ('wedge','hash','hollowWedge') for b in bonds):
            notes.append('Wedge/hashed component left unchanged because full stereo assignment is not implemented.');continue
        if any(a.get('z') for a in atoms):
            notes.append('Perspective component left unchanged; use Object > Flatten before cleanup.');continue
        if len(atoms)<2:continue
        try:
            with rdBase.BlockLogs():
                mol,unknown=molecule(atoms,bonds)
                flag=Chem.SanitizeMol(mol,catchErrors=True)
                if flag!=Chem.SanitizeFlags.SANITIZE_NONE:
                    notes.append('Component with invalid chemistry left unchanged.');continue
                rdDepictor.Compute2DCoords(mol,canonOrient=True,bondLength=bond_length,forceRDKit=True,useRingTemplates=True)
            conformer=mol.GetConformer()
            positions=[conformer.GetAtomPosition(i) for i in range(len(atoms))]
            old_x=sum(a['x'] for a in atoms)/len(atoms);old_y=sum(a['y'] for a in atoms)/len(atoms)
            new_x=sum(p.x for p in positions)/len(atoms);new_y=sum(p.y for p in positions)/len(atoms)
            for a,p in zip(atoms,positions):
                x=old_x+p.x-new_x;y=old_y-p.y+new_y
                if not math.isfinite(x) or not math.isfinite(y):raise ValueError('Invalid layout coordinates.')
                by_id[a['id']]['x']=x;by_id[a['id']]['y']=y
            cleaned+=1
            if unknown:notes.append('Uninterpreted labels retained as layout placeholders; abbreviations were not expanded.')
            if metal:notes.append('Metal geometry rearranged as a 2D drawing, not a chemically validated coordination geometry.')
        except Exception as e:notes.append('Component left unchanged: '+str(e))
    return {'drawing':result,'cleaned_components':cleaned,'notes':list(dict.fromkeys(notes))}
