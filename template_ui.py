"""Press/hold, hover category, release on an icon to select a template."""
import json
from PySide6.QtCore import Qt,QSize,QByteArray
from PySide6.QtGui import QIcon,QPixmap,QPainter
from PySide6.QtWidgets import QMenu,QWidget,QGridLayout,QToolButton,QWidgetAction,QScrollArea


class TemplateCell(QToolButton):
    def __init__(self, item, choose, parent=None):
        super().__init__(parent);self.item=item;self.choose=choose
        self.setObjectName('TemplateCell');self.setText(item['name']);self.setToolTip(item['name'])
        self.setAccessibleName(item['name']);self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        source=QPixmap();source.loadFromData(QByteArray(item['svg'].encode()),'SVG');pixmap=QPixmap(source.size());pixmap.fill(Qt.GlobalColor.white);painter=QPainter(pixmap);painter.drawPixmap(0,0,source);painter.end();self.setIcon(QIcon(pixmap));self.setIconSize(QSize(90,64));self.setFixedSize(125,100);self.setMouseTracking(True)
        # A release may arrive after the press occurred on the Templates button.
        # Native menu tracking must not require a second click on this cell.
    def mouseReleaseEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton:self.choose(self.item);event.accept()
        else:super().mouseReleaseEvent(event)
    def keyPressEvent(self,event):
        if event.key() in (Qt.Key.Key_Return,Qt.Key.Key_Enter,Qt.Key.Key_Space):self.choose(self.item);event.accept()
        else:super().keyPressEvent(event)


class TemplatePaletteMenu(QMenu):
    def mouseReleaseEvent(self,event):
        child=self.childAt(event.position().toPoint())
        while child is not None and child is not self:
            if isinstance(child,TemplateCell):
                if event.button()==Qt.MouseButton.LeftButton:child.choose(child.item);event.accept();return
                break
            child=child.parentWidget()
        super().mouseReleaseEvent(event)


def install_template_menu(editor,button):
    from web.desktop_api import catalog
    menu=QMenu(button);menu.setObjectName('TemplateCategories');editor.template_menu=menu
    def choose(item):
        # Close the complete cascade before returning focus to the canvas.
        for action in menu.actions():
            if action.menu():action.menu().hide()
        menu.hide();editor.active_template=item['name'];button.setToolTip('Templates — '+item['name'])
        if item['kind']=='tool':editor.set_tool(item['tool'])
        else:editor.js(('setGlasswareTemplate' if item['kind']=='glassware' else 'setLigandTemplate')+'('+json.dumps(item['template'])+');')
        editor.view.setFocus()
    for category in catalog()['templates']:
        sub=TemplatePaletteMenu(category['name'],menu);sub.setObjectName('TemplatePalette');menu.addMenu(sub)
        content=QWidget();grid=QGridLayout(content);grid.setContentsMargins(4,4,4,4)
        for i,item in enumerate(category['items']):grid.addWidget(TemplateCell(item,choose,content),i//3,i%3)
        scroll=QScrollArea();scroll.setWidget(content);scroll.setWidgetResizable(True);scroll.setFixedSize(395,min(430,((len(category['items'])+2)//3)*106+12))
        action=QWidgetAction(sub);action.setDefaultWidget(scroll);sub.addAction(action)
    button.setMenu(menu);button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
    return menu
