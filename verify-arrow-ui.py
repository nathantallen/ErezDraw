"""Regression: activate tools through native QAction popup signals, then draw in live SVG."""
import os,json
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS','--no-sandbox --disable-gpu')
from PySide6.QtWidgets import QApplication,QToolButton,QWidgetAction
from PySide6.QtCore import QTimer
from main import Editor
app=QApplication([]);app.setOrganizationName('ErezDrawArrowTest');app.setApplicationName('ErezDrawArrowTest');w=Editor();w.show();pending=[]
def stop(error=None):
 print('FAIL: '+str(error) if error else 'PASS: all native popup variants, remembered arrow selection, live mouse-down preview, drag, mouse-up, cancel and Undo.',flush=True)
 w.allow_close=True;w.close();app.exit(1 if error else 0)
def next_tool():
 if not pending:stop();return
 key,button=pending.pop(0);button.click()
 expected=w.family_buttons[key]
 w.js('JSON.stringify(tool)',lambda value:checked(key,expected,value))
def checked(key,expected,value):
 try:
  assert isinstance(expected,str) and json.loads(value)==expected,(key,expected,value)
  if key!='arrow':next_tool();return
  w.tool_buttons[key].click()
  script="""(()=>{doc=ChemCore.blank();selection.clear();annSelection.clear();undoStack=[];render();const fire=(type,x,y)=>{const p=new DOMPoint(x,y).matrixTransform(canvas.getScreenCTM());canvas.dispatchEvent(new PointerEvent(type,{clientX:p.x,clientY:p.y,button:0,pointerId:1,bubbles:true}));};canvas.setPointerCapture=()=>{};fire('pointerdown',200,200);const down=doc.annotations.length===0&&!!canvas.querySelector('[data-preview]')&&undoStack.length===0;fire('pointermove',320,240);const move=doc.annotations.length===0;fire('pointerup',320,240);const up=doc.annotations.length===1&&undoStack.length===1&&doc.atoms.length===0;action('undo');fire('pointerdown',200,200);fire('pointercancel',200,200);return JSON.stringify({down,move,up,cancel:doc.annotations.length===0&&!gesture});})()"""
  w.js(script,drawn)
 except Exception as e:stop(e)
def drawn(value):
 try:assert all(json.loads(value).values()),value;next_tool()
 except Exception as e:stop(e)
def start():
 if not w.ready:QTimer.singleShot(100,start);return
 for key,parent in w.tool_buttons.items():
  menu=parent.menu()
  if not menu:continue
  for action in menu.actions():
   if isinstance(action,QWidgetAction):
    for button in action.defaultWidget().findChildren(QToolButton):
     if button.isEnabled():pending.append((key,button))
 next_tool()
QTimer.singleShot(100,start);QTimer.singleShot(20000,lambda:stop('Timeout'));raise SystemExit(app.exec())
