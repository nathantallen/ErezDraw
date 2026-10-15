import json
import unittest
from pathlib import Path
from glassware import glassware_catalog

class GlasswareTests(unittest.TestCase):
    def test_catalog_has_air_sensitive_and_pilot_equipment(self):
        catalog=glassware_catalog();names={p['name'] for p in catalog}
        self.assertEqual(len(names),len(catalog))
        for term in ['Schlenk','J. Young','Cannula','manifold','Jacketed','Nutsche','filter reactor']:
            self.assertTrue(any(term in name for name in names),term)
        for part in catalog:
            f=part['template'];self.assertEqual(f['atoms'],[]);self.assertEqual(f['bonds'],[])
            self.assertEqual(set(f['groups'][0]['annotations']),{a['id'] for a in f['annotations']})
            self.assertTrue(all(a['type']=='pen' and len(a['points'])>=2 for a in f['annotations']))
    def test_bundled_catalog_is_current(self):
        self.assertEqual(json.loads((Path(__file__).parent/'assets/glassware.json').read_text()),glassware_catalog())
    def test_mac_web_catalog_and_menu(self):
        from web.server import app
        with app.test_client() as c:
            data=c.get('/api/catalog').get_json()
            self.assertEqual(len(data['glassware']),31)
            self.assertIn(b'Show Glassware Templates',c.get('/web/desktop.js').data)
            self.assertIn(b'setGlasswareTemplate',c.get('/').data)
if __name__=='__main__':unittest.main()
