"""Native regressions for Structure/View commands and bundled offline NMR."""
import os,json,time
os.environ.setdefault('QT_QPA_PLATFORM','offscreen');os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS','--no-sandbox --disable-gpu')
from PySide6.QtWidgets import QApplication,QDialog,QLineEdit,QTableWidget,QPushButton,QToolButton,QWidgetAction,QSpinBox
from PySide6.QtCore import QTimer,QEventLoop
from main import Editor
from structure_ops import from_smiles
from rdkit import Chem
from ligands import LIGANDS,ligand_template
app=QApplication([]);app.setOrganizationName('ErezDrawStructureTest');app.setApplicationName('ErezDrawStructureTest');w=Editor();w.show()
def wait_for(fn,timeout=15000):
 loop=QEventLoop();timer=QTimer();timer.setInterval(20);deadline=time.monotonic()+timeout/1000;result=[]
 def tick():
  try:
   value=fn()
   if value:result.append(value);loop.quit()
   elif time.monotonic()>deadline:result.append(TimeoutError());loop.quit()
  except Exception as e:result.append(e);loop.quit()
 timer.timeout.connect(tick);timer.start();loop.exec();timer.stop()
 if isinstance(result[0],Exception):raise result[0]
 return result[0]
def js(code):
 result=[];w.js(code,lambda v:result.append(v));wait_for(lambda:bool(result));return result[0]
def blank(smiles='CCO'):
 d={'format':'chemsketch-classic','version':1,'name':'QA',**from_smiles(smiles),'annotations':[]}
 js('doc=ChemCore.validate('+json.dumps(d)+');selection.clear();annSelection.clear();undoStack=[];render();');return d
def dialog(key,title,check):
 error=[];done=[]
 def inspect():
  modal=app.activeModalWidget()
  if modal and modal.windowTitle()==title:
   try:check(modal)
   except Exception as e:error.append(e);modal.reject()
   done.append(True)
  elif not done:QTimer.singleShot(25,inspect)
 QTimer.singleShot(25,inspect);w.actions[key].trigger();wait_for(lambda:done)
 if error:raise error[0]
try:
 wait_for(lambda:w.ready)
 assert all(a.text().replace('&','')!='Online' for a in w.menuBar().actions())
 assert 'missing:tlc' not in w.tool_buttons and 'ligands' in w.tool_buttons
 assert not any('Cp' in a.text() or 'Increase Charge' in a.text() or 'Decrease Charge' in a.text() for a in w.menus['Structure'].actions())
 assert all(a.isEnabled() for a in w.menus['Structure'].actions() if not a.isSeparator())
 d=blank();w.actions['addH'].trigger();wait_for(lambda:json.loads(js('JSON.stringify(doc)'))['atoms'].__len__()==9)
 w.actions['removeH'].trigger();wait_for(lambda:len(json.loads(js('JSON.stringify(doc)'))['atoms'])==3)
 js('selection=new Set([doc.atoms[2].id]);render()')
 def atom(q):q.findChildren(QSpinBox)[0].setValue(-1);q.accept()
 dialog('atomProperties','Atom Properties',atom);wait_for(lambda:js('doc.atoms[2].charge')==-1);js("action('undo')")
 js('selection=new Set([doc.atoms[0].id,doc.atoms[1].id]);render()')
 def contracted(q):q.findChild(QLineEdit).setText('Et');q.accept()
 dialog('contract','Contract Label',contracted);wait_for(lambda:js('doc.atoms.length')==2);w.actions['expand'].trigger();wait_for(lambda:js('doc.atoms.length')==3)
 blank()
 def label(q):assert q.findChild(QLineEdit).text()=='ethanol';q.accept()
 dialog('moleculeLabel','Label Molecule',label);wait_for(lambda:len(json.loads(js('JSON.stringify(doc)'))['annotations'])==2)
 assert '46.069' in js('doc.annotations[1].text')
 for nucleus,key in [('1H','nmrH'),('13C','nmrC')]:
  def nmr(q):
   table=q.findChild(QTableWidget);assert table.rowCount()==(3 if nucleus=='1H' else 2);assert all(table.item(i,2).text() for i in range(table.rowCount()));q.reject()
  dialog(key,nucleus+' NMR Prediction',nmr)
 for name,dock in w.view_panels.items():
  w.actions['panel_'+name].trigger();assert dock.isVisible();w.actions['panel_'+name].trigger();assert not dock.isVisible()
 w.actions['panel_Analysis'].trigger();w.update_view_panels();wait_for(lambda:'C2H6O' in w.panel_text['Analysis'].toPlainText());w.actions['panel_Analysis'].trigger()
 w.actions['rulers'].trigger();w.actions['crosshair'].trigger();assert js("!!canvas.querySelector('[data-view-guides]')")
 assert 'data-view-guides' not in js('exportSVG().text')
 w.actions['rulers'].trigger();w.actions['crosshair'].trigger()
 # All ligand fragments survive live document validation and can be drawn as a preview transaction.
 for _,name,_,_ in LIGANDS:
  fragment=ligand_template(name);result=js("(()=>{doc=ChemCore.blank();selection.clear();annSelection.clear();undoStack=[];setLigandTemplate("+json.dumps(fragment)+");const saved=JSON.stringify(doc);const g={kind:'stamp',p:{x:300,y:300},end:{x:300,y:300},stampTool:'ligandTemplate'};creationPreview(g);if(JSON.stringify(doc)!==saved)throw Error('Preview mutated doc');const before=snapshot();applyStamp(g.p,'ligandTemplate');commit(before);doc=ChemCore.validate(doc);copy();paste();doc=ChemCore.validate(doc);return JSON.stringify({atoms:doc.atoms.length,undo:undoStack.length})})()")
  parsed=json.loads(result);assert parsed['atoms']==2*len(fragment['atoms']),name
 # Arrow popup rows are full heads then half heads, with increasing arc angle.
 menu=w.tool_buttons['arrow'].menu();container=next(a for a in menu.actions() if isinstance(a,QWidgetAction));buttons=container.defaultWidget().findChildren(QToolButton)
 assert [b.text() for b in buttons[:5]]==['Full head — Straight','Full head — 90°','Full head — 120°','Full head — 180°','Full head — 270°']
 assert [b.text() for b in buttons[5:10]]==['Half head — Straight','Half head — 90°','Half head — 120°','Half head — 180°','Half head — 270°']
 print('PASS: native menu removals; hydrogen commands; molecule name/MW labels; offline proton/carbon prediction and atom assignments; View panels/guides; 37 ligand templates preview, save validation and copy/paste; arrow row ordering.',flush=True)
except Exception as e:
 print('FAIL:',repr(e),flush=True);raise
finally:w.allow_close=True;w.close()
