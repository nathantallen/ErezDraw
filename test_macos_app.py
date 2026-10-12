"""Native file integration, independent of WebEngine rendering."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from macos_app import Editor

class FakeEditor:
    def __init__(self):
        self.path=None;self.saved_drawing=None;self.script=None;self.persisted=None
    def js(self,code,callback=None):
        self.script=code
        if callback:callback(json.dumps({'name':'Opened','atoms':[],'bonds':[]}))
    def persist(self,value):self.persisted=json.loads(value)

class NativeFiles(unittest.TestCase):
    def test_save_writes_named_editable_drawing(self):
        editor=FakeEditor()
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/'My structure'
            drawing={'name':'Untitled','atoms':[],'bonds':[]}
            with patch('macos_app.QFileDialog.getSaveFileName',return_value=(str(target),'')):
                self.assertTrue(Editor.save_document(editor,json.dumps(drawing)))
            output=target.with_suffix('.chemjson')
            self.assertEqual(json.loads(output.read_text())['name'],'My structure')
            self.assertEqual(editor.path,output)
            self.assertEqual(editor.persisted['name'],'My structure')
            self.assertIn('nativeSaveComplete',editor.script)
    def test_canceled_save_does_not_report_success_or_overwrite(self):
        editor=FakeEditor();editor.path=Path('/tmp/previous.chemjson')
        with patch('macos_app.QFileDialog.getSaveFileName',return_value=('','')):
            self.assertFalse(Editor.save_document(editor,json.dumps({'name':'Changed'})))
        self.assertIsNone(editor.persisted)
    def test_open_saved_json_and_mol(self):
        with tempfile.TemporaryDirectory() as folder:
            for extension,content,expression in [('chemjson','{"name":"Example","atoms":[],"bonds":[]}','ChemCore.validate'),('mol','MOL input','ChemCore.fromMol')]:
                path=Path(folder)/('Example.'+extension);path.write_text(content)
                editor=FakeEditor()
                with patch('macos_app.QFileDialog.getOpenFileName',return_value=(str(path),'')):
                    Editor.open_document(editor)
                self.assertIn(expression,editor.script)
                self.assertIsNotNone(editor.saved_drawing)
                self.assertEqual(editor.path,path if extension=='chemjson' else None)
    def test_open_cdxl_uses_bundled_chemdraw_parser(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'Example.cdxl'
            path.write_text('<CDXML><page><fragment><n id="1" p="10 20" Element="8"/></fragment></page></CDXML>')
            editor=FakeEditor()
            with patch('macos_app.QFileDialog.getOpenFileName',return_value=(str(path),'')):
                Editor.open_document(editor)
            self.assertIn('ChemCore.validate',editor.script)
            self.assertIn('"label": "O"',editor.script)
            self.assertIsNone(editor.path)

if __name__=='__main__':unittest.main()
