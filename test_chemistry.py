import copy
import math
import unittest
from chemistry import validate,cleanup

def drawing(labels,bonds):
 return {'format':'chemsketch-classic','version':1,'name':'test','atoms':[{'id':str(i),'label':s,'charge':0,'x':i*13,'y':(i%2)*7} for i,s in enumerate(labels)],'bonds':[{'id':'b'+str(i),'a':str(a),'b':str(b),'order':order,'style':style} for i,(a,b,order,style) in enumerate(bonds)],'annotations':[{'id':'t','type':'text','x':3,'y':4,'text':'untouched'}]}

class ChemistryTests(unittest.TestCase):
 def test_valid_organic(self):
  d=drawing(['C','C','O'],[(0,1,1,'normal'),(1,2,1,'normal')]);r=validate(d)
  self.assertTrue(r['complete']);self.assertFalse([i for i in r['issues'] if i['severity']=='warning'])
 def test_bad_valence_highlight(self):
  d=drawing(['C']+['F']*5,[(0,i,1,'normal') for i in range(1,6)]);r=validate(d)
  self.assertTrue(any('0' in i['atom_ids'] for i in r['issues'] if i['severity']=='warning'))
 def test_unknown_and_metal_are_unchecked(self):
  d=drawing(['Y','HMDS'],[(0,1,1,'coord')]);r=validate(d)
  self.assertFalse(r['complete']);self.assertEqual(r['checked_atoms'],0)
  self.assertTrue(any('HMDS' in i['message'] for i in r['issues']))
 def test_alias(self):
  d=drawing(['Me','O','Me'],[(0,1,1,'normal'),(1,2,1,'normal')]);self.assertFalse(validate(d)['issues'])
 def test_cleanup_preserves_data_and_length(self):
  d=drawing(['C']*6,[(i,(i+1)%6,2 if i%2==0 else 1,'normal') for i in range(6)]);old=copy.deepcopy(d);r=cleanup(d,40)
  self.assertEqual(d,old);self.assertEqual(r['cleaned_components'],1);out=r['drawing']
  self.assertEqual(out['bonds'],d['bonds']);self.assertEqual(out['annotations'],d['annotations'])
  for a,b in zip(out['atoms'],d['atoms']):self.assertEqual({k:v for k,v in a.items() if k not in ('x','y')},{k:v for k,v in b.items() if k not in ('x','y')})
  for b in out['bonds']:
   a=out['atoms'][int(b['a'])];c=out['atoms'][int(b['b'])];self.assertAlmostEqual(math.hypot(a['x']-c['x'],a['y']-c['y']),40,places=5)
 def test_protected_geometry(self):
  for d in [drawing(['Y','N'],[(0,1,1,'coord')]),drawing(['C','C'],[(0,1,1,'wedge')])]:
   r=cleanup(d);self.assertEqual(r['drawing'],d);self.assertEqual(r['cleaned_components'],0)
 def test_selected_component_only(self):
  d=drawing(['C','C','O','C'],[(0,1,1,'normal'),(2,3,1,'normal')]);r=cleanup(d,40,['0'])
  self.assertEqual(r['cleaned_components'],1);self.assertEqual(r['drawing']['atoms'][2:],d['atoms'][2:])
 def test_invalid_structure_unchanged(self):
  d=drawing(['C']+['F']*5,[(0,i,1,'normal') for i in range(1,6)]);self.assertEqual(cleanup(d)['drawing'],d)
 def test_warning_does_not_mutate(self):
  d=drawing(['C']+['H']*5,[(0,i,1,'normal') for i in range(1,6)]);old=copy.deepcopy(d);validate(d);self.assertEqual(d,old)

if __name__=='__main__':unittest.main()

class CentroidChemistryTests(unittest.TestCase):
 def cp(self):
  import math
  atoms=[{'id':str(i),'x':40*math.cos(i*math.pi*2/5),'y':40*math.sin(i*math.pi*2/5),'label':'C','charge':-1 if i==0 else 0} for i in range(5)]
  atoms.append({'id':'centroid','x':0,'y':0,'label':'','charge':0,'nodeType':'centroid','members':[str(i) for i in range(5)]})
  bonds=[{'id':'b'+str(i),'a':str(i),'b':str((i+1)%5),'order':2 if i in (1,3) else 1,'style':'normal'} for i in range(5)]
  return {'format':'chemsketch-classic','version':1,'name':'Cp','atoms':atoms,'bonds':bonds,'annotations':[],'ligands':[{'id':'cp','type':'cp-anion','atomIds':[str(i) for i in range(5)],'centroidId':'centroid'}]}
 def test_centroid_is_not_a_chemical_atom(self):
  d=self.cp();report=validate(d);self.assertEqual(report['checked_atoms'],5);self.assertFalse(report['complete']);self.assertFalse(any(issue['severity']=='warning' for issue in report['issues']));self.assertTrue(any('Centroid' in issue['message'] for issue in report['issues']))
 def test_cleanup_preserves_centroid_attachment_geometry(self):
  d=self.cp();out=cleanup(d);self.assertEqual(out['drawing'],d);self.assertTrue(any('Cp' in note for note in out['notes']))

 def test_cp_formula_excludes_virtual_attachment(self):
  from chemistry import chemical_graph,molecule
  from rdkit.Chem.rdMolDescriptors import CalcMolFormula
  from rdkit import Chem
  d,_=chemical_graph(self.cp());mol,_=molecule(d['atoms'],d['bonds']);Chem.SanitizeMol(mol);self.assertEqual(CalcMolFormula(mol),'C5H5-')

class PerspectiveCleanupTests(unittest.TestCase):
 def test_cleanup_preserves_projected_depth(self):
  d=drawing(['C','C'],[(0,1,1,'normal')]);d['atoms'][0]['z']=-20;d['atoms'][1]['z']=20
  result=cleanup(d)
  self.assertEqual(result['drawing'],d)
  self.assertEqual(result['cleaned_components'],0)
  self.assertTrue(any('Perspective' in note for note in result['notes']))
