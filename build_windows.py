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
subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--clean','--windowed','--onedir','--name','ErezDraw','--add-data',f'assets{os.pathsep}assets','--add-data',f'COPYING{os.pathsep}.','--add-data',f'THIRD-PARTY-NOTICES.md{os.pathsep}.','--hidden-import','PySide6.QtSvg','--collect-all','rdkit','--exclude-module','PyQt5','--exclude-module','PyQt6','--exclude-module','PySide2','main.py'],cwd=root,check=True)
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
print('Runtime check passed: NumPy ' + data['numpy'] + ', RDKit ' + data['rdkit'])
print('\nBuild complete: '+str(root/'dist'/'ErezDraw'/'ErezDraw.exe'))
print('Keep the entire ErezDraw folder together when copying it to another computer.')

archive = shutil.make_archive(str(root / 'dist' / 'ErezDraw-Windows-x64'), 'zip', root / 'dist', 'ErezDraw')
print('Windows distribution ZIP: ' + archive)
