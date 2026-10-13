"""Atomic native-document writes: never truncate the last saved drawing on failure."""
import json
import os
import tempfile
from pathlib import Path


def _umask():
    mask = os.umask(0)
    os.umask(mask)
    return mask


def write_drawing(path, drawing):
    target = Path(path)
    data = json.dumps(drawing, indent=2, ensure_ascii=False, allow_nan=False) + '\n'
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n', dir=target.parent, prefix='.'+target.name+'.', suffix='.tmp', delete=False) as f:
            temporary = Path(f.name)
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        # mkstemp files are private (0600); keep the permissions a normal save would have.
        try:
            mode = os.stat(target).st_mode & 0o7777
        except FileNotFoundError:
            mode = 0o666 & ~_umask()
        os.chmod(temporary, mode)
        os.replace(temporary, target)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
