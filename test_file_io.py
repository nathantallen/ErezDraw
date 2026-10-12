import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from file_io import write_drawing

class AtomicSaveTests(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'drawing.chemjson'
            drawing={'name':'Y compound α','atoms':[]}
            write_drawing(path,drawing)
            self.assertEqual(json.loads(path.read_text(encoding='utf-8')),drawing)
    def test_failed_replace_preserves_previous_save(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'drawing.chemjson'
            path.write_text('previous drawing',encoding='utf-8')
            with patch('file_io.os.replace',side_effect=OSError('file locked')):
                with self.assertRaises(OSError):write_drawing(path,{'name':'new'})
            self.assertEqual(path.read_text(),'previous drawing')
            self.assertEqual(list(Path(directory).iterdir()),[path])

if __name__=='__main__':unittest.main()
