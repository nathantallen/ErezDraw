"""Native dialogs for implemented Structure menu commands."""
import copy,json,html
from PySide6.QtCore import QObject,Signal,QRunnable,QThreadPool,QTimer,Qt
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QFormLayout,QDialogButtonBox,QLineEdit,QLabel,QCheckBox,QComboBox,QSpinBox,QMessageBox,QPushButton,QTableWidget,QTableWidgetItem,QAbstractItemView,QTextEdit,QFileDialog,QDoubleSpinBox)
from rdkit import Chem
import structure_ops as ops

class Signals(QObject):
    done=Signal(object,object)
class Job(QRunnable):
    def __init__(self,fn,callback):
        super().__init__();self.fn=fn;self.signals=Signals();self.signals.done.connect(callback)
    def run(self):
        try:self.signals.done.emit(self.fn(),None)
        except Exception as e:self.signals.done.emit(None,str(e))

class StructureActions:
    def structure_state(self,callback):
        def received(value):
            try:callback(json.loads(value))
            except Exception as e:QMessageBox.warning(self,'Structure',str(e))
        self.js("finishEditing();JSON.stringify({drawing:doc,selected:[...selection]})",received)

    def apply_structure(self,state,drawing):
        # An asynchronous lookup must never replace newer edits.
        self.js("(()=>{if(JSON.stringify(doc)!==JSON.stringify("+json.dumps(state['drawing'])+")){notify('Drawing changed; run the command again.');return}const before=snapshot();doc=ChemCore.validate("+json.dumps(drawing)+");selection.clear();annSelection.clear();commit(before);render();})();")

    def structure_transform(self,operation):
        def run(state):
            result=ops.hydrogens(state['drawing'],state['selected'],remove=operation=='removeH') if operation in ('addH','removeH') else ops.expand(state['drawing'],state['selected'])
            self.apply_structure(state,result)
        self.structure_state(run)

    def contract_label(self):
        def show(state):
            dialog=QDialog(self);dialog.setWindowTitle('Contract Label');form=QFormLayout(dialog);name=QLineEdit('R');name.setMaxLength(40);form.addRow('Abbreviation',name);buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);form.addRow(buttons);buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject)
            if dialog.exec() and name.text().strip():self.apply_structure(state,ops.contract(state['drawing'],state['selected'],name.text().strip()))
        self.structure_state(show)

    def molecule_label(self):
        def show(state):
            prop=ops.properties(state['drawing'],state['selected']);dialog=QDialog(self);dialog.setWindowTitle('Label Molecule');form=QFormLayout(dialog);name=QLineEdit(prop['name']);name.setMaxLength(400);name.setPlaceholderText('Enter a name or look it up');form.addRow('Name',name);form.addRow('Formula',QLabel(prop['formula']));form.addRow('Molecular weight',QLabel(f"{prop['weight']:.3f} g/mol"))
            lookup=QPushButton('Look up name in PubChem');form.addRow(lookup);notice=QLabel('Lookup sends this molecule’s structure to PubChem. Labels are editable snapshots.');notice.setWordWrap(True);form.addRow(notice)
            jobs=[]
            def search():
                lookup.setEnabled(False)
                def done(value,error):
                    if not dialog.isVisible():return
                    lookup.setEnabled(True)
                    if error:notice.setText('Name lookup failed: '+error)
                    else:name.setText(value['name']);notice.setText('Exact structure/charge match: PubChem CID '+str(value['cid'])+'. '+('Centroid attachments queried as ionic metal/ligand components.' if value['query']['centroid'] else ''))
                job=Job(lambda:ops.lookup_structure_name(state['drawing'],state['selected']),done);jobs.append(job);QThreadPool.globalInstance().start(job)
            lookup.clicked.connect(search)
            buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);buttons.button(QDialogButtonBox.StandardButton.Ok).setText('Insert Label');form.addRow(buttons);buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject)
            if dialog.exec():
                if not name.text().strip():raise ValueError('Enter a molecule name before inserting the label.')
                out=copy.deepcopy(state['drawing']);x=prop['bounds']['x'];y=prop['bounds']['y']+40
                for offset,text in [(0,name.text().strip()),(23,f"MW: {prop['weight']:.3f} g/mol")]:out['annotations'].append({'id':ops.uid('label'),'type':'text','x':x,'y':y+offset,'text':text})
                self.apply_structure(state,out)
        self.structure_state(show)

    def name_to_structure(self):
        def show(state):
            dialog=QDialog(self);dialog.setWindowTitle('Convert Name to Structure');form=QFormLayout(dialog);entry=QLineEdit();entry.setPlaceholderText('Chemical name');form.addRow('Name / SMILES',entry);smiles=QCheckBox('Input is SMILES');form.addRow(smiles);online=QCheckBox('Use PubChem if name is not in local dictionary (sends name)');form.addRow(online);message=QLabel('Local common names and SMILES work offline.');message.setWordWrap(True);form.addRow(message)
            buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);buttons.button(QDialogButtonBox.StandardButton.Ok).setText('Insert Structure');form.addRow(buttons);buttons.rejected.connect(dialog.reject);jobs=[]
            def insert():
                value=entry.text().strip()
                if not value:return
                buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
                def work():return ops.from_smiles(value if smiles.isChecked() else ops.name_to_smiles(value,online.isChecked()))
                # Snapshot control values before leaving the UI thread.
                is_smiles=smiles.isChecked();use_online=online.isChecked()
                def done(fragment,error):
                    if not dialog.isVisible():return
                    buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
                    if error:message.setText(error);return
                    out=copy.deepcopy(state['drawing']);out['atoms']+=fragment['atoms'];out['bonds']+=fragment['bonds'];self.apply_structure(state,out);dialog.accept()
                job=Job(lambda:ops.from_smiles(value if is_smiles else ops.name_to_smiles(value,use_online)),done);jobs.append(job);QThreadPool.globalInstance().start(job)
            buttons.accepted.connect(insert);dialog.exec()
        self.structure_state(show)

    def atom_properties(self):
        def show(state):
            atoms=[a for a in state['drawing']['atoms'] if a['id'] in state['selected']]
            if len(atoms)!=1 or atoms[0].get('nodeType'):raise ValueError('Select one chemical atom.')
            a=copy.deepcopy(atoms[0]);dialog=QDialog(self);dialog.setWindowTitle('Atom Properties');form=QFormLayout(dialog);label=QLineEdit(a['label']);label.setMaxLength(40);form.addRow('Element / label',label);charge=QSpinBox();charge.setRange(-20,20);charge.setValue(a['charge']);form.addRow('Formal charge',charge);automatic=QCheckBox('Update formal charge from recognized bonding / ligand charges');automatic.setChecked(a.get('chargeMode')!='manual' and (a.get('chargeMode')=='auto' or a['charge']==0));form.addRow(automatic);charge.valueChanged.connect(lambda _:automatic.setChecked(False));net=QSpinBox();net.setRange(-20,20);net.setValue(a.get('complexCharge',0));form.addRow('Total complex charge (single metal)',net);radical=QSpinBox();radical.setRange(0,2);radical.setValue(a.get('radical',0));form.addRow('Unpaired electrons',radical);pairs=QSpinBox();pairs.setRange(0,4);pairs.setValue(a.get('lonePairs',0));form.addRow('Displayed lone pairs',pairs);buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);form.addRow(buttons);buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject)
            if dialog.exec():
                if not label.text().strip():raise ValueError('Atom label cannot be empty.')
                if label.text().strip()!=a['label']:a.pop('textRuns',None)
                a.update(label=label.text().strip(),charge=charge.value(),chargeMode='auto' if automatic.isChecked() else 'manual',complexCharge=net.value(),radical=radical.value(),lonePairs=pairs.value());out=copy.deepcopy(state['drawing']);next(x for x in out['atoms'] if x['id']==a['id']).update(a)
                self.apply_structure(state,out)
        self.structure_state(show)

    def bond_properties(self):
        def show(state):
            bonds=[b for b in state['drawing']['bonds'] if b['a'] in state['selected'] and b['b'] in state['selected']]
            if len(bonds)!=1:raise ValueError('Select one bond with the selection tool.')
            b=bonds[0];dialog=QDialog(self);dialog.setWindowTitle('Bond Properties');form=QFormLayout(dialog);order=QComboBox();order.addItems(['Single','Double','Triple','Aromatic']);order.setCurrentIndex(b['order']-1);form.addRow('Order',order);style=QComboBox();style.addItems(['normal','wedge','hash','coord','dashed','hashed','boldBond','hollowWedge','wavy','crossBond']);style.setCurrentText(b['style']);form.addRow('Style',style);side=QComboBox();side.addItems(['auto','left','right','center']);side.setCurrentText(b.get('doublePosition','auto'));form.addRow('Double bond position',side);reverse=QCheckBox('Reverse bond direction');form.addRow(reverse);buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);form.addRow(buttons);buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject)
            if dialog.exec():
                out=copy.deepcopy(state['drawing']);target=next(x for x in out['bonds'] if x['id']==b['id']);target.update(order=order.currentIndex()+1,style=style.currentText());target.pop('doublePosition',None)
                if side.currentText()!='auto':target['doublePosition']=side.currentText()
                if reverse.isChecked():target['a'],target['b']=target['b'],target['a']
                self.apply_structure(state,out)
        self.structure_state(show)

    def predict_nmr(self,nucleus):
        def start(state):
            frag,graph,mol=ops.interpreted(state['drawing'],state['selected'],organic=True)
            if mol.GetNumAtoms()>200:raise ValueError('Local NMR prediction is limited to 200 atoms per molecule.')
            if any(b['style'] in ('wedge','hash','hollowWedge') for b in graph['bonds']):raise ValueError('Stereochemical NMR assignments are not supported yet. Remove wedge/hash stereo only if you intend an unspecified stereoisomer.')
            if any(a.get('radical') for a in graph['atoms']):raise ValueError('Radical NMR prediction is outside the model.')
            ids=[a['id'] for a in graph['atoms'] if a['label']!='H'];mol=Chem.RemoveHs(mol);molfile=Chem.MolToMolBlock(mol)
            self.statusBar().showMessage('Predicting '+nucleus+' shifts locally…')
            def ready(value):
                result=json.loads(value)
                if result.get('error'):QMessageBox.warning(self,'NMR Prediction',result['error']);return
                from nmr_spectrum import estimate_couplings
                rows=result['rows']
                if nucleus=='1H':
                    from nmr_models import refine_proton_shifts
                    refine_proton_shifts(mol,rows);estimate_couplings(mol,rows)
                QTimer.singleShot(0,lambda:self.nmr_result(nucleus,rows,ids,state,mol))
            self.js("(()=>{try{return JSON.stringify({rows:ErezNMR.predict("+json.dumps(molfile)+','+json.dumps(nucleus)+")})}catch(e){return JSON.stringify({error:e.message})}})()",ready)
        self.structure_state(start)

    def nmr_result(self,nucleus,rows,ids,state,mol=None):
        dialog=QDialog(self);dialog.setWindowTitle(nucleus+' NMR Prediction');dialog.resize(850,550);layout=QVBoxLayout(dialog)
        text=QLabel('Confidence-filtered HOSE database and approximate proton environment model. Chemical shifts in ppm; solvent and temperature are not modeled. ¹H uses a small beta database; missing matches are shown as unavailable. Hover a peak or click a row to highlight the associated nuclei. Small coupled proton systems use a spin Hamiltonian with estimated J values, including aromatic ortho/meta/para couplings. Components over 8 spins fall back to first-order splitting. Exchangeable protons are uncoupled; solvent-specific shifts and exact J values are not predicted. The Shift source column identifies environment estimates.');text.setWordWrap(True);layout.addWidget(text)
        table=QTableWidget(len(rows),8);table.setHorizontalHeaderLabels(['δ (ppm)','Nuclei','Attached atom IDs','Matches','Shells','Observed min','Observed max','Shift source']);table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers);table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows);
        for i,row in enumerate(rows):
            attached=[ids[j] for j in row['attachedAtoms'] if 0<=j<len(ids)];row['drawingAtoms']=attached
            values=['Unavailable' if row['delta'] is None else f"{row['delta']:.2f}",str(row['count']),', '.join(attached),str(row['matches']),str(row['level']),str(row.get('min','')),str(row.get('max','')),row.get('source','HOSE database')]
            for j,v in enumerate(values):table.setItem(i,j,QTableWidgetItem(v))
        from spectrum_ui import SpectrumWidget
        from PySide6.QtWidgets import QHBoxLayout,QSplitter
        from PySide6.QtSvgWidgets import QSvgWidget
        spectrum=SpectrumWidget(rows,nucleus,molecule=mol);preview=QSvgWidget();preview.setMinimumSize(180,180);spectrum_row=QSplitter(Qt.Orientation.Horizontal);spectrum_row.setObjectName('SpectrumStructureSplitter');spectrum_row.addWidget(spectrum);spectrum_row.addWidget(preview);spectrum_row.setSizes([510,300]);spectrum_row.setChildrenCollapsible(False);spectrum_row.setHandleWidth(7);splitter=QSplitter(Qt.Orientation.Vertical);splitter.setObjectName('SpectrumTableSplitter');splitter.addWidget(spectrum_row);splitter.addWidget(table);splitter.setSizes([320,180]);splitter.setChildrenCollapsible(False);splitter.setHandleWidth(7);layout.insertWidget(1,splitter)
        def highlight(indices):
            selected=sorted({atom for i in indices for atom in rows[i]['drawingAtoms']})
            script="(()=>{nmrHighlights={nucleus:"+json.dumps(nucleus)+",ids:"+json.dumps(selected)+"};validationIds.clear();render();const saved=doc;try{doc={...doc,atoms:doc.atoms.filter(a=>"+json.dumps(ids)+".includes(a.id)),bonds:doc.bonds.filter(b=>"+json.dumps(ids)+".includes(b.a)&&"+json.dumps(ids)+".includes(b.b)),annotations:[]};return exportSVG(true).text}finally{doc=saved}})()"
            self.js(script,lambda svg:preview.load(svg.encode('utf-8')) if svg else None)
        spectrum.hovered.connect(highlight);highlight([])
        controls=QHBoxLayout();frequency=QDoubleSpinBox();frequency.setRange(40,1200);frequency.setDecimals(1);frequency.setValue(getattr(self,'nmr_mhz',400));frequency.setSuffix(' MHz');linewidth=QDoubleSpinBox();linewidth.setRange(.1,20);linewidth.setValue(1);linewidth.setSuffix(' Hz');coupled=QCheckBox('Coupled ¹H simulation');coupled.setChecked(nucleus=='1H');coupled.setEnabled(nucleus=='1H');controls.addWidget(QLabel('Spectrometer frequency (¹H)'));controls.addWidget(frequency);controls.addWidget(QLabel('Linewidth'));controls.addWidget(linewidth);controls.addWidget(coupled);layout.insertLayout(1,controls)
        def configure():
            self.nmr_mhz=frequency.value();spectrum.configure(frequency.value() if nucleus=='1H' else frequency.value()*.25144953,linewidth.value(),coupled.isChecked())
        frequency.valueChanged.connect(configure);linewidth.valueChanged.connect(configure);coupled.toggled.connect(configure);configure()

        copy_spectrum=QPushButton('Copy Spectrum');layout.addWidget(copy_spectrum)
        def copy_plot():
            from PySide6.QtWidgets import QApplication
            from clipboard_graphics import widget_graphics_mime
            QApplication.clipboard().setMimeData(widget_graphics_mime(spectrum))
        copy_spectrum.clicked.connect(copy_plot)
        for column in (3,4,5,6):table.setColumnHidden(column,True)
        table.resizeColumnsToContents()
        table.cellClicked.connect(lambda i,j:highlight([i]))
        export=QPushButton('Export CSV…');layout.addWidget(export)
        def save():
            path,_=QFileDialog.getSaveFileName(dialog,'Export predicted shifts',nucleus+'-prediction.csv','CSV (*.csv)')
            if path:
                import csv
                with open(path,'w',newline='',encoding='utf-8-sig') as f:
                    writer=csv.writer(f);writer.writerow([table.horizontalHeaderItem(i).text() for i in range(table.columnCount())]);writer.writerows([[table.item(i,j).text() for j in range(table.columnCount())] for i in range(table.rowCount())])
        export.clicked.connect(save);buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Close);buttons.rejected.connect(dialog.reject);layout.addWidget(buttons);dialog.exec();self.js('nmrHighlights=null;validationIds.clear();render();')

    def install_ligand_panel(self):
        from PySide6.QtWidgets import QDockWidget,QTabWidget,QScrollArea,QWidget,QGridLayout,QToolButton
        from PySide6.QtCore import Qt,QSize,QByteArray
        from PySide6.QtGui import QIcon,QPixmap
        from rdkit.Chem.Draw import rdMolDraw2D
        from ligands import LIGANDS,ligand_template
        dock=QDockWidget('Organometallic Ligands',self);dock.setObjectName('LigandTemplates');tabs=QTabWidget();dock.setWidget(tabs);self.ligand_dock=dock
        for category in dict.fromkeys(x[0] for x in LIGANDS):
            content=QWidget();grid=QGridLayout(content);scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(content);tabs.addTab(scroll,category)
            for i,(_,name,smiles,haptic) in enumerate(x for x in LIGANDS if x[0]==category):
                mol=Chem.MolFromSmiles(smiles);draw=rdMolDraw2D.MolDraw2DSVG(140,80);draw.drawOptions().noAtomLabels=haptic=='cp';draw.DrawMolecule(mol);draw.FinishDrawing();pixmap=QPixmap();pixmap.loadFromData(QByteArray(draw.GetDrawingText().encode()),'SVG');button=QToolButton();button.setIcon(QIcon(pixmap));button.setIconSize(QSize(140,80));button.setText(__import__('textwrap').fill(name,24));button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon);button.setFixedSize(185,120);button.setToolTip(name+' — select, then click/drag in the drawing. '+('Bond to the center handle.' if haptic else 'Bond to the donor atom.'))
                button.clicked.connect(lambda checked=False,n=name:self.js('setLigandTemplate('+json.dumps(ligand_template(n))+');'));grid.addWidget(button,i//2,i%2)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea,dock);dock.hide();a=dock.toggleViewAction();a.setText('Show Ligand Templates');self.menus['View'].addAction(a);self.actions['ligandTemplates']=a


    def install_glassware_panel(self):
        from PySide6.QtWidgets import QDockWidget,QScrollArea,QWidget,QGridLayout,QToolButton,QLineEdit
        from PySide6.QtCore import QSize,QByteArray
        from PySide6.QtGui import QIcon,QPixmap
        from glassware import glassware_catalog
        dock=QDockWidget('Glassware & Pilot Equipment',self);dock.setObjectName('GlasswareTemplates')
        host=QWidget();layout=QVBoxLayout(host);search=QLineEdit();search.setPlaceholderText('Find glassware or pilot equipment');search.setClearButtonEnabled(True);layout.addWidget(search)
        note=QLabel('Select a part, then press and drag to position it; release to place. Use selection handles to rotate or resize.');note.setWordWrap(True);layout.addWidget(note)
        content=QWidget();grid=QGridLayout(content);scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(content);layout.addWidget(scroll);dock.setWidget(host)
        buttons=[]
        for i,item in enumerate(glassware_catalog()):
            pixmap=QPixmap();pixmap.loadFromData(QByteArray(item['svg'].encode()),'SVG');button=QToolButton();button.setObjectName('glassware-'+str(i));button.setIcon(QIcon(pixmap));button.setIconSize(QSize(145,100));button.setText(__import__('textwrap').fill(item['name'],25));button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon);button.setFixedSize(185,145);button.setToolTip(item['category']+' — '+item['name'])
            button.clicked.connect(lambda checked=False,f=item['template']:self.js('setGlasswareTemplate('+json.dumps(f)+');'));grid.addWidget(button,i//2,i%2);buttons.append((button,(item['category']+' '+item['name']).lower()))
        def filter_parts(value):
            visible=[button for button,text in buttons if value.lower() in text]
            for button,_ in buttons:grid.removeWidget(button);button.hide()
            for i,button in enumerate(visible):grid.addWidget(button,i//2,i%2);button.show()
        search.textChanged.connect(filter_parts);self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea,dock);dock.hide();self.glassware_dock=dock
        action=dock.toggleViewAction();action.setText('Show Glassware Templates');self.menus['View'].addAction(action);self.actions['glasswareTemplates']=action
