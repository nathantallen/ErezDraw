"""Structure commands. Chemical calculations never include geometric centroid nodes."""
import copy, math, uuid, json, urllib.error, urllib.request, urllib.parse
from functools import lru_cache
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors, rdDepictor
from chemistry import molecule, chemical_graph, components, is_metal, ELEMENTS

ABBREVIATIONS={'Me':'C','Et':'CC','Pr':'CCC','iPr':'C(C)C','Bu':'CCCC','tBu':'C(C)(C)C','Ph':'c1ccccc1','Bn':'Cc1ccccc1','OMe':'OC','OEt':'OCC','Ac':'C(=O)C','OAc':'OC(=O)C','NMe2':'N(C)C','SiMe3':'[Si](C)(C)C','TMS':'[Si](C)(C)C','COOH':'C(=O)O','CO2H':'C(=O)O'}
COMMON={'methane':'C','ethane':'CC','propane':'CCC','butane':'CCCC','pentane':'CCCCC','hexane':'CCCCCC','heptane':'CCCCCCC','octane':'CCCCCCCC','benzene':'c1ccccc1','toluene':'Cc1ccccc1','ethylbenzene':'CCc1ccccc1','cyclopentane':'C1CCCC1','cyclohexane':'C1CCCCC1','methanol':'CO','ethanol':'CCO','acetone':'CC(=O)C','acetic acid':'CC(=O)O','tetrahydrofuran':'C1CCOC1','diethyl ether':'CCOCC','water':'O','ammonia':'N','pyridine':'c1ccncc1','phenol':'Oc1ccccc1','aniline':'Nc1ccccc1','acetonitrile':'CC#N','dimethyl sulfoxide':'CS(C)=O','chloroform':'ClC(Cl)Cl','dichloromethane':'ClCCl'}

def uid(prefix):return prefix+uuid.uuid4().hex[:14]

def scope(drawing,selected=()):
    ids=set(selected);adj={a['id']:set() for a in drawing['atoms']}
    for b in drawing['bonds']:adj[b['a']].add(b['b']);adj[b['b']].add(b['a'])
    for a in drawing['atoms']:
        if a.get('nodeType')=='centroid':
            for member in a['members']:adj[a['id']].add(member);adj[member].add(a['id'])
    if not ids:
        if not adj:raise ValueError('Draw or select a molecule first.')
        ids={next(iter(adj))}
        all_required=True
    else:all_required=False
    todo=list(ids)
    while todo:
        for n in adj[todo.pop()]:
            if n not in ids:ids.add(n);todo.append(n)
    if all_required and ids!=set(adj):raise ValueError('Select the molecule to use; the drawing contains multiple molecules.')
    # Multiple separately selected molecules are ambiguous for names / spectra.
    reachable=set();todo=[next(iter(ids))]
    while todo:
        x=todo.pop()
        if x in reachable:continue
        reachable.add(x);todo.extend(adj[x]-reachable)
    if reachable!=ids:raise ValueError('Select one connected molecule.')
    return {**copy.deepcopy(drawing),'atoms':[copy.deepcopy(a) for a in drawing['atoms'] if a['id'] in ids],'bonds':[copy.deepcopy(b) for b in drawing['bonds'] if b['a'] in ids and b['b'] in ids],'ligands':[copy.deepcopy(l) for l in drawing.get('ligands',[]) if l['centroidId'] in ids],'groups':[],'annotations':[]}

def from_smiles(smiles,center=(500,350),length=40):
    mol=Chem.MolFromSmiles(smiles)
    if mol is None or not mol.GetNumAtoms():raise ValueError('The structure could not be interpreted.')
    rdDepictor.Compute2DCoords(mol,bondLength=length);Chem.WedgeMolBonds(mol,mol.GetConformer())
    pts=[mol.GetConformer().GetAtomPosition(i) for i in range(mol.GetNumAtoms())]
    cx=sum(p.x for p in pts)/len(pts);cy=sum(p.y for p in pts)/len(pts);atoms=[]
    for i,a in enumerate(mol.GetAtoms()):
        if a.GetIsotope():raise ValueError('Isotopic structures are not supported by this document format.')
        atoms.append({'id':uid('a'),'x':center[0]+pts[i].x-cx,'y':center[1]-pts[i].y+cy,'label':a.GetSymbol(),'charge':a.GetFormalCharge(),'radical':a.GetNumRadicalElectrons(),**({'noImplicit':True,'explicitHs':a.GetNumExplicitHs()} if a.GetNoImplicit() else {})})
    bonds=[]
    for b in mol.GetBonds():
        kind=b.GetBondType()
        if not b.GetIsAromatic() and kind not in (Chem.BondType.SINGLE,Chem.BondType.DOUBLE,Chem.BondType.TRIPLE,Chem.BondType.DATIVE):raise ValueError('Only single, double, triple, aromatic and dative bonds are supported.')
        style='coord' if kind==Chem.BondType.DATIVE else 'wedge' if b.GetBondDir()==Chem.BondDir.BEGINWEDGE else 'hash' if b.GetBondDir()==Chem.BondDir.BEGINDASH else 'normal'
        bonds.append({'id':uid('b'),'a':atoms[b.GetBeginAtomIdx()]['id'],'b':atoms[b.GetEndAtomIdx()]['id'],'order':4 if b.GetIsAromatic() else 1 if kind==Chem.BondType.DATIVE else int(b.GetBondTypeAsDouble()),'style':style})
    return {'atoms':atoms,'bonds':bonds}

def _document_bond_length(drawing,default=40):
    try:value=float((drawing.get('drawingSettings') or {}).get('bondLength',default))
    except (TypeError,ValueError):return default
    return value if math.isfinite(value) and 0<value<=1000 else default

def expand(drawing,selected=()):
    out=copy.deepcopy(drawing);ids=set(selected);changed=0;length=_document_bond_length(drawing)
    for a in list(out['atoms']):
        if ids and a['id'] not in ids:continue
        if a.get('abbreviation'):
            frag=copy.deepcopy(a['abbreviation']);anchor=next(x for x in frag['atoms'] if x['id']==frag.get('anchorId',a['id']));dx=a['x']-anchor['x'];dy=a['y']-anchor['y'];mapping={x['id']:(a['id'] if x['id']==anchor['id'] else uid('a')) for x in frag['atoms']}
            for x in frag['atoms']:x['id']=mapping[x['id']]
            for b in frag['bonds']:b['id']=uid('b');b['a']=mapping[b['a']];b['b']=mapping[b['b']]
            for x in frag['atoms']:x['x']+=dx;x['y']+=dy
        elif a['label'] in ABBREVIATIONS:
            frag=from_smiles(ABBREVIATIONS[a['label']],(a['x'],a['y']),length);old=frag['atoms'][0]['id'];dx=a['x']-frag['atoms'][0]['x'];dy=a['y']-frag['atoms'][0]['y']
            for x in frag['atoms']:
                x['x']+=dx;x['y']+=dy
                if x['id']==old:x['id']=a['id'];x['charge']=a.get('charge',0)
            for b in frag['bonds']:
                if b['a']==old:b['a']=a['id']
                if b['b']==old:b['b']=a['id']
        else:continue
        out['atoms']=[x for x in out['atoms'] if x['id']!=a['id']]+frag['atoms'];out['bonds']+=frag['bonds'];changed+=1
    if not changed:raise ValueError('Select an abbreviated label, such as Me, Et, Ph, OMe, NMe2 or SiMe3.')
    return out

def interpreted(drawing,selected=(),organic=False):
    fragment=scope(drawing,selected)
    if any(a.get('abbreviation') or a['label'] in ABBREVIATIONS for a in fragment['atoms']):fragment=expand(fragment)
    graph,virtual=chemical_graph(fragment)
    if organic and (virtual or any(is_metal(a) for a in graph['atoms']) or any(b.get('style')=='coord' for b in graph['bonds'])):raise ValueError('NMR prediction supports organic molecules. Metal complexes and centroid bonding are outside the predictor’s model.')
    mol,unknown=molecule(graph['atoms'],graph['bonds'])
    if unknown:raise ValueError('Expand or correct these uninterpreted labels: '+', '.join(sorted({a['label'] for a in unknown})))
    Chem.SanitizeMol(mol)
    return fragment,graph,mol

@lru_cache(maxsize=1)
def _common_names():
    # First dictionary entry wins for duplicate canonical SMILES, as before.
    names={}
    for name,smiles in COMMON.items():names.setdefault(Chem.MolToSmiles(Chem.MolFromSmiles(smiles)),name)
    return names

def properties(drawing,selected=()):
    fragment=scope(drawing,selected)
    if any(a.get('nodeType')=='centroid' for a in fragment['atoms']) and any(is_metal(a) for a in fragment['atoms']):
        query=pubchem_query_structure(fragment);mol=Chem.MolFromSmiles(query['smiles'])
    else:fragment,graph,mol=interpreted(drawing,selected)
    smiles=Chem.MolToSmiles(mol)
    name=_common_names().get(smiles,'')
    return {'name':name,'smiles':smiles,'formula':rdMolDescriptors.CalcMolFormula(mol),'weight':Descriptors.MolWt(mol),'ids':[a['id'] for a in fragment['atoms']],'bounds':{'x':min(a['x'] for a in fragment['atoms']),'y':max(a['y'] for a in fragment['atoms'])}}

def hydrogens(drawing,selected=(),remove=False):
    frag,graph,mol=interpreted(drawing,selected);out=copy.deepcopy(drawing)
    # interpreted() returns the expanded fragment, so check the drawing's own atoms.
    if any(a.get('abbreviation') or a['label'] in ABBREVIATIONS for a in scope(drawing,selected)['atoms']):raise ValueError('Expand abbreviated labels first.')
    if remove:
        removable=set()
        for a in graph['atoms']:
            if a['label']!='H' or a['charge'] or a.get('radical'):continue
            linked=[b for b in graph['bonds'] if a['id'] in (b['a'],b['b'])]
            if len(linked)==1 and linked[0]['order']==1 and linked[0].get('style','normal')=='normal':
                other=linked[0]['b'] if linked[0]['a']==a['id'] else linked[0]['a']
                if next(x for x in graph['atoms'] if x['id']==other)['label']!='H':removable.add(a['id'])
        out['atoms']=[a for a in out['atoms'] if a['id'] not in removable];out['bonds']=[b for b in out['bonds'] if not {b['a'],b['b']}&removable]
        for index,atom in enumerate(mol.GetAtoms()):atom.SetAtomMapNum(index+1)
        reduced=Chem.RemoveHs(mol)
        for atom in reduced.GetAtoms():
            original=graph['atoms'][atom.GetAtomMapNum()-1];target=next((x for x in out['atoms'] if x['id']==original['id']),None)
            if target is not None and any(b['a']==target['id'] and b['b'] in removable or b['b']==target['id'] and b['a'] in removable for b in graph['bonds']):
                target.pop('explicitHs',None);target.pop('noImplicit',None)
                if atom.GetNoImplicit() or atom.GetNumExplicitHs():target.update(noImplicit=atom.GetNoImplicit(),explicitHs=atom.GetNumExplicitHs())
    else:
        for i,a in enumerate(graph['atoms']):
            atom=mol.GetAtomWithIdx(i);count=atom.GetNumImplicitHs()+atom.GetNumExplicitHs()
            if not count:continue
            target=next(x for x in out['atoms'] if x['id']==a['id']);target.pop('explicitHs',None);target.pop('noImplicit',None)
            if a['label'] not in ELEMENTS:raise ValueError('Expand atom hydrogen labels before adding explicit hydrogens.')
            neighbors=[next(x for x in graph['atoms'] if x['id']==(b['b'] if b['a']==a['id'] else b['a'])) for b in graph['bonds'] if a['id'] in (b['a'],b['b'])]
            used=[math.atan2(n['y']-a['y'],n['x']-a['x']) for n in neighbors]
            for _ in range(count):
                theta=max((j*math.pi/6 for j in range(12)),key=lambda t:min((abs(math.atan2(math.sin(t-u),math.cos(t-u))) for u in used),default=math.pi));used.append(theta)
                h={'id':uid('h'),'x':a['x']+28*math.cos(theta),'y':a['y']+28*math.sin(theta),'label':'H','charge':0};out['atoms'].append(h);out['bonds'].append({'id':uid('b'),'a':a['id'],'b':h['id'],'order':1,'style':'normal'})
    return out

def contract(drawing,selected,label):
    ids=set(selected)
    if not ids:raise ValueError('Select the atoms to contract first.')
    atoms=[a for a in drawing['atoms'] if a['id'] in ids]
    if any(a.get('nodeType') or a.get('abbreviation') for a in atoms) or any(ids&set(l['atomIds']) for l in drawing.get('ligands',[])):raise ValueError('Cp ligands, centroids and already contracted labels cannot be contracted.')
    internal=[b for b in drawing['bonds'] if b['a'] in ids and b['b'] in ids];boundary=[b for b in drawing['bonds'] if (b['a'] in ids)!=(b['b'] in ids)]
    if len(boundary)>1:raise ValueError('A contracted label must have at most one external bond.')
    if len(components({'atoms':atoms,'bonds':internal}))!=1:raise ValueError('Select one connected fragment.')
    anchor=(boundary[0]['a'] if boundary[0]['a'] in ids else boundary[0]['b']) if boundary else atoms[0]['id']
    a=copy.deepcopy(next(x for x in atoms if x['id']==anchor));a['label']=label;a.pop('textRuns',None);a['abbreviation']={'anchorId':anchor,'atoms':copy.deepcopy(atoms),'bonds':copy.deepcopy(internal)}
    out=copy.deepcopy(drawing);out['atoms']=[x for x in out['atoms'] if x['id'] not in ids]+[a];out['bonds']=[b for b in out['bonds'] if b not in internal];return out

def pubchem(value,namespace,prop):
    url='https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/'+namespace+'/'+urllib.parse.quote(value,safe='')+'/property/'+prop+'/JSON'
    request=urllib.request.Request(url,headers={'User-Agent':'ErezDraw/0.9'})
    with urllib.request.urlopen(request,timeout=15) as response:data=json.load(response)
    return data['PropertyTable']['Properties'][0][prop]

def name_to_smiles(name,online=False):
    found=COMMON.get(name.strip().lower())
    if found:return found
    if online:
        try:return pubchem(name,'name','SMILES')
        except urllib.error.HTTPError as e:
            if e.code==404:raise ValueError('No PubChem compound matches this name.') from e
            raise ValueError('PubChem is temporarily unavailable. Please try again later.') from e
        except (urllib.error.URLError,TimeoutError) as e:raise ValueError('Could not reach PubChem. Check the server internet connection and try again.') from e
    raise ValueError('Name is not in the local dictionary. Enable PubChem lookup, or enter SMILES in the import field.')

def analysis(drawing,selected=()):
    frag=scope(drawing,selected) if selected else copy.deepcopy(drawing)
    if not frag['atoms']:raise ValueError('No chemical atoms in the drawing.')
    if any(a.get('abbreviation') or a['label'] in ABBREVIATIONS for a in frag['atoms']):frag=expand(frag)
    graph,virtual=chemical_graph(frag);mol,unknown=molecule(graph['atoms'],graph['bonds'])
    if unknown:raise ValueError('Uninterpreted labels: '+', '.join(a['label'] for a in unknown))
    Chem.SanitizeMol(mol);table=Chem.GetPeriodicTable();counts={}
    for a in Chem.AddHs(mol).GetAtoms():counts[a.GetSymbol()]=counts.get(a.GetSymbol(),0)+1
    weight=Descriptors.MolWt(mol)
    data={'Formula':rdMolDescriptors.CalcMolFormula(mol),'Molecular weight (g/mol)':f'{weight:.3f}','Exact mass (Da)':f'{rdMolDescriptors.CalcExactMolWt(mol):.5f}','Formal charge':str(Chem.GetFormalCharge(mol))}
    data['Elemental composition']='; '.join(f'{symbol}: {100*count*table.GetAtomicWeight(symbol)/weight:.2f}%' for symbol,count in sorted(counts.items()))
    # Natural-abundance isotope envelope; retain the 256 most probable mass bins.
    distribution={0.0:1.0}
    for symbol,count in counts.items():
        z=table.GetAtomicNumber(symbol);isotopes=[(table.GetMassForIsotope(z,n),table.GetAbundanceForIsotope(z,n)/100) for n in range(1,301) if table.GetAbundanceForIsotope(z,n)>0]
        if not isotopes:isotopes=[(table.GetMostCommonIsotopeMass(z),1)]
        for _ in range(count):
            result={}
            for mass,p in distribution.items():
                for isotope,q in isotopes:
                    if p*q<1e-10:continue
                    key=round(mass+isotope,4);result[key]=result.get(key,0)+p*q
            distribution=dict(sorted(result.items(),key=lambda item:item[1],reverse=True)[:256])
    maximum=max(distribution.values(),default=1)
    data['Isotope envelope (mass Da : relative %)']='\n'.join(f'{mass:.4f} : {100*p/maximum:.2f}' for mass,p in sorted(distribution.items(),key=lambda item:item[1],reverse=True)[:10])
    data['Isotope method']='Natural abundance; top 256 mass bins retained; neutral atomic masses.'
    if virtual:data['Coordination note']='Centroid excluded from mass; ligand formal charges retained. Metal oxidation states must be entered explicitly.'
    chemical={}
    if virtual or any(is_metal(a) for a in graph['atoms']):chemical['Model scope']='Organic property models are unavailable for this metal/centroid structure.'
    else:
        chemical={'cLogP (RDKit Crippen)':f'{Descriptors.MolLogP(mol):.3f}','Molar refractivity (RDKit Crippen)':f'{Descriptors.MolMR(mol):.3f}','Polar surface area (Å²)':f'{Descriptors.TPSA(mol):.2f}','H-bond donors':str(Descriptors.NumHDonors(mol)),'H-bond acceptors':str(Descriptors.NumHAcceptors(mol)),'Rotatable bonds':str(Descriptors.NumRotatableBonds(mol)),'Rings':str(Descriptors.RingCount(mol)),'Fraction sp³ carbon':f'{Descriptors.FractionCSP3(mol):.3f}'}
        chemical['Model']='RDKit estimates; not ChemDraw ChemProp/CLogP. Boiling/melting points and thermodynamic estimates are not supplied.'
    return data,chemical


def pubchem_query_structure(drawing,selected=()):
    """Centroid-aware ionic structure identity, without fake centroid atoms/bonds."""
    fragment=scope(drawing,selected)
    if any(a.get('abbreviation') or a['label'] in ABBREVIATIONS for a in fragment['atoms']):fragment=expand(fragment)
    graph,virtual=chemical_graph(fragment);graph=copy.deepcopy(graph)
    metals=[a for a in graph['atoms'] if is_metal(a)]
    if virtual and len(metals)!=1:raise ValueError('Centroid complexes require one metal for an unambiguous PubChem query. Assign a supported explicit structure for a multimetal complex.')
    if metals and virtual:
        metal=metals[0];metal_id=metal['id']
        attached={b['b'] if b['a']==metal_id else b['a'] for b in graph['bonds'] if metal_id in (b['a'],b['b'])}
        graph['bonds']=[b for b in graph['bonds'] if b['a']!=metal_id and b['b']!=metal_id]
        for a in graph['atoms']:
            if a['id'] in attached and a['label'] in ('F','Cl','Br','I','H') and not any(a['id'] in (b['a'],b['b']) for b in graph['bonds']) and a.get('chargeMode')!='manual' and a['charge']==0:
                a['charge']=-1;a['noImplicit']=True
        ligand_charge=sum(a['charge'] for a in graph['atoms'] if a['id']!=metal_id)
        if metal.get('chargeMode')!='manual' and (metal['charge']==0 or metal.get('chargeMode')=='auto'):
            metal['charge']=metal.get('complexCharge',0)-ligand_charge
    mol,unknown=molecule(graph['atoms'],graph['bonds'])
    if unknown:raise ValueError('Expand unsupported ligand labels before PubChem lookup.')
    Chem.SanitizeMol(mol)
    return {'smiles':Chem.MolToSmiles(mol),'formula':rdMolDescriptors.CalcMolFormula(mol),'charge':Chem.GetFormalCharge(mol),'centroid':bool(virtual)}


def lookup_structure_name(drawing,selected=(),property_tags="IUPACName,Title,SMILES,MolecularFormula,Charge"):
    query=pubchem_query_structure(drawing,selected)
    body=urllib.parse.urlencode({'smiles':query['smiles']}).encode('utf-8')
    url='https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/property/'+property_tags+'/JSON'
    request=urllib.request.Request(url,data=body,headers={'User-Agent':'ErezDraw/0.9','Content-Type':'application/x-www-form-urlencoded'})
    try:
        with urllib.request.urlopen(request,timeout=20) as response:data=json.load(response)
    except urllib.error.HTTPError as e:
        if e.code==404:raise ValueError('No exact PubChem structure match. The centroid-aware ionic query was not replaced by a formula or name search.') from e
        raise
    expected=Chem.MolToSmiles(Chem.MolFromSmiles(query['smiles']))
    for hit in data.get('PropertyTable',{}).get('Properties',[]):
        returned=hit.get('SMILES') or hit.get('ConnectivitySMILES') or hit.get('CanonicalSMILES')
        mol=Chem.MolFromSmiles(returned or '')
        if mol is None:continue
        if Chem.MolToSmiles(mol)!=expected or rdMolDescriptors.CalcMolFormula(mol)!=query['formula'] or Chem.GetFormalCharge(mol)!=query['charge']:continue
        return {'name':hit.get('IUPACName') or hit.get('Title') or '','cid':hit['CID'],'query':query,'properties':hit}
    raise ValueError('PubChem returned a different ligand/charge representation. No name was substituted. Check formal charges or enter a verified compound name manually.')


def lookup_structure_properties(drawing,selected=()):
    tags='IUPACName,Title,SMILES,MolecularFormula,Charge,MolecularWeight,ExactMass,MonoisotopicMass,XLogP,TPSA,HBondDonorCount,HBondAcceptorCount,RotatableBondCount,HeavyAtomCount,Complexity,InChIKey'
    try:
        result=lookup_structure_name(drawing,selected,tags)
    except urllib.error.HTTPError as error:
        raise ValueError('PubChem is temporarily unavailable. Please try again later.') from error
    except (urllib.error.URLError,TimeoutError) as error:
        raise ValueError('Could not reach PubChem. Check the server internet connection and try again.') from error
    result['experimental']=[]
    try:
        view_url='https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/'+str(result['cid'])+'/JSON?heading=Experimental+Properties'
        with urllib.request.urlopen(view_url,timeout=20) as response:view=json.load(response)
        references={r['ReferenceNumber']:r.get('SourceName','') for r in view.get('Record',{}).get('Reference',[])}
        wanted={'Melting Point','Boiling Point','Density','Solubility','Vapor Pressure','Flash Point','Refractive Index'}
        def visit(section):
            heading=section.get('TOCHeading','')
            if heading in wanted:
                for info in section.get('Information',[])[:3]:
                    value='; '.join(part.get('String','') for part in info.get('Value',{}).get('StringWithMarkup',[]))
                    if value:result['experimental'].append({'name':heading,'value':value,'source':references.get(info.get('ReferenceNumber'),'')})
            for child in section.get('Section',[]):visit(child)
        visit(view.get('Record',{}))
        if not result['experimental']:result['experimentalNote']='PubChem has no reported physical properties for this matched record.'
    except (urllib.error.URLError,TimeoutError,ValueError):
        result['experimentalNote']='Reported physical properties could not be retrieved; the PubChem compound link contains the full record.'
    result['url']='https://pubchem.ncbi.nlm.nih.gov/compound/'+str(result['cid'])
    return result
