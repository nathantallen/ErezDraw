import json,os,unittest
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication,QToolButton,QWidget
from PySide6.QtCore import Qt,QPoint
from PySide6.QtTest import QTest
from web.desktop_api import catalog
from template_ui import install_template_menu,TemplateCell

app=QApplication.instance() or QApplication([])
class Host:
    def __init__(self):self.calls=[];self.view=QWidget()
    def js(self,code):self.calls.append(code)
    def set_tool(self,tool):self.calls.append('tool:'+tool)

class TemplatePickerTests(unittest.TestCase):
    def setUp(self):
        self.host=Host();self.button=QToolButton();self.menu=install_template_menu(self.host,self.button)
    def tearDown(self):
        for action in self.menu.actions():
            if action.menu():action.menu().hide()
        self.menu.hide();self.button.close();self.host.view.close()
    def test_catalog_covers_existing_templates(self):
        groups=catalog()['templates'];items=[x for g in groups for x in g['items']]
        self.assertEqual(sum(x['kind']=='glassware' for x in items),68)
        self.assertEqual(sum(x['kind']=='ligand' for x in items),37)
        self.assertTrue(any(x.get('tool')=='benzene' for x in items))
        self.assertEqual(self.button.popupMode(),QToolButton.ToolButtonPopupMode.InstantPopup)
    def test_release_without_cell_press_selects_once(self):
        menu=self.menu.actions()[0].menu();cell=next(c for c in menu.findChildren(TemplateCell) if c.item['name']=='Benzene')
        self.menu.popup(QPoint(50,50));menu.popup(QPoint(290,50));app.processEvents()
        self.assertEqual(self.host.calls,[])
        QTest.mouseMove(cell,cell.rect().center());QTest.mouseRelease(cell,Qt.MouseButton.LeftButton,pos=cell.rect().center());app.processEvents()
        self.assertEqual(self.host.calls,['tool:benzene']);self.assertFalse(self.menu.isVisible())
    def test_choose_graphic_template_and_cancel(self):
        target=next(c for a in self.menu.actions() for c in a.menu().findChildren(TemplateCell) if c.item['kind']=='glassware')
        QTest.mouseRelease(target,Qt.MouseButton.LeftButton,pos=target.rect().center())
        self.assertEqual(len(self.host.calls),1);self.assertTrue(self.host.calls[0].startswith('setGlasswareTemplate('))
        self.host.calls=[];self.menu.popup(QPoint(50,50));app.processEvents();QTest.keyClick(self.menu,Qt.Key.Key_Escape);app.processEvents()
        self.assertEqual(self.host.calls,[])
    def test_keyboard_selects_template(self):
        cell=self.menu.actions()[0].menu().findChildren(TemplateCell)[0]
        QTest.keyClick(cell,Qt.Key.Key_Return);self.assertEqual(len(self.host.calls),1)
if __name__=='__main__':unittest.main()
