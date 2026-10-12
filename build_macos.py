"""Build and check an Apple-silicon app from the deployed Docker source."""
import json
import platform
import subprocess
import sys
import shutil
import tempfile
import time
from pathlib import Path

root=Path(__file__).resolve().parent
if sys.platform!='darwin':raise SystemExit('Build the macOS application on a Mac; cross-building is unsupported.')
if platform.machine()!='arm64' or sys.version_info[:2]!=(3,12):raise SystemExit('Use native Apple-silicon Python 3.12, without Rosetta.')
(root/'dist').mkdir(exist_ok=True)
(root/'build').mkdir(exist_ok=True)
# Build outside synced workspace metadata. In particular, do not recursively
# delete a previous framework tree through a file-provider-backed directory.
with tempfile.TemporaryDirectory(prefix='erezdraw-native-build-') as staging:
    staging=Path(staging)
    command=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--windowed','--onedir','--name','ErezDraw','--target-arch','arm64','--osx-bundle-identifier','com.erezdraw.editor','--distpath',str(staging/'dist'),'--workpath',str(staging/'work'),'--collect-all','rdkit','--hidden-import','PySide6.QtSvg','--hidden-import','startup_check','--exclude-module','PyQt5','--exclude-module','PyQt6','--exclude-module','PySide2']
    for resource in ('assets','web','macos','macos-source.json','COPYING','THIRD-PARTY-NOTICES.md'):
        command.extend(['--add-data',str(root/resource)+':'+(resource if resource in ('assets','web','macos') else '.')])
    command.append(str(root/'macos_app.py'))
    subprocess.run(command,cwd=root,check=True)
    clean=staging/'ErezDraw.app'
    subprocess.run(['/usr/bin/ditto','--norsrc','--noextattr',str(staging/'dist/ErezDraw.app'),str(clean)],check=True)
    versions=clean/'Contents/Frameworks/PySide6/Qt/lib/QtWebEngineCore.framework/Versions'
    misplaced=versions/'Resources'
    if (misplaced/'Resources').is_dir():
        shutil.copytree(misplaced/'Resources',versions/'A/Resources',dirs_exist_ok=True)
        if (misplaced/'Helpers').is_dir():shutil.copytree(misplaced/'Helpers',versions/'A/Helpers',dirs_exist_ok=True)
        shutil.rmtree(misplaced)
    subprocess.run(['codesign','--force','--deep','--sign','-',str(clean)],check=True)
    subprocess.run(['codesign','--verify','--deep','--strict',str(clean)],check=True)
    report=root/'build/macos-startup-check.json'
    report.unlink(missing_ok=True)
    subprocess.run([str(clean/'Contents/MacOS/ErezDraw'),'--self-test',str(report)],timeout=90,check=True)
    if not report.exists() or json.loads(report.read_text()).get('status')!='passed':raise SystemExit('The packaged application did not pass its native runtime check.')
    archive=root/'dist/ErezDraw-macOS.zip'
    temporary_archive=staging/'ErezDraw-macOS.zip'
    subprocess.run(['/usr/bin/ditto','-c','-k','--keepParent',str(clean),str(temporary_archive)],check=True)
    # Verify the archive users will receive, including nested framework signatures.
    verification=staging/'verify'
    subprocess.run(['/usr/bin/ditto','-x','-k',str(temporary_archive),str(verification)],check=True)
    subprocess.run(['codesign','--verify','--deep','--strict',str(verification/'ErezDraw.app')],check=True)
    shutil.copyfile(temporary_archive,archive)
    bundle=root/'dist/ErezDraw.app'
    if bundle.exists():
        previous=root/'build'/('previous-macos-'+str(time.time_ns())+'.app')
        bundle.rename(previous)
    subprocess.run(['/usr/bin/ditto','--norsrc','--noextattr',str(clean),str(bundle)],check=True)
print('Ready: '+str(root/'dist/ErezDraw.app'))
print('ZIP verified: '+str(root/'dist/ErezDraw-macOS.zip'))
print('Apple silicon; locally signed, not notarized for external distribution.')
