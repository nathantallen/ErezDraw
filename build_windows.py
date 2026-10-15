"""Run inside the included virtual environment on 64-bit Windows / Python 3.12."""
import os
import platform
import subprocess
import sys
import json
import shutil
from pathlib import Path

root=Path(__file__).resolve().parent
if sys.platform!='win32':
    raise SystemExit('The Windows executable must be built on Windows.')
if sys.version_info[:2]!=(3,12) or platform.architecture()[0]!='64bit':
    raise SystemExit('Use 64-bit Python 3.12 for this build.')
subprocess.run([sys.executable, '-m', 'unittest', 'test_appearance', '-v'], cwd=root, check=True)
subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--clean','--windowed','--onedir','--name','ErezDraw','--icon',str(root/'assets/app-icons/ErezDraw.ico'),'--add-data',f'assets{os.pathsep}assets','--add-data',f'COPYING{os.pathsep}.','--add-data',f'THIRD-PARTY-NOTICES.md{os.pathsep}.','--hidden-import','PySide6.QtSvg','--collect-all','rdkit','--exclude-module','PyQt5','--exclude-module','PyQt6','--exclude-module','PySide2','main.py'],cwd=root,check=True)
report = root / 'build' / 'startup-check.json'
report.unlink(missing_ok=True)
executable = root / 'dist' / 'ErezDraw' / 'ErezDraw.exe'
print('Checking the built executable...', flush=True)
result = subprocess.run([str(executable), '--self-test', str(report)], cwd=executable.parent, timeout=90)
if result.returncode != 0 or not report.exists():
    details = report.read_text(encoding='utf-8') if report.exists() else 'Startup failed before the report could be written.'
    raise SystemExit('Packaged runtime check failed:\n' + details)
data = json.loads(report.read_text(encoding='utf-8'))
if data.get('status') != 'passed':
    raise SystemExit('Packaged runtime check did not pass.')
# Confirm the executable contains the supplied icon payloads, not the PyInstaller default.
import pefile, struct, hashlib
icon=(root/'assets/app-icons/ErezDraw.ico').read_bytes()
count=struct.unpack_from('<H',icon,4)[0]
expected=set()
for i in range(count):
    size,offset=struct.unpack_from('<II',icon,6+16*i+8)
    expected.add(hashlib.sha256(icon[offset:offset+size]).hexdigest())
pe=pefile.PE(str(executable));actual=set();has_group=False
for entry in pe.DIRECTORY_ENTRY_RESOURCE.entries:
    if entry.id==14:has_group=True
    if entry.id!=3:continue
    for image in entry.directory.entries:
        for language in image.directory.entries:
            data=language.data.struct
            actual.add(hashlib.sha256(pe.get_data(data.OffsetToData,data.Size)).hexdigest())
pe.close()
if not has_group or not expected.issubset(actual):raise SystemExit('Executable application icon verification failed.')
print('Verified ErezDraw executable icon at '+str(count)+' sizes.')
print('Runtime check passed: NumPy ' + data['numpy'] + ', RDKit ' + data['rdkit'])
print('\nBuild complete: '+str(root/'dist'/'ErezDraw'/'ErezDraw.exe'))
print('Keep the entire ErezDraw folder together when copying it to another computer.')

# Keep provenance and recipient instructions beside the executable.
(executable.parent / 'BUILD-INFO.txt').write_text('ErezDraw portable Windows x64\nSource commit: '+os.environ.get('GITHUB_SHA','local source build')+'\nNative keyboard transport and runtime self-test passed.\n',encoding='utf-8')
(executable.parent / 'READ-ME-FIRST.txt').write_text('Extract the entire ZIP, then open ErezDraw.exe. Keep the _internal folder beside it. No Python installation is required.\n\nCopy: Ctrl+C. Cut: Ctrl+X. Paste: Ctrl+V. Ctrl-drag duplicates a selection; Shift+Ctrl-drag constrains it to X/Y. One Undo restores a drag-copy.\n\nThis executable is unsigned. Windows may display a publisher warning.\nSee KEYBOARD-SHORTCUTS.md for supported and missing ChemDraw shortcuts.\n',encoding='utf-8')
for name in ('KEYBOARD-SHORTCUTS.md','COPYING','THIRD-PARTY-NOTICES.md'):
    shutil.copy2(root/name,executable.parent/name)

archive = shutil.make_archive(str(root / 'dist' / 'ErezDraw-Windows-x64'), 'zip', root / 'dist', 'ErezDraw')
print('Windows distribution ZIP: ' + archive)
