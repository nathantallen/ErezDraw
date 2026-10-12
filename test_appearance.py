"""Run with QT_QPA_PLATFORM=offscreen to check native appearance behavior."""
import tempfile
import unittest
from pathlib import Path
from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication, QMenu, QLineEdit, QDialog, QVBoxLayout
from appearance import Appearance


class AppearanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_first_launch_follows_system_and_ignores_changes_when_overridden(self):
        with tempfile.TemporaryDirectory() as folder:
            controller = Appearance(self.app, QSettings(str(Path(folder) / 'fresh.ini'), QSettings.Format.IniFormat))
            self.assertEqual(controller.mode, 'System')
            for scheme, expected in ((Qt.ColorScheme.Dark, '#f3f4f6'),
                                     (Qt.ColorScheme.Light, '#17191c')):
                controller.system_changed(scheme)
                self.assertEqual(self.app.palette().color(QPalette.ColorRole.Text).name(), expected)
            controller.choose('Light')
            controller.system_changed(Qt.ColorScheme.Dark)
            self.assertEqual(self.app.palette().color(QPalette.ColorRole.Text).name(), '#17191c')

    def test_modes_persist_and_controls_use_matching_colors(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / 'settings.ini')
            controller = Appearance(self.app, QSettings(path, QSettings.Format.IniFormat))
            menu = QMenu()
            controller.install_menu(menu)
            dialog = QDialog()
            layout = QVBoxLayout(dialog)
            field = QLineEdit('Readable')
            layout.addWidget(field)
            for mode in ('Dark', 'Light', 'System'):
                controller.actions[mode].trigger()
                self.app.processEvents()
                dark = mode == 'Dark' or (mode == 'System' and self.app.styleHints().colorScheme() == Qt.ColorScheme.Dark)
                self.assertEqual(field.palette().color(QPalette.ColorRole.Text).name(), '#f3f4f6' if dark else '#17191c')
                self.assertEqual(field.palette().color(QPalette.ColorRole.Base).name(), '#1e2024' if dark else '#ffffff')
                self.assertEqual(QSettings(path, QSettings.Format.IniFormat).value('appearance'), mode)
                self.assertEqual(sum(a.isChecked() for a in controller.actions.values()), 1)
            controller.choose('Dark')
            restored = Appearance(self.app, QSettings(path, QSettings.Format.IniFormat))
            self.assertEqual(restored.mode, 'Dark')
            restored.choose('System')
            restored.system_changed(self.app.styleHints().colorScheme())
            self.assertEqual(restored.mode, 'System')


if __name__ == '__main__':
    unittest.main()
