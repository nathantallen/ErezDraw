"""Route canvas commands to the native shell and clipboard, including WebEngine overrides."""
import json
from PySide6.QtCore import QObject, Slot, QEvent, QFile, QIODevice
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEnginePage

class DesktopCommands(QObject):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor=editor
    @Slot(str)
    def dispatch(self, name):
        editor=self.editor
        if not editor.ready:return
        if name in ('copy','cut','paste','selectAll'):
            # Ordinary HTML fields keep the browser's text editing behavior.
            def route(field):
                if field:
                    editor.page.triggerAction({'copy':QWebEnginePage.WebAction.Copy,'cut':QWebEnginePage.WebAction.Cut,'paste':QWebEnginePage.WebAction.Paste,'selectAll':QWebEnginePage.WebAction.SelectAll}[name])
                elif name=='selectAll':editor.actions['selectAll'].trigger()
                elif name=='paste':editor.clipboard_paste()
                else:editor.clipboard_copy(name=='cut')
            editor.js("(()=>{const a=document.activeElement;return !!(a&&(a!==document.getElementById('textEditor')||"+("true" if name=="selectAll" else "false")+")&&(a.isContentEditable||['INPUT','TEXTAREA'].includes(a.tagName)))})()",route)
            return
        # Menu enable/check states refresh periodically; canvas state is authoritative.
        if name in ('undo','redo'):
            editor.command(name);return
        local={'group','ungroup','flip','flipVertical','bold','italic','underline','plain','formula','subscript','superscript','textLeft','textCenter','textRight','textJustify'}
        if name in local or name.startswith('align_'):
            editor.js('keyboardCommand('+json.dumps(name)+',true);');return
        if name=='rotate':editor.rotate_selection();return
        if name=='scaleObjects':editor.scale_objects();return
        action=editor.actions.get(name)
        if action and action.isEnabled():action.trigger()

class ClipboardKeys(QObject):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor=editor
    def follow_focus(self, previous, current):
        if current is not None and (current is self.editor.view or self.editor.view.isAncestorOf(current)):
            current.installEventFilter(self)
    def eventFilter(self, watched, event):
        editor=self.editor
        if not editor.ready or event.type() not in (QEvent.Type.ShortcutOverride,QEvent.Type.KeyPress):return False
        focus=QApplication.focusWidget()
        if focus is None or (focus is not editor.view and not editor.view.isAncestorOf(focus)):return False
        for name, key in (('copy',QKeySequence.StandardKey.Copy),('cut',QKeySequence.StandardKey.Cut),('paste',QKeySequence.StandardKey.Paste),('selectAll',QKeySequence.StandardKey.SelectAll)):
            if event.matches(key):
                event.accept()
                if event.type()==QEvent.Type.KeyPress:editor.desktop_commands.dispatch(name)
                return True
        return False

def install(editor):
    editor.desktop_commands=DesktopCommands(editor)
    editor.desktop_channel=QWebChannel(editor.page)
    editor.desktop_channel.registerObject('desktop',editor.desktop_commands)
    editor.page.setWebChannel(editor.desktop_channel)
    editor.clipboard_keys=ClipboardKeys(editor)
    editor.view.installEventFilter(editor.clipboard_keys)
    for child in editor.view.findChildren(QWidget):child.installEventFilter(editor.clipboard_keys)
    QApplication.instance().focusChanged.connect(editor.clipboard_keys.follow_focus)

def initialize_page(editor):
    source=QFile(':/qtwebchannel/qwebchannel.js')
    if not source.open(QIODevice.OpenModeFlag.ReadOnly):raise RuntimeError('Qt WebChannel script is missing.')
    code=bytes(source.readAll()).decode('utf-8');source.close()
    keys=json.dumps(list(editor.actions))
    code+='\nnew QWebChannel(qt.webChannelTransport,channel=>{const keys='+keys+";window.ErezDesktop={dispatch:name=>{const aliases={rotateDialog:'rotate',close:'closeDocument',repeat:'repeatKeyboard'};const key=aliases[name]||name;if(!keys.includes(key))return false;channel.objects.desktop.dispatch(key);return true;}};});"
    editor.page.runJavaScript(code)
