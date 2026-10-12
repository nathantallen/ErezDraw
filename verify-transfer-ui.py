"""Actual browser metrics and centroid ligand integration inside native Qt."""
import os,sys,json
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen');os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS','--no-sandbox --disable-gpu')
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from main import Editor
from chemistry import validate
app=QApplication([]);app.setOrganizationName('ErezDrawTransferQA');app.setApplicationName('ErezDrawTransferQA');w=Editor();w.show()

def stop(error=None):
 w.allow_close=True;w.close();print('FAIL: '+str(error) if error else 'PASS: browser font metrics, label clipping, Cp3Y centroid attachments, source validation, SVG export and drawing serialization.',flush=True);app.exit(1 if error else 0)
def scenario(value):
 try:
  report=json.loads(value);assert report['axis']['x2']<report['label']['x']
  assert report['label']['x2']-report['label']['x']>40
  assert report['lineCount']>0
  w.js("doc=ChemCore.blank();const y=addAtom({x:400,y:250},'Y');y.charge=3;for(const p of [{x:240,y:180},{x:560,y:180},{x:400,y:440}]){const l=placeCpAnion(p);addBond(ChemCore.atom(doc,l.centroidId),y,1,'coord')}setTool('select');selection.clear();annSelection.clear();fit();render();JSON.stringify({drawing:ChemCore.validate(doc),svg:exportSVG().text});",checked)
 except Exception as e:stop(e)
def checked(value):
 try:
  report=json.loads(value);d=report['drawing'];assert len(d['atoms'])==19;assert len(d['ligands'])==3
  for l in d['ligands']:
   nodes=[a for a in d['atoms'] if a['id'] in l['atomIds']];center=next(a for a in d['atoms'] if a['id']==l['centroidId'])
   assert abs(center['x']-sum(a['x'] for a in nodes)/5)<1e-6;assert any(b['a']==center['id'] or b['b']==center['id'] for b in d['bonds'])
  assert validate(d)['checked_atoms']==15
  if '--write-example' in sys.argv:
   example=Path(__file__).parent/'examples'/'Cp3Y_centroid.chemjson';example.parent.mkdir(exist_ok=True);example.write_text(json.dumps(d,indent=2),encoding='utf-8')
  assert 'Cp' not in report['svg'] # graphical ligand has no fake atom label
  assert report['svg'].count('<circle')==3 # delocalization circles; editor handles are excluded
  QTimer.singleShot(500,capture)
 except Exception as e:stop(e)
def capture():
 # Optional internal QA image; not included in application package.
 if '--capture' in sys.argv:w.grab().save(str(Path('cp-centroid-qa.png').resolve()))
 stop()
def start():
 if not w.ready:QTimer.singleShot(100,start);return
 w.js("doc=ChemCore.blank();const a=addAtom({x:100,y:120},'C'),b=addAtom({x:250,y:120},'NMe3');addBond(a,b);render();JSON.stringify({axis:bondAxis(doc.bonds[0]),label:atomLabelBounds(b),lineCount:drawingGroup().childNodes.length});",scenario)
QTimer.singleShot(200,start);QTimer.singleShot(15000,lambda:stop('Timeout'));raise SystemExit(app.exec())
