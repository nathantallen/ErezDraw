import unittest,copy
from rdkit import Chem
from structure_ops import from_smiles,properties,hydrogens,expand,contract,scope,interpreted,name_to_smiles

def drawing(smiles):return {'format':'chemsketch-classic','version':1,'name':'Test',**from_smiles(smiles),'annotations':[]}
class StructureCommands(unittest.TestCase):
 def test_weight_and_common_name(self):
  p=properties(drawing('CCO'));self.assertEqual(p['name'],'ethanol');self.assertEqual(p['formula'],'C2H6O');self.assertAlmostEqual(p['weight'],46.069,places=3)
 def test_hydrogens_roundtrip_preserves_heavy_atoms(self):
  d=drawing('CCO');h=hydrogens(d);self.assertEqual(len(h['atoms']),9);self.assertEqual(properties(h)['formula'],'C2H6O');self.assertEqual(hydrogens(h,remove=True),d)
 def test_single_molecule_scope(self):
  d=drawing('CCO');other=from_smiles('c1ccccc1');d['atoms']+=other['atoms'];d['bonds']+=other['bonds']
  with self.assertRaises(ValueError):properties(d)
  self.assertEqual(properties(d,[d['atoms'][0]['id']])['name'],'ethanol')
 def test_contract_expand_and_copy_identity(self):
  d=drawing('CCOC');ids=[a['id'] for a in d['atoms'][:2]];c=contract(d,ids,'Et');self.assertEqual(len(c['atoms']),3);self.assertEqual(properties(c)['formula'],properties(d)['formula']);e=expand(c);self.assertEqual(properties(e)['smiles'],properties(d)['smiles'])
  a=next(a for a in c['atoms'] if a.get('abbreviation'));old=a['id'];a['id']='copied';
  for b in c['bonds']:
   if b['a']==old:b['a']='copied'
   if b['b']==old:b['b']='copied'
  self.assertEqual(properties(expand(c))['smiles'],properties(d)['smiles'])
 def test_alias_expands_with_attachment(self):
  d=drawing('CO');d['atoms'][0]['label']='Ph';e=expand(d,[d['atoms'][0]['id']]);self.assertEqual(properties(e)['formula'],'C6H6O');self.assertEqual(len(e['atoms']),7)
 def test_contract_multiconnected_rejected(self):
  d=drawing('CCC')
  with self.assertRaises(ValueError):contract(d,[d['atoms'][1]['id']],'R')
 def test_invalid_valence_rejected(self):
  d=drawing('C');d['atoms'][0]['label']='unparsed'
  with self.assertRaises(ValueError):properties(d)
 def test_names(self):
  self.assertEqual(name_to_smiles('Ethanol'),'CCO')
  with self.assertRaises(ValueError):name_to_smiles('unlisted example')
 def test_metal_nmr_rejected(self):
  with self.assertRaises(ValueError):interpreted(drawing('[Y]'),organic=True)
if __name__=='__main__':unittest.main()

class LigandCommands(unittest.TestCase):
 def test_all_ligands_preserve_formula(self):
  from ligands import LIGANDS,ligand_template
  from chemistry import chemical_graph,molecule
  from rdkit.Chem.rdMolDescriptors import CalcMolFormula
  for _,name,smiles,_ in LIGANDS:
   with self.subTest(name=name):
    f=ligand_template(name);g,_=chemical_graph(f);mol,unknown=molecule(g['atoms'],g['bonds']);Chem.SanitizeMol(mol)
    self.assertFalse(unknown);self.assertEqual(CalcMolFormula(mol),CalcMolFormula(Chem.MolFromSmiles(smiles)))
 def test_analysis_multiple_molecules(self):
  from structure_ops import analysis
  d=drawing('CCO');f=from_smiles('O');d['atoms']+=f['atoms'];d['bonds']+=f['bonds'];a,p=analysis(d);self.assertEqual(a['Formula'],'C2H8O2');self.assertIn('cLogP (RDKit Crippen)',p);self.assertIn('Elemental composition',a)
 def test_isotope_chlorine(self):
  from structure_ops import analysis
  a,_=analysis(drawing('ClCl'));self.assertIn('100.00',a['Isotope envelope (mass Da : relative %)']);self.assertIn('Cl: 100.00%',a['Elemental composition'])

class PubChemCentroidIdentity(unittest.TestCase):
 def test_cp3y_ionic_query_has_no_centroids(self):
  import json
  from pathlib import Path
  from structure_ops import pubchem_query_structure
  d=json.loads((Path(__file__).parent/'examples/Cp3Y_centroid.chemjson').read_text())
  q=pubchem_query_structure(d);self.assertEqual(q['formula'],'C15H15Y');self.assertEqual(q['charge'],0)
  mol=Chem.MolFromSmiles(q['smiles']);self.assertEqual(mol.GetNumAtoms(),16);self.assertEqual(next(a for a in mol.GetAtoms() if a.GetSymbol()=='Y').GetFormalCharge(),3)
 def test_manual_metal_charge_preserved(self):
  import json
  from pathlib import Path
  from structure_ops import pubchem_query_structure
  d=json.loads((Path(__file__).parent/'examples/Cp3Y_centroid.chemjson').read_text());metal=next(a for a in d['atoms'] if a['label']=='Y');metal.update(charge=4,chargeMode='manual')
  self.assertEqual(pubchem_query_structure(d)['charge'],1)
 def test_pubchem_different_structure_is_not_accepted(self):
  import io,json
  from unittest.mock import patch
  from structure_ops import lookup_structure_name
  bad={'PropertyTable':{'Properties':[{'CID':123,'SMILES':'CO','IUPACName':'methanol','MolecularFormula':'CH4O','Charge':0}]}}
  with patch('urllib.request.urlopen',return_value=io.BytesIO(json.dumps(bad).encode())):
   with self.assertRaisesRegex(ValueError,'different ligand/charge'):lookup_structure_name(drawing('CCO'))

class RegressionCommands(unittest.TestCase):
 def test_add_hydrogens_rejects_contracted_label(self):
  # interpreted() expands contracted labels; the check previously inspected the expanded atoms and crashed.
  d=drawing('CCOC(C)(C)C');c=contract(d,[a['id'] for a in d['atoms'][3:]],'tBuX')
  for remove in (False,True):
   with self.assertRaisesRegex(ValueError,'Expand abbreviated'):hydrogens(c,remove=remove)
 def test_smiles_bond_types(self):
  with self.assertRaises(ValueError):from_smiles('C$C')
  bond=from_smiles('N->[Pt]')['bonds'][0];self.assertEqual((bond['order'],bond['style']),(1,'coord'))
  with self.assertRaises(ValueError):from_smiles('.')
 def test_pubchem_name_errors_are_user_errors(self):
  import io,urllib.error
  from unittest.mock import patch
  missing=urllib.error.HTTPError('u',404,'Not Found',{},io.BytesIO(b''))
  with patch('structure_ops.urllib.request.urlopen',side_effect=missing):
   with self.assertRaisesRegex(ValueError,'No PubChem'):name_to_smiles('unlisted example',online=True)
  with patch('structure_ops.urllib.request.urlopen',side_effect=urllib.error.URLError('offline')):
   with self.assertRaisesRegex(ValueError,'reach PubChem'):name_to_smiles('unlisted example',online=True)
 def test_expand_uses_document_bond_length(self):
  from structure_ops import expand
  d={'atoms':[{'id':'a1','x':100,'y':100,'label':'C','charge':0},{'id':'a2','x':119.2,'y':100,'label':'Et','charge':0}],'bonds':[{'id':'b1','a':'a1','b':'a2','order':1,'style':'normal'}],'annotations':[],'drawingSettings':{'bondLength':19.2}}
  out=expand(d);pos={a['id']:a for a in out['atoms']}
  new=[b for b in out['bonds'] if b['id']!='b1'][0];p,q=pos[new['a']],pos[new['b']]
  self.assertAlmostEqual(((p['x']-q['x'])**2+(p['y']-q['y'])**2)**.5,19.2,places=1)


class MetalHalideAnalysis(unittest.TestCase):
 def salt(self, halogen='I', style='coord', reverse=False):
  return {'atoms':[{'id':'sr','label':'Sr','x':0,'y':0,'charge':0},
                   {'id':'a','label':halogen,'x':40,'y':0,'charge':0},
                   {'id':'b','label':halogen,'x':-40,'y':0,'charge':0}],
          'bonds':[{'id':str(i),'a':'sr' if reverse else key,
                    'b':key if reverse else 'sr','order':1,'style':style}
                   for i,key in enumerate(('a','b'))], 'annotations':[]}
 def test_sri2_analysis_is_independent_of_bond_direction(self):
  from structure_ops import analysis
  for style in ('normal','coord'):
   for reverse in (False,True):
    with self.subTest(style=style,reverse=reverse):
     d=self.salt(style=style,reverse=reverse)
     data,_=analysis(d)
     self.assertEqual(data['Formula'],'I2Sr')
     self.assertEqual(data['Molecular weight (g/mol)'],'341.428')
     self.assertNotIn('H:',data['Elemental composition'])
     self.assertAlmostEqual(properties(d)['weight'],341.428,places=3)
     self.assertEqual(len(hydrogens(d)['atoms']),3)
 def test_other_metal_halides_do_not_gain_hydrogen(self):
  from structure_ops import analysis
  for halogen in ('F','Cl','Br','I'):
   with self.subTest(halogen=halogen):
    data,_=analysis(self.salt(halogen))
    self.assertNotIn('H',data['Formula'])
 def test_explicit_hydrogen_and_other_donors_are_preserved(self):
  from structure_ops import analysis
  d=self.salt();d['atoms'][1]['explicitHs']=1
  self.assertEqual(analysis(d)[0]['Formula'],'HI2Sr')
  for smiles,formula in [('CI','CH3I'),('I','HI'),('N->[Sr]<-N','H6N2Sr'),('O->[Sr]<-O','H4O2Sr')]:
   with self.subTest(smiles=smiles):
    self.assertEqual(analysis(drawing(smiles))[0]['Formula'],formula)
