import unittest
from rdkit import Chem
from structure_ops import from_smiles
from mass_spec import fragmentation,ELECTRON_MASS
from nmr_spectrum import multiplet_lines,estimate_couplings

def drawing(smiles):return {'format':'chemsketch-classic','version':1,'name':'Test',**from_smiles(smiles),'annotations':[]}
class SpectrumTests(unittest.TestCase):
 def test_triplet_intensities_and_frequency(self):
  row={'delta':1.2,'count':3,'couplings':[{'j':7,'n':2}]}
  a=multiplet_lines(row,400);b=multiplet_lines(row,800)
  self.assertAlmostEqual(sum(area for _,area in a),3)
  self.assertEqual([area for _,area in a],[.75,1.5,.75])
  self.assertAlmostEqual(a[2][0]-a[1][0],7/400)
  self.assertAlmostEqual(b[2][0]-b[1][0],7/800)
 def test_ethanol_triplet_quartet_exchangeable(self):
  rows=[{'attachedAtoms':[i]} for i in range(3)];estimate_couplings(Chem.MolFromSmiles('CCO'),rows)
  self.assertEqual(rows[0]['couplings'],[{'j':7.0,'n':2}]);self.assertEqual(rows[1]['couplings'],[{'j':7.0,'n':3}]);self.assertEqual(rows[2]['couplings'],[])
 def test_carbon_is_decoupled(self):
  self.assertEqual(multiplet_lines({'delta':20,'count':1,'couplings':[{'j':7,'n':3}]},100,'13C'),[(20,1)])
 def test_mass_parent_and_methyl_candidate(self):
  result=fragmentation(drawing('CCO'));parent=next(r for r in result['rows'] if r['precursor']);methyl=next(r for r in result['rows'] if r['formula']=='CH3+')
  self.assertAlmostEqual(parent['mz'],46.041864812-ELECTRON_MASS,places=6);self.assertAlmostEqual(methyl['mz'],15.023475096-ELECTRON_MASS,places=6)
 def test_esi_adduct_shift(self):
  d=drawing('CCO');ei=next(r for r in fragmentation(d)['rows'] if r['precursor']);esi=next(r for r in fragmentation(d,mode='ESI [M+H]+')['rows'] if r['precursor'])
  self.assertAlmostEqual(esi['mz']-ei['mz'],1.007825032,places=6);self.assertEqual(esi['formula'],'C2H7O+')
 def test_ring_is_not_silently_split(self):
  self.assertEqual(len(fragmentation(drawing('C1CCCCC1'))['rows']),1)
 def test_metals_rejected(self):
  with self.assertRaisesRegex(ValueError,'Metal'):fragmentation(drawing('[Y]'))
 def test_hydrogen_free_molecule_rejects_hydrogen_loss_mode(self):
  d=drawing('ClC(Cl)(Cl)Cl')
  with self.assertRaisesRegex(ValueError,'removes a hydrogen'):fragmentation(d,mode='ESI [M-H]-')
  self.assertTrue(fragmentation(d,mode='EI molecular radical cation')['rows'])
