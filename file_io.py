"""Atomic native-document writes: never truncate the last saved drawing on failure."""
import json
import os
import tempfile
from pathlib import Path


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
        os.replace(temporary, target)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
