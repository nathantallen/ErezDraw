"""Real Qt pointer events through the native Mac/web template cascade."""
import os,time,tempfile,sys
from pathlib import Path
# Exercise the actual Cocoa WebEngine backend on the macOS runner.
if sys.platform=='darwin':os.environ.pop('QT_QPA_PLATFORM',None)
else:os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS','--no-sandbox --disable-gpu')
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt,QPoint,QTimer
from PySide6.QtTest import QTest
from macos_app import LocalServer,Editor
app=QApplication([]);server=LocalServer();tmp=tempfile.TemporaryDirectory(ignore_cleanup_errors=True);w=Editor(server,Path(tmp.name));w.show();w.activateWindow();w.raise_();w.view.setFocus()
def wait(fn,seconds=30):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  app.processEvents();QTest.qWait(15)
  if fn():return
 raise AssertionError('Timed out')
def js(code):
 out=[];w.js(code,lambda value:out.append(value));wait(lambda:bool(out));return out[0]
def rect(selector):
 return __import__('json').loads(js("(()=>{const r=document.querySelector("+__import__('json').dumps(selector)+").getBoundingClientRect();return JSON.stringify([r.x+r.width/2,r.y+r.height/2])})()"))
def point(selector):
 x,y=rect(selector);target=w.view.focusProxy() or w.view
 width,height=__import__('json').loads(js('JSON.stringify([innerWidth,innerHeight])'))
 return QPoint(round(x*target.width()/width),round(y*target.height()/height))
errors=[]
def run():
 try:
  wait(lambda:w.loaded,seconds=120);wait(lambda:js("!!document.querySelector('.web-tool-grid [data-tool=templates]')"))
  js("finishEditing();doc=ChemCore.blank();render();")
  # Load once before the quick gesture; opening itself is asynchronous.
  js("document.querySelector('[data-tool=templates]').click()")
  wait(lambda:js("!!document.querySelector('.template-cascade')"));QTest.keyClick(w.view.focusProxy() or w.view,Qt.Key.Key_Escape)
  wait(lambda:js("!document.querySelector('.template-cascade')"))
  target=w.view.focusProxy() or w.view
  js("document.querySelector(\"[data-tool=templates]\").scrollIntoView({block: \"nearest\"})")
  QTest.mousePress(target,Qt.MouseButton.LeftButton,pos=point('[data-tool=templates]'))
  wait(lambda:js("!!document.querySelector('.template-cascade')"))
  # Hover category and release over an icon without pressing that icon.
  index=int(js("[...document.querySelectorAll('.template-category')].findIndex(e=>e.textContent.startsWith('Labware'))"))
  sel=f'.template-category:nth-child({index+1})';QTest.mouseMove(target,point(sel));app.processEvents()
  wait(lambda:js("document.querySelector('.template-category[aria-expanded=true]').textContent.startsWith('Labware')"))
  QTest.mouseMove(target,point('.template-icon'));QTest.mouseRelease(target,Qt.MouseButton.LeftButton,pos=point('.template-icon'));app.processEvents()
  wait(lambda:js("!document.querySelector('.template-cascade')"));assert js("tool==='glasswareTemplate'"),js('tool')
  assert js('doc.annotations.length')==0,'Picking a template must not stamp it'
  QTest.mouseClick(target,Qt.MouseButton.LeftButton,pos=point('#canvas'));wait(lambda:js('doc.annotations.length')>0)
  before=js('JSON.stringify(doc)');QTest.mousePress(target,Qt.MouseButton.LeftButton,pos=point('#canvas'));wait(lambda:js('gesture!==null'));QTest.keyClick(target,Qt.Key.Key_Escape);wait(lambda:js('gesture===null'));QTest.mouseRelease(target,Qt.MouseButton.LeftButton,pos=point('#canvas'));app.processEvents();assert js('JSON.stringify(doc)')==before
  # Closed picker must not consume Escape intended for drawing gestures.
  assert js('gesture===null')
  print('PASS: native web pointer press/hold, hover category, release-to-select, separate canvas placement and Escape cancellation')
 except Exception as error:
  errors.append(error)
  print('Pointer diagnostic:',js("JSON.stringify({dpr:devicePixelRatio,width:innerWidth,height:innerHeight,active:document.activeElement?.tagName,button:document.querySelector('[data-tool=templates]')?.getBoundingClientRect().toJSON()})"),flush=True)
  w.grab().save('template-picker-failure.png')
 finally:
  w.allow_close=True;w.close();server.stop();app.processEvents();tmp.cleanup();app.quit()
QTimer.singleShot(0,run)
app.exec()
if errors:raise errors[0]
