"""Atomically rebuild a private SQLite index from validated Markdown."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import os
import sqlite3
import tempfile
from common import ROLE_COLUMNS, PRACTICE_COLUMNS
from check_workspace import check

def build(root):
    root = Path(root).resolve()
    roles, practice = check(root)
    folder = root / 'data'
    folder.mkdir(exist_ok=True)
    destination = folder / 'index.sqlite'
    fd, temporary = tempfile.mkstemp(prefix='index-', suffix='.sqlite', dir=folder)
    os.close(fd)
    try:
        with sqlite3.connect(temporary) as db:
            for name, columns, rows in [('roles', ROLE_COLUMNS, roles), ('practice', PRACTICE_COLUMNS, practice)]:
                fields = ', '.join('"'+c+'" TEXT'+(' PRIMARY KEY' if c == 'id' else '') for c in columns)
                db.execute(f'CREATE TABLE {name} ({fields})')
                placeholders = ','.join('?' for _ in columns)
                db.executemany(f'INSERT INTO {name} VALUES ({placeholders})', [[row[c] for c in columns] for row in rows])
            db.execute("CREATE UNIQUE INDEX role_identity ON roles(lower(employer), lower(board), lower(requisition)) WHERE board <> '' AND requisition <> ''")
            db.execute('CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT)')
            db.execute('INSERT INTO metadata VALUES (?, ?)', ('rebuilt_at_utc', datetime.now(timezone.utc).isoformat()))
        os.replace(temporary, destination)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return destination

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('workspace', type=Path)
    args = parser.parse_args()
    try:
        print(f'Rebuilt derived index: {build(args.workspace)}')
    except (ValueError, OSError, sqlite3.Error) as exc:
        parser.exit(1, f'Index build failed: {exc}\n')
