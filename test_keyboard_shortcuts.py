import unittest
from keyboard_shortcuts import MENU_SHORTCUTS, LABEL_SHORTCUTS
class ShortcutTests(unittest.TestCase):
    def test_unique_native_bindings(self):
        self.assertEqual(len(MENU_SHORTCUTS.values()),len(set(MENU_SHORTCUTS.values())))
    def test_collision_and_redo(self):
        self.assertEqual(MENU_SHORTCUTS['flipVertical'],'Ctrl+Shift+V')
        self.assertEqual(MENU_SHORTCUTS['redo'],'Ctrl+Shift+Z')
        self.assertEqual(MENU_SHORTCUTS['repeatKeyboard'],'Ctrl+Y')
        self.assertNotIn('validate',MENU_SHORTCUTS)
    def test_macos_menu_bindings(self):
        self.assertEqual(LABEL_SHORTCUTS['Rotate…'],'Ctrl+R')
        self.assertEqual(LABEL_SHORTCUTS['Convert Name to Structure…'],'Ctrl+Shift+N')
