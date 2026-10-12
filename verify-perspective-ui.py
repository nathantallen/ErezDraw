"""Live native trackball activation, SVG pointer events and Flatten regression."""
import os,json
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS','--no-sandbox --disable-gpu')
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from main import Editor
app=QApplication([]);w=Editor();w.show()
def stop(error=None):
 print('FAIL: '+str(error) if error else 'PASS: native Structure Perspective button, live chemical marquee/tilt/Shift/cancel/Undo, centroid depth, persistence and native Flatten.',flush=True)
 w.allow_close=True;w.close();app.exit(1 if error else 0)
def flattened(value):
 try:
  r=json.loads(value);assert r['flat'] and r['xy'] and r['undo'],r;stop()
 except Exception as e:stop(e)
def tilted(value):
 try:
  r=json.loads(value);assert all(r.values()),r
  w.actions['flatten'].setEnabled(True);w.actions['flatten'].trigger()
  w.js("JSON.stringify({flat:doc.atoms.every(a=>a.z===undefined),xy:doc.atoms.every((a,i)=>a.x===tiltSaved.atoms[i].x&&a.y===tiltSaved.atoms[i].y),undo:undoStack.length===2})",flattened)
 except Exception as e:stop(e)
def start():
 if not w.ready:QTimer.singleShot(100,start);return
 try:
  assert w.tool_buttons['trackball'].isEnabled();w.tool_buttons['trackball'].click()
  w.js("""(()=>{doc=ChemCore.blank();placeCpAnion({x:350,y:300});doc.annotations=[{id:'t',type:'text',x:350,y:300,text:'Caption'}];selection.clear();annSelection.clear();undoStack=[];redoStack=[];render();const fire=(type,x,y,shiftKey=false)=>{const p=new DOMPoint(x,y).matrixTransform(canvas.getScreenCTM());canvas.dispatchEvent(new PointerEvent(type,{clientX:p.x,clientY:p.y,shiftKey,button:0,pointerId:1,bubbles:true}));};canvas.setPointerCapture=()=>{};fire('pointerdown',270,220);fire('pointermove',430,380);fire('pointerup',430,380);const marquee=selection.size===6&&annSelection.size===0,activated=tool==='trackball';const flat=snapshot();fire('pointerdown',350,300);fire('pointermove',380,305,true);const preview=undoStack.length===0&&gesture.rx===0&&doc.atoms.some(a=>Math.abs(a.z)>1);fire('pointercancel',380,305);const cancel=JSON.stringify(doc)===JSON.stringify(flat);fire('pointerdown',350,300);fire('pointermove',380,305,true);fire('pointerup',380,305,true);window.tiltSaved=snapshot();const centerAtom=doc.atoms.find(a=>a.nodeType==='centroid');const depth=Math.abs(centerAtom.z-doc.atoms.filter(a=>a.nodeType!=='centroid').reduce((s,a)=>s+a.z,0)/5)<1e-6;const loaded=ChemCore.validate(doc);const persisted=loaded.atoms.every((a,i)=>a.z===doc.atoms[i].z&&a.x===doc.atoms[i].x&&a.y===doc.atoms[i].y);return JSON.stringify({marquee,activated,preview,cancel,depth,persisted,committed:undoStack.length===1,caption:doc.annotations[0].x===350});})()""",tilted)
 except Exception as e:stop(e)
QTimer.singleShot(100,start);QTimer.singleShot(20000,lambda:stop('Timeout'));raise SystemExit(app.exec())
