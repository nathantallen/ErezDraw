"""Create a rebuildable source archive alongside the native Mac app."""
from pathlib import Path
import json
import zipfile
root=Path(__file__).resolve().parent
manifest=json.loads((root/'macos-source.json').read_text())
files=set(manifest['files'])
files.update(['assets/app-icons/ErezDraw.ico','desktop_keyboard.py','keyboard_shortcuts.py','assets/shortcuts.js','KEYBOARD-SHORTCUTS.md','test_keyboard_shortcuts.py'])
files.update(['macos_app.py','appearance.py','startup_check.py','build_macos.py','package_macos_source.py','requirements.txt','requirements-macos.txt','Build-macOS.command','Run-macOS.command','macos-source.json','MACOS.md','README.md','test_macos_app.py','test_chemistry.py','test_structure_ops.py','test_chemdraw_io.py','verify-charges.cjs','verify-hover.cjs','examples/Cp3Y_centroid.chemjson','Dockerfile','compose.yaml','.dockerignore'])
files.update(str(p.relative_to(root)) for p in (root/'macos').rglob('*') if p.is_file())
with zipfile.ZipFile(root/'dist/ErezDraw-macOS-Source.zip','w',zipfile.ZIP_DEFLATED) as z:
    for name in sorted(files):z.write(root/name,'ErezDraw-macOS-Source/'+name)
print('Source archive: '+str(root/'dist/ErezDraw-macOS-Source.zip'))
