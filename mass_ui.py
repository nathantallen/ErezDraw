"""Native fragment mass explorer with linked peaks, structures and CSV export."""
import json,csv
from PySide6.QtCore import QTimer,Qt,QPointF
from PySide6.QtGui import QPainter,QPen,QColor
from PySide6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QLabel,QComboBox,QTableWidget,QTableWidgetItem,QDialogButtonBox,QPushButton,QFileDialog,QWidget,QSplitter
from PySide6.QtSvgWidgets import QSvgWidget
from spectrum_ui import SpectrumWidget
from mass_spec import fragmentation,MODES

class MassPlot(SpectrumWidget):
    def __init__(self,rows,parent=None):
        super().__init__([{**r,'delta':r['mz'],'count':1} for r in rows],'MS',parent);self.low=0;self.high=max([r['mz'] for r in rows] or [100])*1.08
    def xpos(self,value):return 48+(value-self.low)/(self.high-self.low)*max(1,self.width()-70)
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing);p.fillRect(self.rect(),Qt.GlobalColor.white);base=self.height()-38;p.setPen(QColor('#333'));p.drawLine(48,base,self.width()-22,base);p.drawText(8,18,'Calculated fragment-ion candidates — equal marker heights');p.drawText(self.width()-65,self.height()-6,'m/z')
        for j in range(11):
            value=self.high*j/10;x=self.xpos(value);p.drawLine(QPointF(x,base),QPointF(x,base+5));p.drawText(int(x)-12,base+22,f'{value:.0f}')
        for i,r in enumerate(self.rows):
            x=self.xpos(r['mz']);p.setPen(QPen(QColor('#d32f2f') if i in self.active else QColor('#204a76'),2 if i in self.active else 1));p.drawLine(QPointF(x,base),QPointF(x,30));
            if i in self.active:p.drawText(int(x)+3,45,f"{r['mz']:.4f}")

class MassActions:
    def mass_fragmentation(self):
        def show(state,initial):
            dialog=QDialog(self);dialog.setWindowTitle('Mass Spectrometry Fragmentation');dialog.resize(1000,650);layout=QVBoxLayout(dialog);notice=QLabel('Theoretical precursor and single-bond-cleavage ion masses. Hover peaks to highlight fragment atoms. Equal-height markers are not predicted abundances. Rearrangements, sequential fragmentation, collision-energy effects and metal complexes are outside this model.');notice.setWordWrap(True);layout.addWidget(notice);mode=QComboBox();mode.addItems(list(MODES));layout.addWidget(mode);body=QSplitter(Qt.Orientation.Horizontal);body.setObjectName('MassSpectrumStructureSplitter');preview=QSvgWidget();preview.setMinimumSize(180,180);plot_container=QWidget();plot_holder=QVBoxLayout(plot_container);plot_holder.setContentsMargins(0,0,0,0);body.addWidget(plot_container);body.addWidget(preview);body.setSizes([550,350]);body.setChildrenCollapsible(False);body.setHandleWidth(7);table=QTableWidget();splitter=QSplitter(Qt.Orientation.Vertical);splitter.setObjectName('MassSpectrumTableSplitter');splitter.addWidget(body);splitter.addWidget(table);splitter.setSizes([350,200]);splitter.setChildrenCollapsible(False);splitter.setHandleWidth(7);layout.addWidget(splitter);current={};plot=[None]
            def highlight(indices):
                ids=sorted({a for i in indices for a in current['rows'][i]['drawingAtoms']});all_ids=[a['id'] for a in current['atoms']]
                script="(()=>{nmrHighlights={nucleus:'13C',ids:"+json.dumps(ids)+"};render();const saved=doc;try{doc={...doc,atoms:doc.atoms.filter(a=>"+json.dumps(all_ids)+".includes(a.id)),bonds:doc.bonds.filter(b=>"+json.dumps(all_ids)+".includes(b.a)&&"+json.dumps(all_ids)+".includes(b.b)),annotations:[]};return exportSVG(true).text}finally{doc=saved}})()"
                self.js(script,lambda svg:preview.load(svg.encode('utf-8')) if svg else None)
            def update():
                result=fragmentation(state['drawing'],state['selected'],mode.currentText());current.clear();current.update(result)
                if plot[0]:plot_holder.removeWidget(plot[0]);plot[0].deleteLater()
                plot[0]=MassPlot(current['rows']);plot_holder.addWidget(plot[0]);plot[0].hovered.connect(highlight);table.setRowCount(len(current['rows']));table.setColumnCount(5);table.setHorizontalHeaderLabels(['m/z (exact)','Ion formula','Type','Cleaved bond','Neutral loss'])
                for i,r in enumerate(current['rows']):
                    values=[f"{r['mz']:.5f}",r['formula'],'Precursor' if r['precursor'] else 'Cleavage candidate',str(r['bond'] or ''),r['neutralLoss'] or '']
                    for j,v in enumerate(values):table.setItem(i,j,QTableWidgetItem(v))
                table.resizeColumnsToContents();highlight([])
            mode.currentTextChanged.connect(update);table.cellClicked.connect(lambda i,j:highlight([i]));update();copy=QPushButton('Copy Spectrum');layout.addWidget(copy)
            def copy_plot():
                from PySide6.QtWidgets import QApplication
                from clipboard_graphics import widget_graphics_mime
                QApplication.clipboard().setMimeData(widget_graphics_mime(plot[0]))
            copy.clicked.connect(copy_plot);export=QPushButton('Export CSV…');layout.addWidget(export)
            def save():
                path,_=QFileDialog.getSaveFileName(dialog,'Export fragment masses','fragment-masses.csv','CSV (*.csv)')
                if path:
                    with open(path,'w',newline='',encoding='utf-8-sig') as f:
                        writer=csv.writer(f);writer.writerow([table.horizontalHeaderItem(i).text() for i in range(5)]);writer.writerows([[table.item(i,j).text() for j in range(5)] for i in range(table.rowCount())])
            export.clicked.connect(save);buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Close);buttons.rejected.connect(dialog.reject);layout.addWidget(buttons);dialog.exec();self.js('nmrHighlights=null;render();')
        def prepare(state):
            initial=fragmentation(state['drawing'],state['selected']);QTimer.singleShot(0,lambda:show(state,initial))
        self.structure_state(prepare)
