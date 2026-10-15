"""Real Qt key presses through WebEngine: system clipboard and native command routing."""
import os,time,json
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS','--no-sandbox --disable-gpu')
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt,QEventLoop,QTimer,QPoint
from PySide6.QtTest import QTest
from main import Editor
app=QApplication([]);w=Editor();w.show();w.activateWindow()
def wait(fn,seconds=20):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        app.processEvents();QTest.qWait(15)
        if fn():return
    raise AssertionError('Timed out')
def js(code):
    result=[];w.page.runJavaScript(code,lambda value:result.append(value));wait(lambda:bool(result));return result[0]
def keys(key, modifiers=Qt.KeyboardModifier.ControlModifier):
    target=w.view.focusProxy() or w.view
    target.setFocus();QTest.keyClick(target,key,modifiers);app.processEvents()
assert not w.windowIcon().isNull()
assert len(w.windowIcon().availableSizes())>=7
wait(lambda:w.ready)
wait(lambda:js('!!window.ErezDesktop'))
js("finishEditing();doc=ChemCore.blank();let a=addAtom({x:200,y:200}),b=addAtom({x:240,y:200});addBond(a,b);selection=new Set([a.id,b.id]);annSelection.clear();tool='select';render();canvas.focus();")
counts=[];copy=w.clipboard_copy
w.clipboard_copy=lambda cut=False:(counts.append('cut' if cut else 'copy'),copy(cut))[-1]
app.clipboard().setText('old clipboard')
keys(Qt.Key.Key_C)
wait(lambda:app.clipboard().mimeData().hasFormat('application/x-chemsketch-fragment'))
assert counts==['copy'],counts
assert app.clipboard().mimeData().hasFormat('image/png')
assert app.clipboard().mimeData().hasFormat('image/svg+xml')
keys(Qt.Key.Key_V);wait(lambda:js('doc.atoms.length')==4)
keys(Qt.Key.Key_X);wait(lambda:js('doc.atoms.length')==2)
assert counts==['copy','cut'],counts
# A normal field in a web dialog must use the browser text clipboard, not copy structures.
js("$('settingsDialog').showModal();$('docName').value='Native field text';$('docName').focus();$('docName').select();")
js("$('docName').setSelectionRange(5,5)");keys(Qt.Key.Key_A);wait(lambda:js("$('docName').selectionStart===0&&$('docName').selectionEnd===17"))
keys(Qt.Key.Key_C);wait(lambda:app.clipboard().text()=='Native field text')
assert counts==['copy','cut'],counts
keys(Qt.Key.Key_X);wait(lambda:js("$('docName').value")=="")
keys(Qt.Key.Key_V);wait(lambda:js("$('docName').value")=='Native field text')
js("$('settingsDialog').close();canvas.focus()")
# Select All and Copy in a rich atom label must remain text operations.
js("edit(doc.atoms[0],'atom');$('textEditor').textContent='NMe2';$('textEditor').focus()")
keys(Qt.Key.Key_A);wait(lambda:js('window.getSelection().toString()')=='NMe2')
keys(Qt.Key.Key_C);wait(lambda:app.clipboard().text()=='NMe2')
assert counts==['copy','cut','copy'],counts
js("finishEditing(true);selection=new Set(doc.atoms.map(a=>a.id));annSelection.clear();undoStack=[];redoStack=[];tool='select';render();canvas.focus()")
wait(lambda:w.actions['flip'].isEnabled())
keys(Qt.Key.Key_H,Qt.KeyboardModifier.ControlModifier|Qt.KeyboardModifier.ShiftModifier)
wait(lambda:js('undoStack.length')==1)
QTest.qWait(150);assert js('undoStack.length')==1
keys(Qt.Key.Key_Y);wait(lambda:js('undoStack.length')==2)
QTest.qWait(150);assert js('undoStack.length')==2
# The JS route must reach native Save As, rather than browser download.
seen=[];w.actions['saveas'].triggered.disconnect();w.actions['saveas'].triggered.connect(lambda:seen.append('saveas'))
assert js("handleChemDrawKey({key:'S',ctrlKey:true,shiftKey:true,target:canvas})") is True
wait(lambda:seen==['saveas'])
assert js("window.ErezDesktop.dispatch('not-a-command')") is False
# Actual Qt mouse events must duplicate selected structures and leave originals still.
js("doc=ChemCore.blank();const ma=addAtom({x:360,y:300}),mb=addAtom({x:400,y:300});addBond(ma,mb);selection=new Set([ma.id,mb.id]);annSelection.clear();tool='select';undoStack=[];redoStack=[];center={x:500,y:350};zoomTo(1);render();canvas.focus()")
original=json.loads(js('JSON.stringify(doc)'))
def screen(x,y):
    p=json.loads(js(f"(()=>{{const p=new DOMPoint({x},{y}).matrixTransform(canvas.getScreenCTM());return JSON.stringify([p.x,p.y])}})()"))
    return QPoint(round(p[0]),round(p[1]))
target=w.view.focusProxy() or w.view
start,end=screen(360,300),screen(480,380)
QTest.mouseMove(target,start);QTest.mousePress(target,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.ControlModifier,start)
wait(lambda:js("gesture?.kind==='move'&&gesture.copyDrag"))
QTest.mouseMove(target,end,100);wait(lambda:js('doc.atoms.length')==4)
assert json.loads(js('JSON.stringify(doc.atoms.slice(0,2))'))==original['atoms']
assert js('undoStack.length')==0
QTest.mouseRelease(target,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.ControlModifier,end)
wait(lambda:js('undoStack.length')==1)
js("action('undo')");assert json.loads(js('JSON.stringify(doc)'))==original
print('PASS: real Ctrl+C/X/V through WebEngine, SVG/PNG/system/fragment clipboard, one dispatch, text fields and rich labels protected, single flip/repeat dispatch, native Save As bridge, real Ctrl-drag preview/commit/undo.')
app.clipboard().clear();w.allow_close=True;w.close();app.processEvents()
