"""Persistent application appearance; document and spectrum colors stay independent."""
from PySide6.QtCore import QObject, QSettings, Qt
from PySide6.QtGui import QAction, QActionGroup, QColor, QPalette


class Appearance(QObject):
    def __init__(self, app, settings=None):
        super().__init__(app)
        self.app = app
        self.settings = settings if settings is not None else QSettings()
        self.mode = str(self.settings.value('appearance', 'System'))
        if self.mode not in ('System', 'Light', 'Dark'):
            self.mode = 'System'
        # Fusion respects explicit text and control palettes on Windows and macOS.
        app.setStyle('Fusion')
        app.styleHints().colorSchemeChanged.connect(self.system_changed)
        self.apply()

    def system_changed(self, scheme):
        if self.mode == 'System':
            self.apply(scheme)

    def choose(self, mode):
        self.mode = mode
        self.settings.setValue('appearance', mode)
        self.settings.sync()
        self.apply()

    def install_menu(self, menu):
        submenu = menu.addMenu('Appearance')
        self.group = QActionGroup(self)
        self.group.setExclusive(True)
        self.actions = {}
        for mode in ('System', 'Light', 'Dark'):
            action = QAction(mode, self.group)
            action.setCheckable(True)
            action.setChecked(self.mode == mode)
            action.triggered.connect(lambda checked=False, mode=mode: self.choose(mode))
            submenu.addAction(action)
            self.actions[mode] = action

    def apply(self, scheme=None):
        if scheme is None:
            scheme = self.app.styleHints().colorScheme()
        dark = self.mode == 'Dark' or (self.mode == 'System' and
                scheme == Qt.ColorScheme.Dark)
        bg, base, text, button, border, disabled = (
            ('#292b30', '#1e2024', '#f3f4f6', '#383b42', '#747983', '#a3a8b2') if dark else
            ('#ededed', '#ffffff', '#17191c', '#e4e6e9', '#858b94', '#606670'))
        palette = QPalette()
        roles = {'Window': bg, 'WindowText': text, 'Base': base,
                 'AlternateBase': button, 'Text': text, 'Button': button,
                 'ButtonText': text, 'ToolTipBase': base, 'ToolTipText': text,
                 'Highlight': '#245fba', 'HighlightedText': '#ffffff',
                 'PlaceholderText': disabled, 'Link': '#80b7ff' if dark else '#1657a5',
                 'Light': border, 'Midlight': button, 'Mid': border,
                 'Dark': border, 'Shadow': '#111111', 'BrightText': '#ffffff'}
        for role, color in roles.items():
            palette.setColor(getattr(QPalette.ColorRole, role), QColor(color))
        for role in ('WindowText', 'Text', 'ButtonText', 'PlaceholderText'):
            palette.setColor(QPalette.ColorGroup.Disabled,
                             getattr(QPalette.ColorRole, role), QColor(disabled))
        self.app.setPalette(palette)
        self.app.setStyleSheet(f'''
            QWidget {{background-color:{bg}; color:{text};}}
            QLineEdit, QTextEdit, QPlainTextEdit, QAbstractSpinBox, QComboBox,
            QAbstractItemView {{background-color:{base}; color:{text};
                              selection-background-color:#245fba; selection-color:white;}}
            QAbstractItemView::item:selected {{background:#245fba; color:white;}}
            QPushButton, QHeaderView::section {{background-color:{button}; color:{text};}}
            QMenu, QMenuBar {{background-color:{bg}; color:{text};}}
            QMenu::item:selected, QMenuBar::item:selected {{background:#245fba; color:white;}}
            QWidget:disabled {{color:{disabled};}}
            QToolBar {{spacing:1px; background:{bg}; border-bottom:1px solid {border};}}
            QDockWidget::title {{background:{button}; color:{text}; padding:4px;}}
            QToolButton {{padding:2px; color:#17191c; background:#f4f5f7;
                          border:1px solid #858b94; border-radius:2px;}}
            QToolButton:hover {{background:#dfebff; border-color:#245fba;}}
            QToolButton:checked, QToolButton:pressed {{background:#b4cef5; border:2px solid #245fba;}}
            QToolButton:disabled {{background:#cdd0d5; color:#606670;}}
            QToolTip {{background:{base}; color:{text}; border:1px solid {border};}}
            QSplitter::handle {{background:{border};}}
            QSplitter::handle:hover {{background:#80b7ff;}}
        ''')
