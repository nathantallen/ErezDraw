"""Compact classic desktop interface, with explicit capability states."""
import json,sys
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QIcon, QPixmap, QPainter, QFont, QColor
from PySide6.QtWidgets import (QToolBar,QToolButton,QMenu,QWidget,QGridLayout,QComboBox,
 QLabel,QFontComboBox,QScrollBar,QScrollArea,QWidgetAction,QDialog,QVBoxLayout,QDialogButtonBox,QPushButton)

CLASSIC_STYLE = '''
QMainWindow, QDialog {background:#ededed; color:#111;}
QMenuBar {background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #fafafa,stop:1 #dedede); border-bottom:1px solid #aaa; padding:1px;}
QMenuBar::item {padding:3px 9px; background:transparent;}
QMenuBar::item:selected, QMenu::item:selected {background:#3875d7;color:white;}
QMenu {background:#f8f8f8;border:1px solid #999;padding:3px;}
QMenu::item {padding:3px 25px 3px 20px;}
QMenu::item:disabled {color:#999;}
QToolBar {background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #fafafa,stop:1 #e1e1e1);border-bottom:1px solid #aaa;spacing:1px;padding:2px;}
QToolButton {border:1px solid transparent;border-radius:2px;padding:2px;}
QToolButton:hover {border:1px solid #999;background:#f7f7f7;}
QToolButton:checked,QToolButton:pressed {border:1px solid #7f7f7f;background:#c6c6c6;}
QToolButton::menu-indicator {width:5px;height:5px;subcontrol-position:bottom right;}
QDockWidget {font-size:10px;}
QDockWidget::title {background:#ddd;border-bottom:1px solid #aaa;padding:3px;}
QComboBox,QLineEdit,QDoubleSpinBox {background:white;border:1px solid #aaa;border-radius:2px;min-height:18px;}
QStatusBar {background:#e8e8e8;border-top:1px solid #aaa;font-size:10px;}
QPushButton {padding:3px 12px;}
'''

def install(editor, legacy, tool_icon):
    # The application appearance controller owns all control colors.
    editor.setFont(QFont('Arial',9))
    editor.removeToolBar(legacy);legacy.hide();editor.legacy_toolbar=legacy
    menus=editor.menus
    view=menus['View'];view.removeAction(legacy.toggleViewAction())
    editor.toolbars={}
    def toolbar(name,break_before=False):
        if break_before:editor.addToolBarBreak()
        t=QToolBar(name,editor);t.setObjectName(name.replace(' ','')+'Toolbar');t.setIconSize(QSize(18,18));t.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        editor.addToolBar(t);view.addAction(t.toggleViewAction());editor.toolbars[name]=t;return t
    general=toolbar('General')
    for key in ['new','open','save','print',None,'cut','copy','paste',None,'undo','redo']:
        if key is None:general.addSeparator();continue
        a=editor.actions[key];a.setIcon(tool_icon(key));general.addAction(a)
    general.addSeparator();editor.zoom_combo=QComboBox();editor.zoom_combo.setEditable(True);editor.zoom_combo.addItems(['25%','33%','50%','67%','75%','100%','125%','150%','200%','300%','400%']);editor.zoom_combo.setCurrentText('100%');general.addWidget(editor.zoom_combo);editor.zoom_combo.setFixedWidth(75)
    def change_zoom():
        try:value=float(editor.zoom_combo.currentText().rstrip('%'))
        except ValueError:return
        if 10<=value<=999:editor.js('zoomTo('+str(value/100)+');')
    editor.zoom_combo.activated.connect(lambda index:change_zoom());editor.zoom_combo.lineEdit().editingFinished.connect(change_zoom)
    for key in ['zoomIn','zoomOut']:
        a=editor.add_action(menus['View'],key,'Magnify' if key=='zoomIn' else 'Reduce',lambda key=key:editor.command(key));a.setIcon(tool_icon(key));general.addAction(a)
    general.addSeparator()
    for key in ['validate','cleanup']:
        editor.actions[key].setIcon(tool_icon(key));general.addAction(editor.actions[key])
    obj=toolbar('Object')
    for key in ['group','ungroup']:
        editor.actions[key].setIcon(tool_icon(key));obj.addAction(editor.actions[key])
    obj.addSeparator()
    for key,label in [('front','Bring to Front'),('back','Send to Back')]:
        a=QAction(tool_icon(key),label,editor);a.setEnabled(False);a.setToolTip(label+' — not implemented');obj.addAction(a)
    obj.addSeparator()
    for key,label in [('align_left','⊢'),('align_horizontal','↔'),('align_right','⊣'),('align_top','⊤'),('align_vertical','↕'),('align_bottom','⊥'),('distribute_x','⋯'),('distribute_y','⋮'),('centerPage','⊕')]:
        a=editor.actions[key];a.setIcon(tool_icon(key));obj.addAction(a)
    style=toolbar('Text Style',True)
    editor.font_combo=QFontComboBox();editor.font_combo.setCurrentFont(QFont('Arial'));editor.font_combo.setMaximumWidth(170)
    editor.font_combo.currentFontChanged.connect(lambda font:editor.js('setTextStyle('+json.dumps({'font':font.family()})+');'))
    style.addWidget(editor.font_combo)
    size=QComboBox();size.setEditable(True);size.addItems(['8','9','10','12','14','18','24','36']);size.setCurrentText('12');size.setFixedWidth(52)
    def set_size(text):
        try:value=float(text)
        except ValueError:return
        if 4<=value<=96:editor.js('setTextStyle('+json.dumps({'size':value*1.5})+');')
    size.currentTextChanged.connect(set_size);style.addWidget(size);editor.text_size_combo=size
    style.addSeparator();text_menu=menus['Text']
    for key,label in [('textLeft','Left'),('textCenter','Center'),('textRight','Right'),('textJustify','Justify')]:
        a=editor.add_action(text_menu,key,label,lambda value=label.lower():editor.js('paragraphStyle('+json.dumps({'alignment':value})+');'));a.setIcon(tool_icon(key));style.addAction(a)
    style.addSeparator()
    for key,label,prop,value in [('bold','B','bold',True),('italic','I','italic',True),('underline','U','underline',True),('plain','P','plain',True)]:
        a=editor.add_action(text_menu,key,{'bold':'Bold','italic':'Italic','underline':'Underline','plain':'Plain'}[key],lambda prop=prop,value=value:editor.js('setTextStyle('+json.dumps({prop:value})+');'))
        if key!='plain':
            a.triggered.disconnect()
            a.setCheckable(True)
            a.triggered.connect(lambda checked,prop=prop:editor.js('setTextStyle('+json.dumps({prop:checked})+');'))
        if key in ('bold','italic','underline'):a.setShortcut({'bold':'Ctrl+B','italic':'Ctrl+I','underline':'Ctrl+U'}[key])
        a.setIcon(tool_icon(key));style.addAction(a)
    editor.add_action(text_menu,'formula','Formula',lambda:editor.js('formatFormula();'))
    editor.add_action(text_menu,'lineSpacing','Line Spacing…',editor.text_line_spacing)
    colors=editor.menuBar().addMenu('Color')
    for key,label in [('subscript','Subscript'),('superscript','Superscript')]:
        a=editor.add_action(text_menu,key,label,lambda value='sub' if key=='subscript' else 'super':editor.js('setTextStyle('+json.dumps({'script':value})+');'));a.setIcon(tool_icon(key));style.addAction(a)
    color=QToolButton();color.setIcon(tool_icon('color'));color.setToolTip('Text Color');cm=QMenu(color)
    for name,hexval in [('Black','#000000'),('Red','#cc0000'),('Blue','#0033cc'),('Green','#008000'),('Gray','#666666')]:
        a=editor.add_action(colors,'color_'+name,name,lambda v=hexval:editor.js('setTextStyle('+json.dumps({'color':v})+');'));cm.addAction(a)
    more=editor.add_action(colors,'customTextColor','More Colors…',editor.choose_text_color);cm.addAction(more)
    color.setMenu(cm);color.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup);style.addWidget(color)
    # Keep color menu before Help, matching a desktop drawing application's order.
    editor.menuBar().removeAction(colors.menuAction());editor.menuBar().insertMenu(menus['Help'].menuAction(),colors)
    tools=QWidget();layout=QGridLayout(tools);layout.setContentsMargins(2,2,2,2);layout.setSpacing(0)
    editor.tool_buttons={};editor.family_buttons={};editor.unavailable_actions=[]
    def unavailable(menu,key,label):
        a=QAction(label,editor);a.setEnabled(False);a.setToolTip('Not implemented in ErezDraw');menu.addAction(a);editor.actions[key]=a;editor.unavailable_actions.append(a);return a
    families=[
      ('lasso','Lasso',None),('select','Marquee',None),
      ('trackball','Structure Perspective',None),('fragment','Mass Fragmentation',None),
      ('single','Solid Bond',None),('erase','Eraser',None),
      ('double','Multiple Bonds',[('double','Double Bond'),('triple','Triple Bond'),('boldBond','Bold Bond'),('crossBond','Crossed Double Bond')]),('text','Text / Atom Labels',None),
      ('dashed','Dashed Bond',None),('pen','Pen',None),
      ('hashed','Hashed Bond',None),('arrow', 'Arrows', [('arrow', 'Full head — Straight'), ('arcArrow90', 'Full head — 90°'), ('arcArrow120', 'Full head — 120°'), ('arcArrow180', 'Full head — 180°'), ('arcArrow270', 'Full head — 270°'), ('straightFishhook', 'Half head — Straight'), ('arcFishhook90', 'Half head — 90°'), ('arcFishhook120', 'Half head — 120°'), ('arcFishhook180', 'Half head — 180°'), ('arcFishhook270', 'Half head — 270°'), ('curvedArrow', 'Curved Full Head'), ('fishhook', 'Curved Half Head'), ('equilibrium', 'Equilibrium — Equal'), ('equilibriumRight', 'Equilibrium — Forward Favored'), ('equilibriumLeft', 'Equilibrium — Reverse Favored'), ('resonance', 'Resonance'), ('twoWay', 'Opposing Full Heads'), ('retrosynthetic', 'Retrosynthetic'), ('noGo', 'No-Go'), ('dashedArrow', 'Dashed Arrow'), ('solidArrow', 'Solid Head'), ('hollowArrow', 'Hollow Head'), ('boldArrow', 'Bold Arrow')]),
      ('hash','Hashed Wedge',None),('orbital_p_phase','Orbitals',[(f'orbital_{k}_{f}',f'{k} — {f}') for k in ('s','p','dxy','dz2','hybrid') for f in ('outline','gray','phase')]),
      ('boldBond','Bold Bond',None),('elements','Drawing Elements',[('elements','Rectangle'),('ellipse','Ellipse')]),
      ('wedge','Solid Wedge',None),('bracket','Brackets',None),
      ('hollowWedge','Hollow Wedge',None),('symbol','Chemical Symbols',[('chargeUp','Positive Charge'),('chargeDown','Negative Charge'),('radical','Radical'),('lonePair','Lone Pair')]),
      ('wavy','Wavy Bond',None),
      ('table','Table',None),('ligands','Organometallic Ligands',None),
      ('chain','Acyclic Chain',None),('templates','Templates',[(f'ring{n}',f'{n}-Membered Ring') for n in range(3,9)]+[('benzene','Benzene'),('cpAnion','Cp Ring / Centroid'),('coord','Coordination Bond')]),
      ('ring3','3-Membered Ring',None),('ring4','4-Membered Ring',None),('ring5','5-Membered Ring',None),('ring6','6-Membered Ring',None),
      ('ring7','7-Membered Ring',None),('ring8','8-Membered Ring',None),('chair','Cyclohexane Chair',None),('chair2','Cyclohexane Chair (Alternative)',None),
      ('cyclopentadiene','Cyclopentadiene',None),('benzene','Benzene',None),('cpAnion','Cp Rings / Centroid Attachment',[('cpAnion','Cp Ring — Face On'),('cpTilt30','Cp Perspective — 30° Tilt'),('cpTilt60','Cp Perspective — 60° Tilt'),('cpTilt75','Cp Perspective — 75° Tilt')])]
    for i,(key,label,options) in enumerate(families):
        b=QToolButton();b.setFixedSize(29,35);b.setIconSize(QSize(23,23));b.setCheckable(True);b.setToolTip(label)
        b.setIcon(tool_icon(key))
        if key=='fragment':b.clicked.connect(lambda checked=False:editor.mass_fragmentation())
        elif key=='ligands':b.clicked.connect(lambda checked=False:editor.ligand_dock.setVisible(not editor.ligand_dock.isVisible()))
        elif key.startswith('missing:'):b.setEnabled(False);b.setToolTip(label+' — not implemented')
        elif options:
            menu=QMenu(b);menu.setTearOffEnabled(True)
            popup=QWidget();cells=QGridLayout(popup);cells.setContentsMargins(3,3,3,3);cells.setSpacing(1)
            for j,(variant,name) in enumerate(options):
                a=QAction(tool_icon(variant),name,editor)
                if variant.startswith('missing:'):
                    a.setEnabled(False);a.setToolTip(name+' — not implemented');editor.unavailable_actions.append(a)
                else:
                    def choose(checked=False,variant=variant,b=b,a=a,key=key,menu=menu):
                        editor.set_tool(variant);b.setIcon(a.icon());editor.family_buttons[key]=variant
                        menu.hide()
                    a.triggered.connect(choose)
                child=QToolButton();child.setDefaultAction(a);child.setFixedSize(30,30);child.setIconSize(QSize(24,24));cells.addWidget(child,j//(5 if key=='arrow' else 4),j%(5 if key=='arrow' else 4))
            container=QWidgetAction(menu);container.setDefaultWidget(popup);menu.addAction(container)
            b.setStyleSheet('QToolButton {padding-bottom:7px;} QToolButton::menu-button {subcontrol-origin:padding; subcontrol-position:bottom center; width:27px; height:7px; border:0;} QToolButton::menu-arrow {width:5px; height:4px;}');b.setMenu(menu);b.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
            b.clicked.connect(lambda checked=False,key=key:editor.set_tool(editor.family_buttons.get(key,'ring6' if key=='templates' else 'chargeUp' if key=='symbol' else key)))
            editor.family_buttons[key]='ring6' if key=='templates' else 'chargeUp' if key=='symbol' else key
        else:b.clicked.connect(lambda checked=False,key=key:editor.set_tool(key))
        layout.addWidget(b,i//2,i%2);editor.tool_buttons[key]=b
    layout.setRowStretch((len(families)+1)//2,1);tools.setFixedWidth(62);scroll=QScrollArea();scroll.setWidget(tools);scroll.setWidgetResizable(True);scroll.setFrameShape(QScrollArea.Shape.NoFrame);scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff);editor.dock.setWidget(scroll);editor.dock.setMinimumWidth(64);editor.dock.setMaximumWidth(76)
    # Reference commands appear unavailable until implemented, never as successful no-ops.
    for menu_name,items in {'File':['New from Stationery…','Save As Stationery…','Page Setup…'],
       'Edit':['Insert Graphic…','Insert Object…'],
       'Object':['Bring to Front','Send to Back','Join'],
       'Text':[]}.items():
        menu=menus[menu_name];menu.addSeparator()
        for label in items:unavailable(menu,'unavailable_'+label,label)
    curves=editor.menuBar().addMenu('Curves');editor.menuBar().removeAction(curves.menuAction());editor.menuBar().insertMenu(colors.menuAction(),curves)
    for label,change in [('Closed',{'closed':True,'heads':'none'}),('Open',{'closed':False}),('Plain',{'fill':'none','dashed':False,'lineWidth':1.7}),('Filled',{'closed':True,'fill':'black','heads':'none'}),('Shaded',{'closed':True,'fill':'gray','heads':'none'}),('Dashed',{'dashed':True}),('Bold',{'lineWidth':3.4}),('Arrow at Start',{'closed':False,'heads':'start'}),('Arrow at End',{'closed':False,'heads':'end'}),('Arrows at Both Ends',{'closed':False,'heads':'both'})]:editor.add_action(curves,'curve_'+label,label,lambda change=change:editor.js('curveCommand('+json.dumps(change)+');'))
    editor.add_action(curves,'curve_Add Point','Add Point',lambda:editor.js('curvePointCommand(false);'))
    editor.add_action(curves,'curve_Delete Point','Delete Point',lambda:editor.js('curvePointCommand(true);'))
    window=editor.menuBar().addMenu('Window');editor.menuBar().removeAction(window.menuAction());editor.menuBar().insertMenu(menus['Help'].menuAction(),window)
    a=QAction('Untitled structure',editor);a.setCheckable(True);a.setChecked(True);window.addAction(a);editor.document_action=a
    # Persistent document scrollbars pan the same SVG coordinate system used by drawing.
    viewport=QWidget();page_layout=QGridLayout(viewport);page_layout.setContentsMargins(0,0,0,0);page_layout.setSpacing(0)
    editor.takeCentralWidget();page_layout.addWidget(editor.view,0,0)
    editor.hscroll=QScrollBar(Qt.Orientation.Horizontal);editor.vscroll=QScrollBar(Qt.Orientation.Vertical)
    editor.hscroll.setRange(-2000,2000);editor.vscroll.setRange(-2000,2000)
    editor.hscroll.setPageStep(1000);editor.vscroll.setPageStep(700)
    editor.hscroll.valueChanged.connect(lambda v:editor.js('center.x='+str(500+v)+';render();'))
    editor.vscroll.valueChanged.connect(lambda v:editor.js('center.y='+str(350+v)+';render();'))
    page_layout.addWidget(editor.vscroll,0,1);page_layout.addWidget(editor.hscroll,1,0);page_layout.addWidget(QLabel(''),1,1)
    editor.setCentralWidget(viewport)
    # Native context menus use the same command objects and capability states.
    editor.view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    def context(pos):
        m=QMenu(editor)
        for key in ['undo','redo','cut','copy','paste','delete']:m.addAction(editor.actions[key])
        m.addSeparator()
        for key in ['rotate','scaleObjects','flip','flipVertical']:m.addAction(editor.actions[key])
        for a in menus['Object'].actions():
            if a.menu() and a.text() in ['Align','Distribute']:m.addMenu(a.menu())
        m.exec(editor.view.mapToGlobal(pos))
    editor.view.customContextMenuRequested.connect(context)
