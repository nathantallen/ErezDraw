"""Windows desktop shell with native Qt controls and the local drawing engine."""
from __future__ import annotations
import json
import sys
from pathlib import Path
# Load the native array runtime first: RDKit can otherwise suppress the initial
# NumPy import failure and a later import reports only a misleading reload error.
import numpy
from PySide6.QtCore import Qt, QTimer, QUrl, QSize, QStandardPaths, QByteArray, QMimeData
from PySide6.QtGui import QAction, QKeySequence, QIcon, QPixmap, QPainter, QColor
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (QApplication, QMainWindow, QToolBar, QDockWidget, QWidget,
    QGridLayout, QToolButton, QLineEdit, QComboBox, QLabel, QFileDialog, QMessageBox,
    QDialog, QFormLayout, QDialogButtonBox, QCheckBox, QTextEdit, QVBoxLayout, QDoubleSpinBox, QRadioButton, QButtonGroup, QHBoxLayout, QScrollBar)
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtPrintSupport import QPrinter, QPrintDialog

ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
APP_NAME = 'ErezDraw'


from classic_icons import tool_icon


class LocalPage(QWebEnginePage):
    """The editor is offline; prevent navigation away from its bundled file."""
    def acceptNavigationRequest(self, url, navigation_type, is_main_frame):
        return url.scheme() in ('file', 'qrc', 'about', 'data', 'blob')


from structure_ui import StructureActions
from view_ui import ViewPanels
from graphics_ui import GraphicsActions
from mass_ui import MassActions

class Editor(StructureActions,ViewPanels,GraphicsActions,MassActions,QMainWindow):
    def __init__(self):
        super().__init__()
        app = QApplication.instance()
        if not hasattr(app, 'appearance'):
            from appearance import Appearance
            app.appearance = Appearance(app)
        self.resize(1200, 800)
        self.setMinimumSize(650, 450)
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(tool_icon('benzene'))
        self.path: Path | None = None
        self.saved_doc = None
        self.is_dirty = False
        self.ready = False
        self.allow_close = False
        self.tool_buttons = {}
        self.actions = {}
        self.active_downloads = []
        storage = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation))
        storage.mkdir(parents=True, exist_ok=True)
        self.profile = QWebEngineProfile('ErezDraw', self)
        self.profile.setPersistentStoragePath(str(storage / 'browser-data'))
        self.profile.setCachePath(str(storage / 'cache'))
        self.profile.downloadRequested.connect(self.download_requested)
        self.view = QWebEngineView(self)
        self.page = LocalPage(self.profile, self.view)
        self.view.setPage(self.page)
        self.page.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, False)
        self.page.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, False)
        self.setCentralWidget(self.view)
        self.build_controls()
        QApplication.instance().appearance.install_menu(self.menus['View'])
        if sys.platform=='darwin':
            self.menuBar().setNativeMenuBar(True)
            self.actions['about'].setMenuRole(QAction.MenuRole.AboutRole)
            if 'settings' in self.actions:self.actions['settings'].setMenuRole(QAction.MenuRole.PreferencesRole)
        self.view.loadFinished.connect(self.loaded)
        self.page.load(QUrl.fromLocalFile(str(ROOT / 'assets' / 'editor.html')))
        self.timer = QTimer(self)
        self.timer.setInterval(400)
        self.timer.timeout.connect(self.refresh)
        self.statusBar().showMessage('Loading drawing engine…')
        self.set_controls_enabled(False)

    def js(self, code, callback=None):
        if self.ready:
            if callback is None:
                self.page.runJavaScript(code)
            else:
                self.page.runJavaScript(code, callback)

    def command(self, name):
        self.js('action(' + json.dumps(name) + ');')

    def add_action(self, menu, key, label, callback, shortcut=None):
        a = QAction(label, self)
        if shortcut:
            a.setShortcut(QKeySequence(shortcut))
        a.triggered.connect(lambda checked=False: callback())
        menu.addAction(a)
        self.actions[key] = a
        return a

    def build_controls(self):
        bar = self.menuBar()
        self.menus = {}
        file = bar.addMenu('&File')
        self.menus['File'] = file
        self.add_action(file, 'new', '&New', self.new_document, 'Ctrl+N')
        self.add_action(file, 'open', '&Open…', self.open_document, 'Ctrl+O')
        self.add_action(file, 'save', '&Save', self.save_document, 'Ctrl+S')
        self.add_action(file, 'saveas', 'Save &As…', lambda: self.save_document(force_dialog=True), 'Ctrl+Shift+S')
        file.addSeparator()
        for ext in ('svg', 'png', 'mol'):
            self.add_action(file, ext, f'Export {ext.upper()}…', lambda ext=ext: self.command(ext))
        file.addSeparator()
        self.add_action(file, 'settings', 'Document Settings…', self.settings)
        self.add_action(file, 'print', '&Print…', self.print_document, 'Ctrl+P')
        file.addSeparator()
        self.add_action(file, 'exit', 'E&xit', self.close, 'Alt+F4')
        edit = bar.addMenu('&Edit')
        self.menus['Edit'] = edit
        for key, label, shortcut in [('undo','&Undo','Ctrl+Z'),('redo','&Redo','Ctrl+Y'),('cut','Cu&t','Ctrl+X'),('copy','&Copy','Ctrl+C'),('paste','&Paste','Ctrl+V'),('selectAll','Select &All','Ctrl+A'),('delete','&Delete','Delete')]:
            self.add_action(edit, key, label, lambda key=key: self.clipboard_copy(key=='cut') if key in ('copy','cut') else self.clipboard_paste() if key=='paste' else self.command(key), shortcut)
        view = bar.addMenu('&View')
        self.menus['View'] = view
        self.add_action(view, 'fit', '&Fit Drawing', lambda: self.command('fit'), 'Home')
        self.add_action(view, 'actual', '&Actual Size', lambda: self.command('actual'))
        self.add_action(view, 'grid', 'Toggle &Grid', lambda: self.command('grid'))
        self.actions['grid'].setCheckable(True)
        obj = bar.addMenu('&Object')
        self.menus['Object'] = obj
        for key,label in [('fixedLengths','Fixed Lengths'),('fixedAngles','Fixed Angles')]:
            a=QAction(label,self);a.setCheckable(True);a.setChecked(True);a.toggled.connect(lambda checked,key=key:self.js(key+'='+json.dumps(checked)+';'));obj.addAction(a);self.actions[key]=a
        obj.addSeparator()
        self.add_action(obj, 'group', 'Group', lambda:self.js('groupSelection();'), 'Ctrl+G')
        self.add_action(obj, 'ungroup', 'Ungroup', lambda:self.js('ungroupSelection();'), 'Ctrl+Shift+G')
        self.add_action(obj, 'integral', 'Make Group Integral', lambda:self.js('integralSelection();'))
        obj.addSeparator()
        self.add_action(obj, 'flatten', 'Flatten', lambda:self.command('flatten'))
        self.add_action(obj, 'rotate', 'Rotate…', self.rotate_selection)
        self.add_action(edit, 'repeatRotate', 'Repeat Rotate', lambda:self.js('rotateSelection(lastRotation);'))
        self.add_action(obj, 'flip', 'Flip Horizontally', lambda: self.command('flip'))
        self.add_action(obj, 'flipVertical', 'Flip Vertically', lambda: self.js('flipSelection(true);'))
        self.add_action(obj, 'scaleObjects', 'Scale Objects…', self.scale_objects)
        self.add_action(obj, 'centerPage', 'Center on Page', lambda: self.js('centerSelection();'))
        align = obj.addMenu('Align')
        for mode,label in [('left','Left'),('horizontal','Horizontal Centers'),('right','Right'),('top','Top'),('vertical','Vertical Centers'),('bottom','Bottom')]:
            self.add_action(align, 'align_'+mode, label, lambda mode=mode:self.js('objectAlign('+json.dumps(mode)+');'))
        distribute = obj.addMenu('Distribute')
        for axis,label in [('x','Horizontally'),('y','Vertically')]:
            self.add_action(distribute, 'distribute_'+axis, label, lambda axis=axis:self.js('objectDistribute('+json.dumps(axis)+');'))
        structure = bar.addMenu('&Structure')
        self.menus['Structure'] = structure
        self.add_action(structure, 'validate', 'Check Structure…', self.validate_chemistry, 'Ctrl+Shift+V')
        self.add_action(structure, 'cleanup', 'Clean Up Structure…', self.cleanup_structure, 'Ctrl+Shift+K')
        structure.addSeparator()
        self.add_action(structure, 'label', 'Edit Atom Label…', self.edit_atom_label)
        self.add_action(structure, 'moleculeLabel', 'Label Molecule (Name and MW)…', self.molecule_label)
        for key,label in [('addH','Add Explicit Hydrogens'),('removeH','Remove Explicit Hydrogens'),('expand','Expand Label')]:
            self.add_action(structure,key,label,lambda key=key:self.structure_transform(key))
        self.add_action(structure,'contract','Contract Label…',self.contract_label)
        self.add_action(structure,'nameToStructure','Convert Name to Structure…',self.name_to_structure)
        self.add_action(structure,'structureToName','Convert Structure to Name…',self.molecule_label)
        self.add_action(structure,'nmrH','Predict ¹H-NMR Shifts…',lambda:self.predict_nmr('1H'))
        self.add_action(structure,'massFragmentation','Mass Spectrometry Fragmentation…',self.mass_fragmentation)
        self.add_action(structure,'nmrC','Predict ¹³C-NMR Shifts…',lambda:self.predict_nmr('13C'))
        self.add_action(structure,'atomProperties','Atom Properties…',self.atom_properties)
        self.add_action(structure,'bondProperties','Bond Properties…',self.bond_properties)
        text = bar.addMenu('&Text')
        self.menus['Text'] = text
        self.add_action(text, 'caption', 'Caption Tool', lambda: self.set_tool('text'))
        help_menu = bar.addMenu('&Help')
        self.menus['Help'] = help_menu
        self.add_action(help_menu, 'help', 'Drawing Guide', lambda: self.command('help'))
        self.add_action(help_menu, 'demo', 'Load Example Reaction', lambda: self.command('demo'))
        self.add_action(help_menu, 'about', 'About ErezDraw', self.about)
        toolbar = QToolBar('General', self)
        toolbar.setObjectName('GeneralToolbar')
        toolbar.setIconSize(QSize(20,20))
        self.addToolBar(toolbar)
        standards = {'new': 'SP_FileIcon', 'open': 'SP_DialogOpenButton', 'save': 'SP_DialogSaveButton'}
        from PySide6.QtWidgets import QStyle
        for key in ('new', 'open', 'save', 'undo', 'redo'):
            if key in standards:
                self.actions[key].setIcon(self.style().standardIcon(getattr(QStyle.StandardPixmap, standards[key])))
            toolbar.addAction(self.actions[key])
        toolbar.addSeparator()
        toolbar.addAction(self.actions['validate'])
        toolbar.addAction(self.actions['cleanup'])
        toolbar.addSeparator()
        toolbar.addAction(self.actions['fit'])
        toolbar.addWidget(QLabel('  Zoom  '))
        self.zoom_combo = QComboBox()
        self.zoom_combo.addItems(['50%', '75%', '100%', '125%', '150%', '200%', '300%'])
        self.zoom_combo.setCurrentText('100%')
        self.zoom_combo.currentTextChanged.connect(lambda value: self.js(f'zoomTo({int(value[:-1])/100});'))
        toolbar.addWidget(self.zoom_combo)
        toolbar.addSeparator()
        toolbar.addWidget(QLabel(' Atom  '))
        self.atom_input = QLineEdit('C')
        self.atom_input.setMaximumWidth(100)
        self.atom_input.setMaxLength(40)
        self.atom_input.setToolTip('Element or arbitrary atom label, e.g. Y, La, HMDS')
        self.atom_input.returnPressed.connect(self.use_atom)
        toolbar.addWidget(self.atom_input)
        apply = QAction('Label Tool', self)
        apply.triggered.connect(self.use_atom)
        toolbar.addAction(apply)
        self.dock = QDockWidget('Main Tools', self)
        self.dock.setObjectName('MainTools')
        self.dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        tools = QWidget()
        layout = QGridLayout(tools)
        layout.setContentsMargins(5,5,5,5)
        layout.setSpacing(2)
        entries = [('lasso','Lasso'),('select','Marquee'),('erase','Eraser'),('single','Single Bond'),('double','Double Bond'),('triple','Triple Bond'),('wedge','Solid Wedge'),('hash','Hashed Wedge'),('coord','Coordination Bond'),('atom','Atom Label'),('text','Caption'),('arrow','Reaction Arrow'),('benzene','Benzene')] + [(f'ring{n}',f'{n}-Membered Ring') for n in range(3,9)]
        for i, (key, label) in enumerate(entries):
            button = QToolButton()
            button.setIcon(tool_icon(key))
            button.setIconSize(QSize(25,25))
            button.setFixedSize(33,33)
            button.setCheckable(True)
            button.setToolTip(label)
            button.clicked.connect(lambda checked=False, key=key: self.set_tool(key))
            layout.addWidget(button, i//2, i%2)
            self.tool_buttons[key] = button
        layout.setRowStretch((len(entries)+1)//2,1)
        self.dock.setWidget(tools)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock)
        view.addAction(self.dock.toggleViewAction())
        view.addAction(toolbar.toggleViewAction())
        from classic_ui import install
        install(self, toolbar, tool_icon)
        self.install_view_panels()
        self.install_ligand_panel()
        self.count_label = QLabel('0 atoms · 0 bonds')
        self.statusBar().addPermanentWidget(self.count_label)

    def set_controls_enabled(self, enabled):
        for a in self.actions.values():
            if a is not self.actions.get('exit'):
                a.setEnabled(enabled and a not in self.unavailable_actions)
        for key,b in self.tool_buttons.items():
            b.setEnabled(enabled and not key.startswith('missing:'))
        self.atom_input.setEnabled(enabled)
        self.zoom_combo.setEnabled(enabled)

    def loaded(self, ok):
        self.ready = ok
        self.set_controls_enabled(ok)
        if not ok:
            QMessageBox.critical(self, APP_NAME, 'The bundled drawing engine could not be loaded.')
            return
        self.js('JSON.stringify(doc)', self.initial_document)
        self.timer.start()
        self.refresh()

    def initial_document(self, value):
        self.saved_doc = value
        if len(sys.argv)>1 and Path(sys.argv[1]).is_file():
            self.load_path(Path(sys.argv[1]))

    def refresh(self):
        if not self.ready:
            return
        self.js("JSON.stringify({drawing:doc,tool,undo:undoStack.length,redo:redoStack.length,selection:selection.size+annSelection.size,units:selectedUnits().length,textStyle:activeTextStyle(),rotateRequest:nativeRotateRequest,scaleRequest:nativeScaleRequest,graphicRequest:nativeGraphicRequest,status:$('status').textContent,grid,zoom})", self.receive_state)

    def receive_state(self, value):
        if not value:
            return
        try:
            state = json.loads(value)
        except (ValueError, TypeError):
            return
        if state.get('graphicRequest'):
            self.js('nativeGraphicRequest=null;')
            QTimer.singleShot(0,lambda key=state['graphicRequest']:self.edit_table(key))
        if state.get('rotateRequest'):
            self.js('nativeRotateRequest=false;')
            QTimer.singleShot(0,self.rotate_selection)
        if state.get('scaleRequest'):
            self.js('nativeScaleRequest=false;')
            QTimer.singleShot(0,self.scale_objects)
        self.current_doc = state['drawing']
        # Compare canonical JSON so undoing back to the saved document clears the dirty flag.
        saved = json.loads(self.saved_doc) if self.saved_doc else None
        self.is_dirty = saved is not None and self.current_doc != saved
        name = self.path.name if self.path else self.current_doc['name']
        self.setWindowTitle(f"{'* ' if self.is_dirty else ''}{name} — {APP_NAME}")
        self.count_label.setText(f"{sum(a.get('nodeType')!='centroid' for a in self.current_doc['atoms'])} atoms · {len(self.current_doc['bonds'])} bonds")
        self.statusBar().showMessage(state['status'])
        self.document_action.setText(name)
        self.zoom_combo.blockSignals(True);self.zoom_combo.setCurrentText(f"{state['zoom']*100:.0f}%");self.zoom_combo.blockSignals(False)
        self.actions['grid'].setChecked(state.get('grid',False))
        for key in ['copy','cut','delete','rotate','scaleObjects','flip','flipVertical','centerPage','group','ungroup','integral','flatten']:
            self.actions[key].setEnabled(bool(state['selection']))
        for key in ['left','horizontal','right','top','vertical','bottom']:
            self.actions['align_'+key].setEnabled(state['units']>=2)
        for axis in ['x','y']:
            self.actions['distribute_'+axis].setEnabled(state['units']>=3)
        self.font_combo.blockSignals(True);self.font_combo.setCurrentFont(__import__('PySide6.QtGui',fromlist=['QFont']).QFont(state['textStyle'].get('font','Arial')));self.font_combo.blockSignals(False)
        self.text_size_combo.blockSignals(True);self.text_size_combo.setCurrentText(f"{state['textStyle'].get('size',18)/1.5:g}");self.text_size_combo.blockSignals(False)
        for key in ['bold','italic','underline']:
            self.actions[key].setChecked(bool(state['textStyle'].get(key)))
        self.actions['undo'].setEnabled(bool(state['undo']))
        self.actions['redo'].setEnabled(bool(state['redo']))
        for key, button in self.tool_buttons.items():
            button.setChecked(key == state['tool'] or self.family_buttons.get(key) == state['tool'])

    def set_tool(self, key):
        self.js('setTool(' + json.dumps(key) + ');')
        self.view.setFocus()

    def use_atom(self):
        label = self.atom_input.text().strip() or 'C'
        self.js('element='+json.dumps(label)+";$('elementInput').value=element;setTool('atom');")
        self.view.setFocus()

    def edit_atom_label(self):
        from PySide6.QtWidgets import QInputDialog
        def show(value):
            if not value:
                QMessageBox.information(self, APP_NAME, 'Select one atom first.')
                return
            label, ok = QInputDialog.getText(self, 'Atom Label', 'Element or label:', text=value)
            if ok and label.strip():
                self.js('changeLabel('+json.dumps(label[:40])+');')
        self.js("selection.size===1?ChemCore.atom(doc,[...selection][0]).label:''", show)

    def settings(self):
        def show(value):
            if not value:
                return
            state = json.loads(value)
            dialog = QDialog(self)
            dialog.setWindowTitle('Document Settings')
            form = QFormLayout(dialog)
            name = QLineEdit(state['name']); name.setMaxLength(100)
            length = QDoubleSpinBox(); length.setRange(1,1000); length.setDecimals(2); length.setValue(float(state['length']))
            form.addRow('Document name',name)
            form.addRow('New bond length (px)',length)
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            buttons.accepted.connect(dialog.accept); buttons.rejected.connect(dialog.reject); form.addRow(buttons)
            if dialog.exec():
                self.js('(()=>{const before=snapshot();doc.name='+json.dumps(name.text().strip() or 'Untitled structure')+";$('docName').value=doc.name;$('bondLength').value="+json.dumps(str(length.value()))+';if(doc.drawingSettings)doc.drawingSettings.bondLength='+str(length.value())+';commit(before);render();})();')
        self.js("JSON.stringify({name:doc.name,length:L()})",show)

    def scale_objects(self):
        def show(value):
            info=json.loads(value)
            if not info['count']:
                self.statusBar().showMessage('Select objects to scale.');return
            dialog=QDialog(self);dialog.setWindowTitle('Scale Objects');form=QFormLayout(dialog)
            fixed=QRadioButton('Scale to fixed bond length ('+str(info['fixed'])+' px)')
            median=QRadioButton('Scale to median bond length:')
            percent=QRadioButton('Scale by:');percent.setChecked(True)
            group=QButtonGroup(dialog)
            for radio in [fixed,median,percent]:group.addButton(radio)
            bond=QDoubleSpinBox();bond.setRange(1,1000);bond.setValue(info['median'] or info['fixed']);bond.setSuffix(' px')
            amount=QDoubleSpinBox();amount.setRange(1,10000);amount.setValue(100);amount.setSuffix(' %')
            labels=QCheckBox('Scale Atom Labels');labels.setChecked(False)
            fixed.setEnabled(info['median']>0);median.setEnabled(info['median']>0)
            form.addRow(fixed);form.addRow(median,bond);form.addRow(percent,amount);form.addRow(labels)
            buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);buttons.button(QDialogButtonBox.StandardButton.Ok).setText('Scale');buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject);form.addRow(buttons)
            if dialog.exec():
                factor=100*(info['fixed'] if fixed.isChecked() else bond.value())/info['median'] if not percent.isChecked() else amount.value()
                self.js('scaleSelection('+json.dumps(factor)+','+json.dumps(labels.isChecked())+');')
        self.js("JSON.stringify({count:selection.size+annSelection.size,median:medianSelectedBond(),fixed:L()})",show)

    def rotate_selection(self):
        def show(count):
            if not count:
                self.statusBar().showMessage('Select objects to rotate.');return
            dialog=QDialog(self);dialog.setWindowTitle('Rotate Objects');form=QFormLayout(dialog)
            degrees=QDoubleSpinBox();degrees.setRange(0,3600);degrees.setDecimals(2);degrees.setValue(30);degrees.setFixedWidth(95)
            cw=QRadioButton('degrees CW');ccw=QRadioButton('degrees CCW');cw.setChecked(True)
            group=QButtonGroup(dialog);group.addButton(cw);group.addButton(ccw)
            direction=QWidget();row=QHBoxLayout(direction);row.setContentsMargins(0,0,0,0);row.addWidget(cw);row.addWidget(ccw)
            form.addRow(degrees,direction)
            labels=QCheckBox('Rotate Atom Labels');form.addRow(labels)
            buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);buttons.button(QDialogButtonBox.StandardButton.Ok).setText('Rotate');buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject);form.addRow(buttons)
            if dialog.exec():
                angle=degrees.value()*(1 if cw.isChecked() else -1)
                self.js('rotateSelection('+str(angle)+','+json.dumps(labels.isChecked())+');')
        self.js('selection.size+annSelection.size',show)

    def validate_chemistry(self):
        def checked(value):
            if not value:return
            try:
                from chemistry import validate
                report=validate(json.loads(value))
            except Exception as e:
                QMessageBox.warning(self,'Validation Failed',str(e));return
            ids=list({key for issue in report['issues'] if issue['severity']=='warning' for key in issue['atom_ids']})
            self.js('validationIds=new Set('+json.dumps(ids)+');render();')
            dialog=QDialog(self);dialog.setWindowTitle('Check Structure');dialog.resize(660,420)
            layout=QVBoxLayout(dialog);heading=QLabel(report['summary']);heading.setWordWrap(True);layout.addWidget(heading)
            details=QTextEdit();details.setReadOnly(True)
            details.setPlainText('\n\n'.join(i['severity'].upper()+': '+i['message'] for i in report['issues']) or 'No RDKit valence/aromaticity problems detected. This does not prove chemical stability or synthesizability.')
            layout.addWidget(details);buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Close);buttons.rejected.connect(dialog.reject);layout.addWidget(buttons);dialog.exec()
        self.js('finishEditing();JSON.stringify(doc)',checked)

    def cleanup_structure(self):
        def clean(value):
            if not value:return
            state=json.loads(value)
            dialog=QDialog(self);dialog.setWindowTitle('Clean Up Structure')
            layout=QVBoxLayout(dialog)
            label=QLabel('Clean complete molecules touched by the selected atoms, or all molecules if nothing is selected. Atom/bond identities, charges, labels and annotations remain unchanged.');label.setWordWrap(True);layout.addWidget(label)
            protect=QCheckBox('Preserve metal and coordination geometry');protect.setChecked(True);layout.addWidget(protect)
            label=QLabel('Drawings containing wedge/hashed bonds are preserved. Cleanup changes 2D coordinates; it does not optimize 3D geometry. Undo restores the previous drawing.');label.setWordWrap(True);layout.addWidget(label)
            buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject);layout.addWidget(buttons)
            if not dialog.exec():return
            try:
                from chemistry import cleanup
                report=cleanup(state['drawing'],float(state['length']),state['selected'],protect.isChecked())
            except Exception as e:
                QMessageBox.warning(self,'Cleanup Failed',str(e));return
            coordinates=[{'id':a['id'],'x':a['x'],'y':a['y']} for a in report['drawing']['atoms']]
            self.js('(()=>{const before=snapshot();const coords='+json.dumps(coordinates)+';for(const p of coords){const a=ChemCore.atom(doc,p.id);if(a){a.x=p.x;a.y=p.y}}validationIds.clear();commit(before);fit();})();')
            message=str(report['cleaned_components'])+' molecule(s) cleaned.'
            if report['notes']:message+='\n\n'+'\n'.join(report['notes'])
            QMessageBox.information(self,'Cleanup Result',message)
        self.js("finishEditing();JSON.stringify({drawing:doc,selected:[...selection],length:$('bondLength').value})",clean)

    def clipboard_copy(self, cut=False):
        def copied(value):
            if not value:
                return
            payload=json.loads(value)
            if 'textSelection' in payload:
                mime=QMimeData();mime.setText(payload['textSelection']);mime.setHtml(payload['html']);QApplication.clipboard().setMimeData(mime);return
            from clipboard_graphics import graphics_mime
            try:mime=graphics_mime(payload['svg'],payload['fragment'])
            except ValueError as error:
                QMessageBox.warning(self,'Copy Failed',str(error));return
            QApplication.clipboard().setMimeData(mime)
            if cut:
                self.command('delete')
        self.js("(()=>{const text=textClipboard("+json.dumps(cut)+");if(text)return JSON.stringify(text);finishEditing();if(!selection.size&&!annSelection.size)return '';copy();const whole=doc;try{doc={...doc,...clipboard};return JSON.stringify({fragment:clipboard,svg:exportSVG().text});}finally{doc=whole}})();",copied)

    def clipboard_paste(self):
        mime=QApplication.clipboard().mimeData()
        if mime.hasText():
            text=mime.text()
            self.js('JSON.stringify(!!editing)',lambda value:self.js('insertCharacter('+json.dumps(text)+');') if json.loads(value) else self.statusBar().showMessage('Select the Text tool to paste text.'))
            if not mime.hasFormat('application/x-chemsketch-fragment'):return
        if not mime.hasFormat('application/x-chemsketch-fragment'):
            self.command('paste');return
        try:
            fragment=json.loads(bytes(mime.data('application/x-chemsketch-fragment')).decode('utf-8'))
        except (ValueError,UnicodeError):
            QMessageBox.warning(self,'Paste Failed','The clipboard fragment is invalid.');return
        self.js("(()=>{try{const frag="+json.dumps(fragment)+";const checked=ChemCore.validate({format:'chemsketch-classic',version:1,name:'Clipboard',...frag});clipboard={atoms:checked.atoms,bonds:checked.bonds,annotations:checked.annotations,groups:checked.groups||[],ligands:checked.ligands||[]};paste();}catch(e){notify('Paste failed: '+e.message)}})();")

    def new_document(self):
        def reset():
            self.js('finishEditing();replaceDoc(ChemCore.blank());JSON.stringify(doc)', self.new_saved)
        self.check_unsaved(reset)

    def new_saved(self, value):
        self.path = None; self.saved_doc = value; self.refresh()

    def check_unsaved(self, callback):
        def check(value):
            if not value:
                return
            changed = self.saved_doc is not None and json.loads(value) != json.loads(self.saved_doc)
            if not changed:
                callback(); return
            choice = QMessageBox.question(self, 'Unsaved Drawing', 'Save changes to the current drawing?', QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Save)
            if choice == QMessageBox.StandardButton.Save:
                self.save_document(after=callback)
            elif choice == QMessageBox.StandardButton.Discard:
                callback()
        self.js('finishEditing();JSON.stringify(doc)', check)

    def open_document(self):
        def choose():
            path, _ = QFileDialog.getOpenFileName(self, 'Open Drawing', str(self.path.parent if self.path else Path.home()), 'Chemical Drawings (*.chemjson *.json *.mol *.sdf *.cdx *.cdxml *.cdxl);;All Files (*)')
            if path:
                self.load_path(Path(path))
        self.check_unsaved(choose)

    def load_path(self, path):
        try:
            if path.stat().st_size > 5_000_000:
                raise ValueError('Maximum file size is 5 MB.')
            imported=None
            if path.suffix.lower() in ('.cdx','.cdxml','.cdxl'):
                from chemdraw_io import read_chemdraw
                imported=read_chemdraw(path)
                text=''
            else:text = path.read_text(encoding='utf-8-sig')
        except (OSError, ValueError) as e:
            QMessageBox.warning(self, 'Open Failed', str(e)); return
        if imported:
            code='(()=>{try{const next=ChemCore.validate('+json.dumps(imported['drawing'])+');replaceDoc(next);return JSON.stringify({ok:true,doc});}catch(e){return JSON.stringify({ok:false,error:e.message});}})();'
        else:
            code = '(()=>{try{const text='+json.dumps(text)+";const next=/^\\s*\\{/.test(text)?ChemCore.validate(JSON.parse(text)):ChemCore.fromMol(text);replaceDoc(next);return JSON.stringify({ok:true,doc});}catch(e){return JSON.stringify({ok:false,error:e.message});}})();"
        def opened(value):
            result = json.loads(value or '{}')
            if not result.get('ok'):
                QMessageBox.warning(self, 'Open Failed', result.get('error','Could not load drawing.')); return
            # MOL is an import; subsequent Save writes native JSON instead of overwriting the MOL.
            self.path = path if path.suffix.lower() in ('.chemjson','.json') else None
            self.saved_doc = json.dumps(result['doc']); self.refresh()
            if imported and imported['warnings']:
                QMessageBox.warning(self,'ChemDraw Import Limitations','\n'.join(imported['warnings']))
        self.js(code, opened)

    def save_document(self, force_dialog=False, after=None):
        def write(value):
            if not value:
                return
            path = self.path
            if force_dialog or path is None:
                suggestion = str(path or (Path.home() / 'Drawing.chemjson'))
                chosen, _ = QFileDialog.getSaveFileName(self, 'Save Drawing', suggestion, 'ErezDraw Drawing (*.chemjson)')
                if not chosen:
                    return
                path = Path(chosen)
                if path.suffix.lower() not in ('.chemjson','.json'):
                    path = path.with_suffix('.chemjson')
            try:
                from file_io import write_drawing
                write_drawing(path, json.loads(value))
            except (OSError, ValueError) as e:
                QMessageBox.warning(self, 'Save Failed', str(e)); return
            self.path = path; self.saved_doc = value; self.refresh()
            if after:
                after()
        self.js('finishEditing();JSON.stringify(doc)', write)

    def download_requested(self, download):
        suggested = download.downloadFileName()
        ext = Path(suggested).suffix.lower()
        filters = {'.svg':'SVG Image (*.svg)', '.png':'PNG Image (*.png)', '.mol':'MOL V2000 (*.mol)', '.chemjson':'ErezDraw Drawing (*.chemjson)'}
        chosen, _ = QFileDialog.getSaveFileName(self, 'Export Drawing', str(Path.home()/suggested), filters.get(ext,'All Files (*)'))
        if not chosen:
            download.cancel(); return
        path = Path(chosen)
        if ext and path.suffix.lower() != ext:
            path = path.with_suffix(ext)
        download.setDownloadDirectory(str(path.parent))
        download.setDownloadFileName(path.name)
        self.active_downloads.append(download)
        def finished():
            from PySide6.QtWebEngineCore import QWebEngineDownloadRequest
            if not download.isFinished():
                return
            if download.state() == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
                self.statusBar().showMessage('Exported '+path.name, 5000)
            elif download.state() == QWebEngineDownloadRequest.DownloadState.DownloadInterrupted:
                QMessageBox.warning(self,'Export Failed',download.interruptReasonString())
            if download in self.active_downloads:
                self.active_downloads.remove(download)
        download.stateChanged.connect(finished)
        download.accept()

    def print_document(self):
        self.printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        if QPrintDialog(self.printer,self).exec():
            self.view.print(self.printer)

    def about(self):
        QMessageBox.about(self, APP_NAME, 'ErezDraw 0.11 development\n\nWindows/macOS desktop application with native Qt menus, toolbars, dialogs and dockable palette.\n\nThe embedded offline drawing canvas retains the JavaScript/SVG engine. No external browser or local server is required.\n\nGPL-3.0-or-later source; includes attributed ChemCanvas geometry adaptations. Independent software, not affiliated with ChemDraw. RDKit supplies warning-only valence/aromaticity checks and 2D cleanup. Unsupported labels and metal components are reported as unchecked.')

    def closeEvent(self, event):
        if self.allow_close or not self.ready:
            self.timer.stop(); event.accept(); return
        event.ignore()
        def confirmed():
            self.allow_close = True
            self.close()
        self.check_unsaved(confirmed)


def main():
    if '--self-test' in sys.argv:
        from startup_check import check_runtime
        report = Path(sys.argv[sys.argv.index('--self-test') + 1])
        try:
            result = check_runtime(ROOT)
            report.write_text(json.dumps(result, indent=2), encoding='utf-8')
            return 0
        except Exception:
            import traceback
            report.write_text(traceback.format_exc(), encoding='utf-8')
            return 1
    app = QApplication(sys.argv)
    app.setOrganizationName('ErezDraw')
    app.setApplicationName(APP_NAME)
    from appearance import Appearance
    app.appearance = Appearance(app)
    window = Editor()
    window.show()
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
