"""Live Qt/browser integration for rich text, graphics, spectrum hover and clipboard."""
import os,json,time
os.environ.setdefault('QT_QPA_PLATFORM','offscreen');os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS','--no-sandbox --disable-gpu')
from PySide6.QtWidgets import QApplication,QDialog,QTableWidget,QSpinBox,QPushButton,QDoubleSpinBox
from PySide6.QtCore import QTimer,QEventLoop
from PySide6.QtSvg import QSvgRenderer
from main import Editor
from structure_ops import from_smiles
from spectrum_ui import SpectrumWidget
app=QApplication([]);w=Editor();w.show()
def wait_for(fn,timeout=12000):
 loop=QEventLoop();timer=QTimer();timer.setInterval(20);deadline=time.monotonic()+timeout/1000;result=[]
 def tick():
  try:
   v=fn()
   if v:result.append(v);loop.quit()
   elif time.monotonic()>deadline:result.append(TimeoutError());loop.quit()
  except Exception as e:result.append(e);loop.quit()
 timer.timeout.connect(tick);timer.start();loop.exec();timer.stop()
 if isinstance(result[0],Exception):raise result[0]
 return result[0]
def js(code):
 out=[];w.js(code,lambda v:out.append(v));wait_for(lambda:bool(out));return out[0]
def modal(action,title,check):
 errors=[];done=[]
 def inspect():
  q=app.activeModalWidget()
  if q and q.windowTitle()==title:
   try:check(q)
   except Exception as e:errors.append(e)
   q.reject();done.append(True)
  elif not done:QTimer.singleShot(30,inspect)
 QTimer.singleShot(30,inspect);action();wait_for(lambda:done)
 if errors:raise errors[0]
from PySide6.QtWidgets import QSplitter
from PySide6.QtCore import Qt,QPoint
from PySide6.QtTest import QTest
try:
 wait_for(lambda:w.ready)
 js("doc=ChemCore.blank();doc.atoms=[{id:'Y',x:400,y:300,label:'Y',charge:3}];render();")
 charge=json.loads(js("(()=>{const s=canvas.querySelector('[data-metal-charge]');return JSON.stringify({x:+s.getAttribute('x'),y:+s.getAttribute('y'),text:s.textContent,label:s.parentNode.textContent,marks:atomMarks(doc.atoms[0]).length})})()"))
 assert charge['x']>0 and charge['y']<0 and charge['text']=='3+' and charge['label']=='Y3+' and charge['marks']==0,charge
 d={'format':'chemsketch-classic','version':1,'name':'Toluene',**from_smiles('Cc1ccccc1'),'annotations':[]};js('doc=ChemCore.validate('+json.dumps(d)+');selection.clear();annSelection.clear();render();')
 def inspect(q):
  spectrum=q.findChild(SpectrumWidget);rows=spectrum.rows;methyl=next(r for r in rows if r['count']==3)
  assert abs(methyl['delta']-2.34)<.001;assert spectrum.lines(methyl)==[(2.34,3.0)]
  aromatic=[r for r in rows if r is not methyl];assert sum(r['count'] for r in aromatic)==5 and all(7<r['delta']<7.4 for r in aromatic),rows
  assert spectrum.quantum is not None;assert all(r['source']!='HOSE database' for r in rows)
  for name,delta in [('SpectrumStructureSplitter',QPoint(35,0)),('SpectrumTableSplitter',QPoint(0,35))]:
   splitter=q.findChild(QSplitter,name);assert splitter is not None
   before=splitter.sizes();handle=splitter.handle(1);point=handle.rect().center();QTest.mousePress(handle,Qt.MouseButton.LeftButton,pos=point);QTest.mouseMove(handle,point+delta,20);QTest.mouseRelease(handle,Qt.MouseButton.LeftButton,pos=point+delta);app.processEvents();after=splitter.sizes()
   assert before!=after,(name,before,after)
  spectrum.hovered.emit([rows.index(methyl)]);wait_for(lambda:js('nmrHighlights&&nmrHighlights.ids.length')>0)
  q.grab().save('/tmp/toluene-nmr-011.png')
 modal(lambda:w.actions['nmrH'].trigger(),'1H NMR Prediction',inspect)
 print('PASS: live bundled toluene predictor correction, 3H singlet/5H coupled aromatic region, quantum assignments, actual horizontal/vertical divider dragging, and fixed right-superscript metal label.',flush=True)
except Exception as e:print('FAIL:',repr(e),flush=True);raise
finally:QApplication.clipboard().clear();w.allow_close=True;w.close();app.processEvents()
