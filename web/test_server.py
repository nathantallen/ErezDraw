import unittest
import io
from web.server import app
from structure_ops import from_smiles

class WebTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.drawing = {**from_smiles('CCO'), 'annotations': [], 'groups': [], 'ligands': [], 'name': 'Ethanol'}
    def test_shell_assets_and_health(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'/web/app.js', response.data)
        self.assertIn(b'/web/style.css', response.data)
        for path in ('/health','/web/app.js','/web/style.css','/chemgeometry.js'):
            # Close streamed file responses, as a WSGI server would.
            with self.client.get(path) as asset:
                self.assertEqual(asset.status_code, 200)
        self.assertEqual(self.client.get('/web/server.py').status_code, 404)
    def test_chemistry_roundtrip(self):
        body = {'drawing': self.drawing, 'selected': []}
        for op in ('validate','cleanup','analysis','add-hydrogens','remove-hydrogens'):
            response = self.client.post('/api/'+op, json=body)
            self.assertEqual(response.status_code,200, response.json)
        response=self.client.post('/api/properties',json=body)
        self.assertEqual(response.json['formula'],'C2H6O')
    def test_desktop_catalog_and_models(self):
        catalog = self.client.get('/api/catalog')
        self.assertEqual(catalog.status_code, 200)
        self.assertEqual(len(catalog.json['elements']),118)
        self.assertEqual(len(catalog.json['ligands']),37)
        payload={'drawing':self.drawing,'selected':[]}
        self.assertEqual(self.client.post('/api/name-to-structure',json={**payload,'value':'ethanol'}).status_code,200)
        mass=self.client.post('/api/mass',json=payload)
        self.assertEqual(mass.status_code,200)
        self.assertEqual(len(mass.json['modes']),3)
        prep=self.client.post('/api/nmr-prepare',json=payload)
        self.assertEqual(prep.status_code,200)
        rows=[{'delta':1.2,'count':3,'attachedAtoms':[0],'matches':20,'level':3,'std':.1},
              {'delta':3.6,'count':2,'attachedAtoms':[1],'matches':20,'level':3,'std':.1},
              {'delta':2.0,'count':1,'attachedAtoms':[2],'matches':0,'level':0}]
        result=self.client.post('/api/nmr-simulate',json={**payload,'rows':rows,'nucleus':'1H','mhz':400,'coupled':True})
        self.assertEqual(result.status_code,200,result.json)
        self.assertEqual(len(result.json['lines']),3)
        self.assertAlmostEqual(sum(area for delta,area in result.json['lines'][0]),3,places=4)
        bad=self.client.post('/api/nmr-simulate',json={**payload,'rows':rows,'nucleus':'1H','mhz':-1})
        self.assertEqual(bad.status_code,400)

    def test_cdxml_and_cdxl_import(self):
        xml=b'<CDXML><page><fragment><n id="1" p="10 20" Element="6"/><n id="2" p="40 20" Element="8"/><b id="3" B="1" E="2" Order="1"/></fragment></page></CDXML>'
        for extension in ('cdxml','cdxl'):
            response=self.client.post('/api/import-chemdraw',data={'file':(io.BytesIO(xml),'example.'+extension)})
            self.assertEqual(response.status_code,200,response.json)
            self.assertEqual(len(response.json['drawing']['atoms']),2)
            self.assertEqual(response.json['drawing']['atoms'][1]['label'],'O')
        invalid=self.client.post('/api/import-chemdraw',data={'file':(io.BytesIO(b'not XML'),'bad.cdxl')})
        self.assertEqual(invalid.status_code,400)

    def test_pubchem_properties_identity(self):
        import json
        from unittest.mock import patch
        hit={'CID':702,'IUPACName':'ethanol','Title':'Ethanol','SMILES':'CCO','MolecularFormula':'C2H6O','Charge':0,'MolecularWeight':'46.07','XLogP':-.3}
        def response(*args,**kwargs):return io.BytesIO(json.dumps({'PropertyTable':{'Properties':[hit]}}).encode())
        with patch('structure_ops.urllib.request.urlopen',side_effect=response):
            result=self.client.post('/api/pubchem-properties',json={'drawing':self.drawing})
            self.assertEqual(result.status_code,200,result.json)
            self.assertEqual(result.json['properties']['MolecularWeight'],'46.07')
            self.assertEqual(result.json['cid'],702)
            hit['SMILES']='CO'
            rejected=self.client.post('/api/pubchem-properties',json={'drawing':self.drawing})
            self.assertEqual(rejected.status_code,400)
            self.assertIn('different',rejected.json['error'])

    def test_invalid_and_cross_origin(self):
        self.assertEqual(self.client.post('/api/validate',json={}).status_code,400)
        self.assertEqual(self.client.post('/api/validate',json={'drawing':self.drawing},headers={'Origin':'http://other.invalid'}).status_code,403)
        self.assertEqual(self.client.post('/api/smiles',json={'smiles':'not a molecule'}).status_code,400)
        self.assertEqual(self.client.get('/../../chemistry.py').status_code,404)

    def test_malformed_drawings_are_client_errors(self):
        import copy
        atom0, atom1 = self.drawing['atoms'][0]['id'], self.drawing['atoms'][1]['id']
        def changed(edit):
            drawing = copy.deepcopy(self.drawing); edit(drawing); return drawing
        cases = [
            lambda d: d['bonds'].append('not a bond'),
            lambda d: d['bonds'].append({**d['bonds'][0], 'id': 'duplicate'}),
            lambda d: d['bonds'].append({'id': 'self', 'a': atom0, 'b': atom0, 'order': 1, 'style': 'normal'}),
            lambda d: d['atoms'][0].update(charge=10**30),
            lambda d: d['atoms'][0].update(radical=-1),
            lambda d: d['atoms'][0].update(explicitHs=5000, noImplicit=True),
            lambda d: d['atoms'][0].update(abbreviation={'anchorId': 'missing', 'atoms': [], 'bonds': []}),
            lambda d: d['atoms'].append({'id': 'c', 'label': '', 'x': 0, 'y': 0, 'nodeType': 'centroid', 'members': [atom0, 'missing']}),
        ]
        for edit in cases:
            for op in ('validate', 'properties', 'analysis', 'add-hydrogens'):
                response = self.client.post('/api/'+op, json={'drawing': changed(edit), 'selected': []})
                self.assertEqual(response.status_code, 400, (op, response.json))
        response = self.client.post('/api/contract', json={'drawing': self.drawing, 'selected': [atom1], 'label': 5})
        self.assertEqual(response.status_code, 400)

    def test_nmr_rows_accept_null_level_and_pubchem_outage_is_reported(self):
        import urllib.error
        from unittest.mock import patch
        rows = [{'delta': 1.2, 'count': 3, 'attachedAtoms': [0], 'level': None, 'std': None}]
        result = self.client.post('/api/nmr-simulate', json={'drawing': self.drawing, 'rows': rows, 'nucleus': '1H', 'mhz': 400})
        self.assertEqual(result.status_code, 200, result.json)
        with patch('structure_ops.urllib.request.urlopen', side_effect=urllib.error.URLError('offline')):
            result = self.client.post('/api/lookup-name', json={'drawing': self.drawing, 'online': True})
        self.assertEqual(result.status_code, 400)
        self.assertIn('PubChem', result.json['error'])

if __name__ == '__main__': unittest.main()
