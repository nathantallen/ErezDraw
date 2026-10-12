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
try:
 wait_for(lambda:w.ready)
 for key in ['pen','table','orbital_p_phase']:assert w.tool_buttons[key].isEnabled();w.tool_buttons[key].click();assert js('tool')==key
 assert 'missing:query' not in w.tool_buttons
 for key in ['textLeft','textCenter','textRight','textJustify','subscript','superscript','formula','lineSpacing']:assert w.actions[key].isEnabled()
 result=json.loads(js("""(()=>{doc=ChemCore.blank();selection.clear();annSelection.clear();undoStack=[];setTool('text');const a={id:'caption',type:'text',x:250,y:200,text:'Cp3Y'};doc.annotations.push(a);edit(a,'text');const el=$('textEditor');const range=document.createRange();range.selectNodeContents(el);const sel=window.getSelection();sel.removeAllRanges();sel.addRange(range);rememberTextSelection();setTextStyle({bold:true});finishEditing();return JSON.stringify({runs:a.textRuns,valid:!!ChemCore.validate(doc),editable:el.isContentEditable});})()"""))
 assert result['editable'] and result['valid'] and all(r['bold'] for r in result['runs']),result
 # Select only the numeral and format it without changing neighboring characters.
 result=json.loads(js("""(()=>{const a=doc.annotations[0];edit(a,'text');const el=$('textEditor'),text=el.firstChild.firstChild,range=document.createRange();range.setStart(text,2);range.setEnd(text,3);const sel=window.getSelection();sel.removeAllRanges();sel.addRange(range);rememberTextSelection();setTextStyle({script:'sub'});finishEditing();return JSON.stringify({text:a.text,runs:a.textRuns,valid:!!ChemCore.validate(doc)});})()"""))
 assert result['text']=='Cp3Y' and result['valid'] and any(r['text']=='3' and r['script']=='sub' for r in result['runs']),result
 js("edit(doc.annotations[0],'text');rememberTextSelection();")
 w.clipboard_copy();wait_for(lambda:QApplication.clipboard().mimeData().hasText());assert QApplication.clipboard().mimeData().text()=='Cp3Y';assert js("$('textEditor').value")=='Cp3Y';js('finishEditing()')
 # Every graphic enters SVG and raster clipboard; paste retains editable objects.
 js("doc.annotations.push({id:'p',type:'pen',x:300,y:300,angle:0,points:[{x:0,y:0,hx:30,hy:-50},{x:100,y:0,hx:30,hy:50}],closed:false,heads:'end',fill:'none',lineWidth:1.7},{id:'o',type:'orbital',x:350,y:380,width:90,height:90,angle:0,kind:'dxy',fill:'phase'},{id:'tab',type:'table',x:200,y:430,width:240,height:90,angle:0,rows:2,cols:2,cells:['Ligand','Mass','Cp','65.095']});doc=ChemCore.validate(doc);action('selectAll');render();")
 w.clipboard_copy();wait_for(lambda:QApplication.clipboard().mimeData().hasImage());mime=QApplication.clipboard().mimeData();assert mime.hasFormat('image/svg+xml') and mime.hasFormat('image/png') and not mime.hasText();assert QSvgRenderer(mime.data('image/svg+xml')).isValid();image=mime.imageData();assert image.width()>200 and image.height()>200
 old=js('doc.annotations.length');w.clipboard_paste();wait_for(lambda:js('doc.annotations.length')==old*2)
 def table(q):assert q.findChild(QTableWidget).rowCount()==2;assert q.findChildren(QSpinBox)[0].maximum()==30
 modal(lambda:w.edit_table('tab'),'Edit Table',table)
 # Local NMR spectrum signal highlights nuclei in live canvas and is copyable.
 for nucleus,key in [('1H','nmrH'),('13C','nmrC')]:
  d={'format':'chemsketch-classic','version':1,'name':'Ethanol',**from_smiles('CCO'),'annotations':[]};js('doc=ChemCore.validate('+json.dumps(d)+');selection.clear();annSelection.clear();render();')
  def nmr(q):
   spectrum=q.findChild(SpectrumWidget);assert spectrum is not None and spectrum.rows;delta=spectrum.rows[0]['delta'];assert 0 in spectrum.peaks_near(spectrum.xpos(delta));frequency=q.findChildren(QDoubleSpinBox)[0];frequency.setValue(800);assert abs(spectrum.mhz-(800 if nucleus=='1H' else 800*.25144953))<1e-6;spectrum.hovered.emit([0]);wait_for(lambda:js('nmrHighlights&&nmrHighlights.ids.length')>0);assert js('nmrHighlights.nucleus')==nucleus
   next(b for b in q.findChildren(QPushButton) if b.text()=='Copy Spectrum').click();assert QApplication.clipboard().mimeData().hasImage();q.grab().save('/tmp/erezdraw-nmr-'+nucleus+'.png')
  modal(lambda:w.actions[key].trigger(),nucleus+' NMR Prediction',nmr)
 def mass(q):
  from mass_ui import MassPlot
  plot=q.findChild(MassPlot);assert plot and len(plot.rows)>1;plot.hovered.emit([0]);wait_for(lambda:js('nmrHighlights&&nmrHighlights.ids.length')>0)
  next(b for b in q.findChildren(QPushButton) if b.text()=='Copy Spectrum').click();assert QApplication.clipboard().mimeData().hasImage()
 modal(lambda:w.actions['massFragmentation'].trigger(),'Mass Spectrometry Fragmentation',mass)
 w.grab().save('/tmp/erezdraw-expanded-ui.png')
 print('PASS: active pen/table/orbitals, removed Query, all text bar controls, native inline rich substring editing, SVG/PNG/native image clipboard and editable paste, table dialog, 1H/13C spectrum hover assignment and Copy Spectrum.',flush=True)
except Exception as e:w.grab().save('/tmp/expanded-failure.png');print('FAIL:',repr(e),flush=True);raise
finally:QApplication.clipboard().clear();w.allow_close=True;w.close();app.processEvents()
