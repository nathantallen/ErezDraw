"""Dockable View panels, updated from the live document and selection."""
import json
from PySide6.QtCore import Qt,QTimer
from PySide6.QtWidgets import QDockWidget,QWidget,QVBoxLayout,QGridLayout,QPushButton,QLabel,QTextEdit,QScrollArea,QApplication,QComboBox
from PySide6.QtGui import QAction
from rdkit import Chem
from structure_ops import analysis

class ViewPanels:
    def install_view_panels(self):
        self.view_panels={};self.panel_text={};self.panel_values={};self.panel_cache=None;view=self.menus['View']
        for name in ['Analysis','Chemical Properties','Info','Periodic Table','Character Map']:
            dock=QDockWidget(name,self);dock.setObjectName('Panel'+name.replace(' ',''));body=QWidget();layout=QVBoxLayout(body)
            if name in ('Analysis','Chemical Properties','Info'):
                text=QTextEdit();text.setReadOnly(True);layout.addWidget(text);self.panel_text[name]=text
                copy=QPushButton('Copy');copy.clicked.connect(lambda checked=False,n=name:QApplication.clipboard().setText(self.panel_text[n].toPlainText()));layout.addWidget(copy)
                if name!='Info':
                    paste=QPushButton('Paste into Drawing');paste.clicked.connect(lambda checked=False,n=name:self.paste_analysis(n));layout.addWidget(paste)
            elif name=='Periodic Table':
                desc=QLabel('Select an element to activate its atom tool.');desc.setWordWrap(True);layout.addWidget(desc);grid=QGridLayout();table=Chem.GetPeriodicTable()
                rows=[[1]+[0]*16+[2],[3,4]+[0]*10+list(range(5,11)),[11,12]+[0]*10+list(range(13,19)),list(range(19,37)),list(range(37,55)),[55,56,57]+list(range(72,87)),[87,88,89]+list(range(104,119)),[0,0,0]+list(range(58,72)),[0,0,0]+list(range(90,104))]
                for row,values in enumerate(rows):
                    for col,z in enumerate(values):
                        if not z:continue
                        symbol=table.GetElementSymbol(z);button=QPushButton(symbol);button.setFixedSize(35,29);button.setToolTip(f'{z}: {table.GetElementName(z)}; atomic weight {table.GetAtomicWeight(z)}');button.clicked.connect(lambda checked=False,s=symbol:self.choose_element(s));grid.addWidget(button,row,col)
                layout.addLayout(grid)
            else:
                layout.addWidget(QLabel('Click a character to insert it into the selected caption,\nor create a caption at the view center.'))
                grid=QGridLayout()
                chars='αβγδεζηθικλμνξοπρστυφχψωΔΣΩ±−×÷≈≠≤≥∞°Åηκ·•‡†←→↔⇌₀₁₂₃₄₅₆₇₈₉⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻'
                for i,char in enumerate(chars):
                    b=QPushButton(char);b.setFixedSize(32,28);b.clicked.connect(lambda checked=False,c=char:self.js('insertCharacter('+json.dumps(c)+');'));grid.addWidget(b,i//12,i%12)
                layout.addLayout(grid)
            scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(body);dock.setWidget(scroll);self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea,dock);dock.hide();self.view_panels[name]=dock
            a=dock.toggleViewAction();a.setText('Show '+name+' Window');view.addAction(a);self.actions['panel_'+name]=a
        view.addSeparator()
        for key,label,variable in [('rulers','Show Rulers','showRulers'),('crosshair','Show Crosshair','showCrosshair')]:
            a=QAction(label,self);a.setCheckable(True);a.toggled.connect(lambda value,v=variable:self.js(v+'='+json.dumps(value)+';render();'));view.addAction(a);self.actions[key]=a
        self.add_action(view,'fitWindow','Fit to Window',lambda:self.js('center={x:408,y:528};zoomTo(Math.min(canvas.clientWidth/816,canvas.clientHeight/1056)*.95);'))
        self.panel_timer=QTimer(self);self.panel_timer.setInterval(600);self.panel_timer.timeout.connect(self.update_view_panels);self.panel_timer.start()

    def choose_element(self,symbol):
        self.atom_input.setText(symbol);self.js('element='+json.dumps(symbol)+";$('elementInput').value=element;setTool('atom');if(selection.size===1)changeLabel(element);")

    def update_view_panels(self):
        if not self.ready or not any(self.view_panels[n].isVisible() for n in self.panel_text):return
        def update(value):
            if not value:return
            state=json.loads(value);key=json.dumps([state['drawing'],state['selected']])
            if key!=self.panel_cache:
                self.panel_cache=key
                try:self.panel_values['Analysis'],self.panel_values['Chemical Properties']=analysis(state['drawing'],state['selected'])
                except Exception as e:self.panel_values['Analysis']={'Status':str(e)};self.panel_values['Chemical Properties']={'Status':str(e)}
                for name in ('Analysis','Chemical Properties'):self.panel_text[name].setPlainText('\n\n'.join(f'{k}: {v}' for k,v in self.panel_values[name].items()))
            b=state.get('bounds');info=f"Zoom: {state['zoom']*100:.0f}%\nSelected atoms: {len(state['selected'])}\nSelected annotations: {state['annotations']}\nPointer: {state['pointer']['x']*.75:.1f}, {state['pointer']['y']*.75:.1f} pt"
            if b:info+=f"\nPosition: {b['x']*.75:.1f}, {b['y']*.75:.1f} pt\nSize: {(b['x2']-b['x'])*.75:.1f} × {(b['y2']-b['y'])*.75:.1f} pt"
            if state.get('bond'):info+=f"\nBond length: {state['bond']['length']*.75:.2f} pt\nBond angle: {state['bond']['angle']:.1f}°"
            self.panel_text['Info'].setPlainText(info)
        self.js("JSON.stringify({drawing:doc,selected:[...selection],annotations:annSelection.size,bounds:selectionBounds(),zoom,pointer:lastPointer,bond:(()=>{const b=doc.bonds.filter(b=>selection.has(b.a)&&selection.has(b.b));if(b.length!==1)return null;const a=ChemCore.atom(doc,b[0].a),c=ChemCore.atom(doc,b[0].b);return {length:ChemCore.dist(a,c),angle:Math.atan2(a.y-c.y,c.x-a.x)*180/Math.PI}})()})",update)

    def paste_analysis(self,name):
        values=self.panel_values.get(name,{})
        if 'Status' in values or not values:return
        lines=[f'{k}: {v}'[:500] for k,v in values.items() if '\n' not in v and k not in ('Model','Isotope method')]
        self.js('(()=>{const before=snapshot();const lines='+json.dumps(lines)+";for(let i=0;i<lines.length;i++)doc.annotations.push({id:id('analysis'),type:'text',x:center.x,y:center.y+i*24,text:lines[i]});commit(before);})();")
