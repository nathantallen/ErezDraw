"""Native offscreen QA: live UI, real dialogs and SVG engine integration."""
import json,os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS','--no-sandbox --disable-gpu')
from PySide6.QtWidgets import QApplication,QDoubleSpinBox,QCheckBox,QRadioButton,QDialogButtonBox
from PySide6.QtCore import QTimer
from main import Editor
app=QApplication([]);app.setOrganizationName('ErezDrawUiTest');app.setApplicationName('ErezDrawUiTest');w=Editor();w.show();stage='load';error=None;pivot=None

def stop(message=None):
 global error,stage
 error=message;stage='done';w.allow_close=True;w.close();print('FAIL: '+message if message else 'PASS: palette and toolbar controls, correct disabled capabilities, native CW label rotation, Scale dialog label scaling, and Undo.',flush=True);app.exit(1 if message else 0)
def verify_rotation(value):
 global stage
 try:
  d=json.loads(value);assert d['atoms'][0]['labelAngle']==90;assert abs(d['atoms'][0]['x']-(pivot['x']-(100-pivot['y'])))<1e-6
  stage='scale';w.actions['scaleObjects'].trigger()
 except Exception as e:stop(repr(e))
def verify_scale(value):
 try:
  d=json.loads(value);assert d['atoms'][0]['textStyle']['size']==36;assert abs(d['atoms'][1]['y']-d['atoms'][0]['y']-80)<1e-6
  w.actions['undo'].trigger();QTimer.singleShot(150,lambda:w.js('JSON.stringify(doc)',verify_undo))
 except Exception as e:stop(repr(e))
def verify_undo(value):
 try:
  d=json.loads(value);assert 'textStyle' not in d['atoms'][0];assert d['atoms'][0]['labelAngle']==90;stop()
 except Exception as e:stop(repr(e))
def tick():
 global stage
 if stage=='done':return
 try:
  if stage=='load' and w.ready:
   assert len(w.tool_buttons)>=36 and 'cpAnion' in w.tool_buttons
   assert set(w.toolbars)=={'General','Object','Text Style'}
   assert all(not a.isEnabled() for a in w.unavailable_actions)
   assert w.zoom_combo.isVisible()
   stage='prepare';w.js("doc=ChemCore.blank();doc.atoms=[{id:'a',x:100,y:100,label:'N',charge:0},{id:'b',x:140,y:100,label:'O',charge:0}];doc.bonds=[{id:'ab',a:'a',b:'b',order:1,style:'normal'}];action('selectAll');JSON.stringify(rotationCenter(selectionBounds()));",prepared)
  dialog=app.activeModalWidget()
  if dialog and dialog.windowTitle()=='Rotate Objects' and stage=='rotate':
   assert len(dialog.findChildren(QRadioButton))==2
   dialog.findChild(QDoubleSpinBox).setValue(90);dialog.findChild(QCheckBox).setChecked(True);stage='waitrotate';dialog.accept();QTimer.singleShot(150,lambda:w.js('JSON.stringify(doc)',verify_rotation))
  elif dialog and dialog.windowTitle()=='Scale Objects' and stage=='scale':
   assert len(dialog.findChildren(QRadioButton))==3
   for spin in dialog.findChildren(QDoubleSpinBox):
    if spin.suffix()==' %':spin.setValue(200)
   dialog.findChild(QCheckBox).setChecked(True);stage='waitscale';dialog.accept();QTimer.singleShot(150,lambda:w.js('JSON.stringify(doc)',verify_scale))
 except Exception as e:stop(repr(e));return
 QTimer.singleShot(50,tick)
def prepared(value):
 global pivot
 pivot=json.loads(value);QTimer.singleShot(500,start_rotate)
def start_rotate():
 global stage
 stage='rotate';w.actions['rotate'].trigger()
QTimer.singleShot(100,tick);QTimer.singleShot(15000,lambda:stop('Timed out at '+stage));raise SystemExit(app.exec())
