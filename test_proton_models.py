import unittest
from rdkit import Chem
from nmr_models import refine_proton_shifts,quantum_lines

def toluene_rows():return [dict(delta=7.3111,count=1,attachedAtoms=[4],level=5,std=.19),dict(delta=3.8121,count=2,attachedAtoms=[2,6],level=2,std=2.47),dict(delta=3.8121,count=2,attachedAtoms=[3,5],level=2,std=2.47),dict(delta=2.1627,count=3,attachedAtoms=[0],level=3,std=.607)]
class ProtonRegressionTests(unittest.TestCase):
 def test_toluene_bad_hose_fallback_is_not_used(self):
  m=Chem.MolFromSmiles('Cc1ccccc1');r=refine_proton_shifts(m,toluene_rows())
  self.assertEqual(r[-1]['delta'],2.34);self.assertEqual(r[-1]['count'],3);self.assertEqual(sum(x['count'] for x in r[:-1]),5)
  self.assertTrue(all(7<x['delta']<7.4 for x in r[:-1]));self.assertTrue(all('estimate' in x['source'] for x in r))
 def test_toluene_methyl_singlet_aromatic_coupled_area(self):
  m=Chem.MolFromSmiles('Cc1ccccc1');r=refine_proton_shifts(m,toluene_rows());lines=quantum_lines(m,r,400)
  self.assertEqual(lines[-1],[(2.34,3.0)]);self.assertGreater(len(lines[0]),3)
  for row,peak in zip(r,lines):self.assertAlmostEqual(sum(area for ppm,area in peak),row['count'],places=5)
 def test_frequency_changes_second_order_aromatic_shape(self):
  m=Chem.MolFromSmiles('Cc1ccccc1');r=refine_proton_shifts(m,toluene_rows())
  self.assertNotEqual(quantum_lines(m,r,100)[0],quantum_lines(m,r,800)[0])
 def test_benzene_equivalent_protons_are_one_resonance(self):
  m=Chem.MolFromSmiles('c1ccccc1');rows=[dict(delta=7.26,count=6,attachedAtoms=list(range(6)))];lines=quantum_lines(m,rows,400)
  self.assertEqual(len(lines[0]),1);self.assertAlmostEqual(lines[0][0][1],6)
 def test_ethanol_quantum_areas_and_splitting(self):
  m=Chem.MolFromSmiles('CCO');rows=[dict(delta=1.2,count=3,attachedAtoms=[0]),dict(delta=3.6,count=2,attachedAtoms=[1]),dict(delta=2,count=1,attachedAtoms=[2])];lines=quantum_lines(m,rows,400)
  methyl=sorted({round(ppm,2) for ppm,area in lines[0] if area>.01});methylene={round(ppm,2) for ppm,area in lines[1] if area>.01}
  self.assertEqual(len(methyl),3);self.assertEqual(len(methylene),4);self.assertEqual(len(lines[2]),1)
  self.assertAlmostEqual(sum(area for ppm,area in lines[0]),3,places=5)
 def test_unavailable_heteroatom_h_is_not_assigned_generic_ch(self):
  rows=[dict(delta=None,count=1,attachedAtoms=[2],level=0,std=0)];refine_proton_shifts(Chem.MolFromSmiles('CCO'),rows);self.assertIsNone(rows[0]['delta'])
