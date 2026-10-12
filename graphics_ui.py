"""Native editing of drawing tables and curve styles."""
import json
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication,QDialog,QVBoxLayout,QFormLayout,QSpinBox,QTableWidget,QTableWidgetItem,QDialogButtonBox,QPushButton,QHBoxLayout

class GraphicsActions:
    def choose_text_color(self):
        from PySide6.QtWidgets import QColorDialog
        from PySide6.QtGui import QColor
        color=QColorDialog.getColor(QColor('#000000'),self,'Text Color')
        if color.isValid():self.js('setTextStyle('+json.dumps({'color':color.name()})+');')

    def text_line_spacing(self):
        from PySide6.QtWidgets import QInputDialog
        value,ok=QInputDialog.getDouble(self,'Line Spacing','Line-height multiplier',1.2,.5,5,2)
        if ok:self.js('paragraphStyle('+json.dumps({'lineSpacing':value})+');')

    def edit_table(self,object_id):
        def loaded(value):
            state=json.loads(value);a=next((a for a in state['drawing']['annotations'] if a['id']==object_id),None)
            if not a or a['type']!='table':return
            dialog=QDialog(self);dialog.setWindowTitle('Edit Table');dialog.resize(620,420);layout=QVBoxLayout(dialog);form=QFormLayout();rows=QSpinBox();cols=QSpinBox();rows.setRange(1,30);cols.setRange(1,20);rows.setValue(a['rows']);cols.setValue(a['cols']);form.addRow('Rows',rows);form.addRow('Columns',cols);layout.addLayout(form)
            table=QTableWidget(a['rows'],a['cols']);layout.addWidget(table)
            for r in range(a['rows']):
                for c in range(a['cols']):
                    item=QTableWidgetItem(a['cells'][r*a['cols']+c]);fragment=(a.get('cellObjects') or [None]*(a['rows']*a['cols']))[r*a['cols']+c]
                    if fragment:item.setText('[Drawing]');item.setData(Qt.ItemDataRole.UserRole,fragment)
                    table.setItem(r,c,item)
            paste=QPushButton('Paste ErezDraw selection into cell');layout.addWidget(paste)
            def paste_drawing():
                mime=QApplication.clipboard().mimeData();data=mime.data('application/x-chemsketch-fragment')
                if not data:return
                fragment=json.loads(bytes(data));r=max(0,table.currentRow());c=max(0,table.currentColumn());item=QTableWidgetItem('[Drawing]');item.setData(Qt.ItemDataRole.UserRole,fragment);table.setItem(r,c,item)
            paste.clicked.connect(paste_drawing)
            rows.valueChanged.connect(table.setRowCount);cols.valueChanged.connect(table.setColumnCount)
            buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject);layout.addWidget(buttons)
            if dialog.exec():
                cells=[table.item(r,c).text()[:500] if table.item(r,c) else '' for r in range(rows.value()) for c in range(cols.value())]
                objects=[table.item(r,c).data(Qt.ItemDataRole.UserRole) if table.item(r,c) and table.item(r,c).text()=='[Drawing]' else None for r in range(rows.value()) for c in range(cols.value())];update={'rows':rows.value(),'cols':cols.value(),'cells':cells,'cellObjects':objects}
                self.js("(()=>{const a=doc.annotations.find(a=>a.id==="+json.dumps(object_id)+");if(!a)return;const before=snapshot();Object.assign(a,"+json.dumps(update)+");try{ChemCore.validate(doc);commit(before)}catch(e){doc=before;notify(e.message);render()}})()")
        self.js('JSON.stringify({drawing:doc})',loaded)
