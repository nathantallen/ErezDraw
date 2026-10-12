import struct,unittest
from chemdraw_io import import_chemdraw,ImportErrorDetail

def prop(tag,data):return struct.pack('<HH',tag,len(data))+data

def obj(tag,id,*parts):return struct.pack('<HI',tag,id)+b''.join(parts)+b'\0\0'

def position(x,y):return prop(0x0200,struct.pack('<ii',int(y*65536),int(x*65536)))

def integer(tag,value,size=2,signed=False):return prop(tag,value.to_bytes(size,'little',signed=signed))

def cdx_fixture():
 return b'VjCD0100'+b'\x04\x03\x02\x01'+b'\0'*16+obj(0x8001,1,obj(0x8003,2,obj(0x8004,3,position(10,20),integer(0x0402,8),integer(0x0421,-1,1,True),integer(0x0422,2,1)),obj(0x8004,4,position(40,20)),obj(0x8005,5,integer(0x0604,3,4),integer(0x0605,4,4),integer(0x0600,2),integer(0x0603,2))))+b'\0\0'

class ChemDrawImportTests(unittest.TestCase):
 def test_binary_charge_radical_position_and_double_side(self):
  r=import_chemdraw(cdx_fixture());d=r['drawing'];self.assertEqual(len(d['atoms']),2);self.assertEqual(d['atoms'][0]['charge'],-1);self.assertEqual(d['atoms'][0]['radical'],1);self.assertAlmostEqual(d['atoms'][0]['y'],20*4/3);self.assertEqual(d['bonds'][0]['doublePosition'],'left');self.assertFalse(r['warnings'])
 def test_xml_labels_styles_wedge_end_caption_and_graphic(self):
  xml=b'''<CDXML LineWidth="0.6" BondLength="14.4" BondSpacing="18"><fonttable><font id="3" name="Arial"/></fonttable><page><fragment><n id="1" p="10 20" Element="7" Charge="1"><t><s font="3" size="10" face="1">NH2</s></t></n><n id="2" p="30 20"/><b B="1" E="2" Display="WedgeEnd"/></fragment><t p="40 50"><s size="12">Caption</s></t><graphic GraphicType="Line" ArrowType="Equilibrium" BoundingBox="90 30 50 30"/></page></CDXML>'''
  d=import_chemdraw(xml)['drawing'];self.assertEqual(d['atoms'][0]['label'],'NH2');self.assertTrue(d['atoms'][0]['textStyle']['bold']);self.assertEqual(d['bonds'][0]['style'],'wedge');self.assertEqual(d['bonds'][0]['a'],d['atoms'][1]['id']);self.assertEqual(d['annotations'][1]['variant'],'equilibrium');self.assertAlmostEqual(d['drawingSettings']['lineWidth'],.8)
 def test_reject_truncated_cdx(self):
  for cut in [1,4,10,20]:
   with self.assertRaises(ImportErrorDetail):import_chemdraw(cdx_fixture()[:-cut])
 def test_reject_entities(self):
  with self.assertRaises(ImportErrorDetail):import_chemdraw(b'<!DOCTYPE CDXML [<!ENTITY x "foo">]><CDXML>&x;</CDXML>')
 def test_unsupported_bond_rejected(self):
  with self.assertRaises(ImportErrorDetail):import_chemdraw(b'<CDXML><page><fragment><n id="1" p="0 0"/><n id="2" p="10 10"/><b B="1" E="2" Order="Any"/></fragment></page></CDXML>')
 def test_nested_and_rich_text_warnings(self):
  r=import_chemdraw(b'<CDXML><page><n id="1" p="0 0"><t><s>A</s><s>B</s></t><fragment><n id="2" p="1 1"/></fragment></n><curve/></page></CDXML>');self.assertEqual(len(r['drawing']['atoms']),1);self.assertTrue(any('Nested' in w for w in r['warnings']));self.assertTrue(any('Rich' in w for w in r['warnings']));self.assertTrue(any('curve' in w for w in r['warnings']))

if __name__=='__main__':unittest.main()
