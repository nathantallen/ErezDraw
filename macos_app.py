"""Native macOS shell for the source deployed in the ErezDraw Docker image."""
from __future__ import annotations
import json
import sys
import tempfile
import threading
from pathlib import Path
import numpy  # Load the array runtime before RDKit.
from PySide6.QtCore import QFile, QObject, QStandardPaths, QTimer, QUrl, Slot, Qt
from PySide6.QtGui import QAction, QDesktopServices, QKeySequence
from PySide6.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineScript
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from werkzeug.serving import make_server
from appearance import Appearance
from web.server import app as web_app

ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))

class LocalServer:
    def __init__(self):
        # Reject other Host headers so a DNS-rebinding page cannot reach the local API.
        web_app.config['TRUSTED_HOSTS'] = ['127.0.0.1']
        self.server = make_server('127.0.0.1', 0, web_app, threaded=True)
        self.url = f'http://127.0.0.1:{self.server.server_port}'
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

class NativePage(QWebEnginePage):
    def __init__(self, profile, origin, parent):
        super().__init__(profile, parent)
        self.origin = origin
    def acceptNavigationRequest(self, url, kind, main):
        if url.toString().startswith(self.origin + '/') or url.scheme() in ('about','blob','data'):
            return True
        if main and url.scheme() in ('https','http'):
            QDesktopServices.openUrl(url)
        return False

class Bridge(QObject):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
    @Slot(str)
    def ready(self, menus):
        self.editor.ready(json.loads(menus))
    @Slot(str)
    def autosave(self, drawing):
        self.editor.persist(drawing)
    @Slot()
    def openDocument(self):
        self.editor.open_document()
    @Slot(str)
    def save(self, drawing):
        self.editor.save_document(drawing)
    @Slot(str)
    def saved(self, drawing):
        self.editor.saved_drawing = drawing
        self.editor.persist(drawing)
    @Slot()
    def printDocument(self):
        self.editor.print_document()

class Editor(QMainWindow):
    def __init__(self, server, storage, report=None):
        super().__init__()
        self.server = server
        self.storage = storage
        self.report = report
        self.path = None
        self.current_drawing = None
        self.saved_drawing = None
        self.loaded = False
        self.allow_close = False
        self.downloads = []
        self.resize(1280,850)
        self.setMinimumSize(720,480)
        self.setWindowTitle('ErezDraw')
        self.profile = QWebEngineProfile(self)
        self.profile.setPersistentStoragePath(str(storage/'browser-data'))
        self.profile.downloadRequested.connect(self.download)
        self.profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
        self.view = QWebEngineView(self)
        self.page = NativePage(self.profile,server.url,self.view)
        self.view.setPage(self.page)
        self.setCentralWidget(self.view)
        self.channel = QWebChannel(self.page)
        self.bridge = Bridge(self)
        self.channel.registerObject('native',self.bridge)
        self.page.setWebChannel(self.channel)
        channel_source = QFile(':/qtwebchannel/qwebchannel.js')
        if not channel_source.open(QFile.OpenModeFlag.ReadOnly):
            raise RuntimeError('Qt WebChannel integration is unavailable.')
        script = QWebEngineScript()
        script.setName('ErezDraw native integration')
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
        script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        script.setRunsOnSubFrames(False)
        script.setSourceCode(bytes(channel_source.readAll()).decode()+'\n'+(ROOT/'macos/native.js').read_text(encoding='utf-8'))
        self.page.scripts().insert(script)
        self.page.loadFinished.connect(self.load_finished)
        QApplication.instance().styleHints().colorSchemeChanged.connect(lambda _:self.sync_appearance())
        self.page.load(QUrl(server.url+'/'))
        if report:
            QTimer.singleShot(60000,lambda:self.finish_test({'status':'failed','error':'Native editor startup timed out'}))
    def js(self, code, callback=None):
        if callback:self.page.runJavaScript(code,callback)
        else:self.page.runJavaScript(code)
    def load_finished(self, ok):
        if not ok:
            if self.report:self.finish_test({'status':'failed','error':'Editor failed to load'})
            else:QMessageBox.critical(self,'ErezDraw','The bundled drawing editor could not start.')
    def ready(self, menus):
        if self.loaded:return
        self.loaded = True
        self.build_menus(menus)
        autosave = self.storage/'autosave.chemjson'
        if autosave.exists() and not self.report:
            try:
                drawing = json.loads(autosave.read_text(encoding='utf-8'))
                self.js('nativeRestore('+json.dumps(drawing)+');')
                self.current_drawing = json.dumps(drawing)
                self.saved_drawing = self.current_drawing
            except (OSError, ValueError):
                QMessageBox.warning(self,'Autosave','The last autosave could not be restored. Open a saved drawing instead.')
        self.sync_appearance()
        if self.report:QTimer.singleShot(500,self.self_test)
    def build_menus(self, menus):
        shortcuts = {'new':QKeySequence.StandardKey.New,'open':QKeySequence.StandardKey.Open,
                     'save':QKeySequence.StandardKey.Save,'print':QKeySequence.StandardKey.Print,
                     'undo':QKeySequence.StandardKey.Undo,'redo':QKeySequence.StandardKey.Redo,
                     'cut':QKeySequence.StandardKey.Cut,'copy':QKeySequence.StandardKey.Copy,
                     'paste':QKeySequence.StandardKey.Paste,'selectAll':QKeySequence.StandardKey.SelectAll}
        self.menuBar().setNativeMenuBar(True)
        for spec in menus:
            menu=self.menuBar().addMenu(spec['label'])
            for item in spec['items']:
                action=QAction(item['label'].split('  ')[0],self)
                key=item['action']
                if key in shortcuts:action.setShortcut(QKeySequence(shortcuts[key]))
                if key=='print':action.triggered.connect(self.print_document)
                elif key=='open':action.triggered.connect(self.open_document)
                else:action.triggered.connect(lambda checked=False,id=item['id']:self.js('nativeCommand('+json.dumps(id)+');'))
                if key=='about':action.setMenuRole(QAction.MenuRole.AboutRole)
                if key=='settings':action.setMenuRole(QAction.MenuRole.PreferencesRole)
                menu.addAction(action)
            if spec['label']=='View':
                self.appearance_menu=menu.addMenu('Appearance')
                for mode in ('System','Light','Dark'):
                    a=self.appearance_menu.addAction(mode)
                    a.triggered.connect(lambda checked=False,mode=mode:self.choose_appearance(mode))
            if spec['label']=='File':
                menu.addSeparator()
                close=menu.addAction('Close')
                close.setShortcut(QKeySequence(QKeySequence.StandardKey.Close))
                close.triggered.connect(self.close)
                quit_action=menu.addAction('Quit ErezDraw')
                quit_action.setMenuRole(QAction.MenuRole.QuitRole)
                quit_action.setShortcut(QKeySequence(QKeySequence.StandardKey.Quit))
                quit_action.triggered.connect(self.close)
    def choose_appearance(self, mode):
        QApplication.instance().appearance.choose(mode)
        self.sync_appearance()
    def sync_appearance(self):
        if not self.loaded:return
        app=QApplication.instance();mode=app.appearance.mode
        dark=mode=='Dark' or (mode=='System' and app.styleHints().colorScheme()==Qt.ColorScheme.Dark)
        self.js('nativeAppearance('+json.dumps(mode)+','+json.dumps(dark)+');')
    def persist(self, value):
        try:
            drawing=json.loads(value)
            if not isinstance(drawing.get('atoms'),list):return
            self.current_drawing=value
            target=self.storage/'autosave.chemjson'
            temporary=target.with_suffix('.tmp')
            temporary.write_text(value,encoding='utf-8');temporary.replace(target)
            self.setWindowTitle((drawing.get('name') or 'Untitled structure')+' — ErezDraw')
        except (ValueError,OSError) as error:
            self.statusBar().showMessage('Autosave failed: '+str(error),5000)
    def open_document(self):
        name,_=QFileDialog.getOpenFileName(self,'Open Drawing',str(Path.home()/'Documents'),'Chemical Drawings (*.chemjson *.json *.mol *.sdf *.cdx *.cdxml *.cdxl);;All Files (*)')
        if not name:return
        path=Path(name)
        try:
            if path.stat().st_size>5_000_000:raise ValueError('File too large (maximum 5 MB).')
            suffix=path.suffix.lower()
            if suffix in ('.cdx','.cdxml','.cdxl'):
                from chemdraw_io import import_chemdraw
                imported=import_chemdraw(path.read_bytes(),path.stem)
                expression='ChemCore.validate('+json.dumps(imported['drawing'])+')'
            elif suffix in ('.mol','.sdf'):
                expression='ChemCore.fromMol('+json.dumps(path.read_text(encoding='utf-8-sig'))+')'
            else:expression='ChemCore.validate('+json.dumps(json.loads(path.read_text(encoding='utf-8-sig')))+')'
        except (OSError,ValueError) as error:
            QMessageBox.warning(self,'Open Failed',str(error));return
        code="""(()=>{try{const next=%s;finishEditing();if((doc.atoms.length||doc.annotations.length)&&!confirm('Replace the current drawing? You can Undo to restore it.'))return '';replaceDoc(next);dirty=false;return JSON.stringify(doc)}catch(error){notify('Could not open drawing: '+error.message);return ''}})()""" % expression
        def opened(value):
            if value:
                self.path=path if suffix in ('.chemjson','.json') else None
                self.saved_drawing=value
                self.persist(value)
        self.js(code,opened)
    def save_document(self,value):
        drawing=json.loads(value)
        suggested=str(self.path or Path.home()/'Documents'/(drawing.get('name','Untitled structure')+'.chemjson'))
        name,_=QFileDialog.getSaveFileName(self,'Save Drawing',suggested,'ErezDraw Drawing (*.chemjson)')
        if not name:return False
        path=Path(name)
        if path.suffix.lower()!='.chemjson':path=path.with_suffix('.chemjson')
        drawing['name']=path.stem
        try:path.write_text(json.dumps(drawing,indent=2)+'\n')
        except OSError as error:
            QMessageBox.warning(self,'Save Failed',str(error));return False
        self.path=path
        self.persist(json.dumps(drawing,separators=(',',':')))
        self.js('nativeSaveComplete('+json.dumps(path.stem)+');')
        return True
    def download(self,request):
        name,_=QFileDialog.getSaveFileName(self,'Export File',str(Path.home()/'Documents'/request.suggestedFileName()))
        if not name:request.cancel();return
        path=Path(name)
        request.setDownloadDirectory(str(path.parent));request.setDownloadFileName(path.name)
        self.downloads.append(request)
        request.isFinishedChanged.connect(lambda:self.downloads.remove(request) if request.isFinished() and request in self.downloads else None)
        request.accept()
    def print_document(self):
        self.printer=QPrinter(QPrinter.PrinterMode.HighResolution)
        if QPrintDialog(self.printer,self).exec():
            self.js("document.body.classList.add('native-print')")
            self.view.printFinished.connect(self.print_finished)
            self.view.print(self.printer)
    def print_finished(self,ok):
        self.js("document.body.classList.remove('native-print')")
        self.view.printFinished.disconnect(self.print_finished)
        if not ok:QMessageBox.warning(self,'Print','The drawing could not be printed.')
    def closeEvent(self,event):
        if self.allow_close or not self.loaded or self.report:event.accept();return
        event.ignore()
        self.js('finishEditing();JSON.stringify(doc)',self.confirm_close)
    def confirm_close(self,value):
        if value and (self.saved_drawing is None or json.loads(value)!=json.loads(self.saved_drawing)):
            doc=json.loads(value)
            if doc.get('atoms') or doc.get('annotations'):
                answer=QMessageBox.question(self,'Save Drawing','Save this drawing before closing?',QMessageBox.StandardButton.Save|QMessageBox.StandardButton.Discard|QMessageBox.StandardButton.Cancel)
                if answer==QMessageBox.StandardButton.Cancel:return
                if answer==QMessageBox.StandardButton.Save:
                    if not self.save_document(value):return
                    value=None
        if value:self.persist(value)
        self.allow_close=True;self.close()
    def self_test(self):
        code="""(()=>{const before=doc;try{
          doc=ChemCore.blank();doc.atoms=[{id:'m',label:'La',charge:0,x:0,y:0}];doc.bonds=[];
          for(let i=0;i<3;i++){doc.atoms.push({id:'n'+i,label:'N',charge:0,x:40,y:i*40},{id:'s'+i,label:'Si',charge:0,x:80,y:i*40},{id:'t'+i,label:'Si',charge:0,x:80,y:i*40+20});doc.bonds.push({id:'m'+i,a:'n'+i,b:'m',order:1,style:'coord'},{id:'s'+i,a:'n'+i,b:'s'+i,order:1,style:'normal'},{id:'t'+i,a:'n'+i,b:'t'+i,order:1,style:'normal'});}
          updateBondCharges();return JSON.stringify({charge:doc.atoms[0].charge,acs:ChemCore.blank().drawingSettings.bondLength,hover:typeof hoverGraphic==='function',native:!!window.ErezNative,web:!!window.ErezWeb,menus:document.querySelectorAll('[data-native-command]').length,palette:document.querySelectorAll('.web-family').length});
        }finally{doc=before;}})()"""
        def checked(value):
            try:
                result=json.loads(value)
                assert result['charge']==3 and result['acs']==19.2 and result['hover'] and result['native'] and result['web'] and result['menus']>60 and result['palette']>=30,result
                from startup_check import check_runtime
                result.update(check_runtime(ROOT));result['source_image']=json.loads((ROOT/'macos-source.json').read_text())['image']
                self.finish_test(result)
            except Exception as error:self.finish_test({'status':'failed','error':str(error)})
        self.js(code,checked)
    def finish_test(self,result):
        if not self.report:return
        path=self.report;self.report=None
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(result,indent=2)+'\n')
        self.allow_close=True
        QApplication.instance().exit(0 if result.get('status')=='passed' else 1)

def main():
    app=QApplication(sys.argv)
    app.setApplicationName('ErezDraw');app.setOrganizationName('ErezDraw')
    app.appearance=Appearance(app)
    report=Path(sys.argv[sys.argv.index('--self-test')+1]) if '--self-test' in sys.argv else None
    temporary=tempfile.TemporaryDirectory(prefix='erezdraw-native-check-') if report else None
    storage=Path(temporary.name) if temporary else Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation))/'docker-native'
    storage.mkdir(parents=True,exist_ok=True)
    server=LocalServer()
    editor=Editor(server,storage,report);editor.show()
    result=app.exec()
    # Destroy the page before its WebEngine profile.
    from shiboken6 import delete
    delete(editor.view)
    delete(editor.profile)
    server.stop()
    if temporary:temporary.cleanup()
    return result
if __name__=='__main__':sys.exit(main())
