"""Menu shortcut bindings from ChemDraw 17 manual, chapter 5.
Qt maps the logical Ctrl modifier to Command on macOS.
"""
from PySide6.QtGui import QKeySequence

MENU_SHORTCUTS = {
 'new':'Ctrl+N','open':'Ctrl+O','save':'Ctrl+S','saveas':'Ctrl+Shift+S',
 'print':'Ctrl+P','pageSetup':'Ctrl+Shift+P','closeDocument':'Ctrl+W',
 'undo':'Ctrl+Z','redo':'Ctrl+Shift+Z','cut':'Ctrl+X','copy':'Ctrl+C','paste':'Ctrl+V','selectAll':'Ctrl+A',
 'actual':'F5','fitWindow':'F6','zoomIn':'F7','zoomOut':'F8','rulers':'F11',
 'fixedLengths':'Ctrl+L','fixedAngles':'Ctrl+E','group':'Ctrl+G','ungroup':'Ctrl+Shift+G',
 'flip':'Ctrl+Shift+H','flipVertical':'Ctrl+Shift+V','rotate':'Ctrl+R','scaleObjects':'Ctrl+K',
 'cleanup':'Ctrl+Shift+K','nameToStructure':'Ctrl+Shift+N','structureToName':'Ctrl+Alt+N',
 'align_left':'Ctrl+Alt+Shift+L','align_horizontal':'Ctrl+Alt+Shift+C','align_right':'Ctrl+Alt+Shift+R',
 'align_top':'Ctrl+Alt+Shift+T','align_vertical':'Ctrl+Alt+Shift+M','align_bottom':'Ctrl+Alt+Shift+B',
 'textLeft':'Ctrl+Shift+L','textCenter':'Ctrl+Shift+C','textRight':'Ctrl+Shift+R','textJustify':'Ctrl+Shift+J',
 'plain':'Ctrl+T','bold':'Ctrl+B','italic':'Ctrl+I','underline':'Ctrl+U','formula':'Ctrl+F',
 'subscript':'F9','superscript':'F10','repeatKeyboard':'Ctrl+Y',
}
LABEL_SHORTCUTS={
 'Save As…':'Ctrl+Shift+S','Actual Size':'F5','Fit to Window':'F6','Magnify':'F7','Reduce':'F8',
 'Show Rulers':'F11','Group':'Ctrl+G','Ungroup':'Ctrl+Shift+G','Flip Horizontally':'Ctrl+Shift+H',
 'Flip Vertically':'Ctrl+Shift+V','Rotate…':'Ctrl+R','Scale Objects…':'Ctrl+K',
 'Clean Up Structure…':'Ctrl+Shift+K','Convert Name to Structure…':'Ctrl+Shift+N',
 'Convert Structure to Name…':'Ctrl+Alt+N','Plain':'Ctrl+T','Bold':'Ctrl+B','Italic':'Ctrl+I',
 'Underline':'Ctrl+U','Formula':'Ctrl+F','Subscript':'F9','Superscript':'F10',
 'Align left':'Ctrl+Shift+L','Align center':'Ctrl+Shift+C','Align right':'Ctrl+Shift+R','Align justify':'Ctrl+Shift+J',
 'Align Left':'Ctrl+Alt+Shift+L','Align Horizontal Centers':'Ctrl+Alt+Shift+C','Align Right':'Ctrl+Alt+Shift+R',
 'Align Top':'Ctrl+Alt+Shift+T','Align Vertical Centers':'Ctrl+Alt+Shift+M','Align Bottom':'Ctrl+Alt+Shift+B',
}
def install(editor):
    # Remove the previous validation binding: it belongs to vertical flipping.
    editor.actions['validate'].setShortcut(QKeySequence())
    editor.add_action(editor.menus['File'],'closeDocument','Close',editor.close)
    editor.add_action(editor.menus['File'],'pageSetup','Page Setup…',editor.page_setup)
    editor.add_action(editor.menus['Edit'],'repeatKeyboard','Repeat Keyboard Command',lambda:editor.js("keyboardCommand('repeat',true);"))
    for key in ("flip", "flipVertical"):
        editor.actions[key].triggered.disconnect()
        editor.actions[key].triggered.connect(lambda checked=False, key=key:editor.js("keyboardCommand("+repr(key)+",true);"))
    for key,sequence in MENU_SHORTCUTS.items():
        if key in editor.actions:editor.actions[key].setShortcut(QKeySequence(sequence))
