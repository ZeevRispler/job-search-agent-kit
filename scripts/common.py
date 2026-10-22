"""Shared strict parsing for the canonical Markdown ledgers."""
from datetime import date
from pathlib import Path
import re

ROLE_COLUMNS = 'id employer role board requisition url decision stage route ownership verified_on next_action due_on note'.split()
PRACTICE_COLUMNS = 'id topic status score assistance last_practiced review_on note'.split()
DECISIONS = {'review', 'pursue', 'deferred', 'declined'}
STAGES = {'discovered', 'verified', 'materials-ready', 'submission-reported', 'acknowledged', 'interviewing', 'offer', 'rejected', 'withdrawn', 'closed'}
ROUTES = {'direct', 'recruiter', 'referral', 'unknown'}
OWNERSHIP = {'clear', 'unresolved', 'recruiter-managed', 'referral-pending'}
PRACTICE_STATES = {'prepared', 'in-progress', 'completed', 'studied', 'deferred', 'void'}

def table(path, columns):
    lines = Path(path).read_text(encoding='utf-8').splitlines()
    header = None
    rows = []
    for number, line in enumerate(lines, 1):
        if not line.strip().startswith('|'):
            continue
        cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
        if header is None:
            if cells != columns:
                raise ValueError(f'{path}:{number}: expected columns {columns}')
            header = cells
            continue
        if all(re.fullmatch(r':?-+:?', c) for c in cells):
            continue
        if len(cells) != len(columns):
            raise ValueError(f'{path}:{number}: expected {len(columns)} cells, got {len(cells)}')
        rows.append(dict(zip(columns, cells)))
    if header is None:
        raise ValueError(f'{path}: missing table header')
    return rows

def valid_date(value):
    if value and (not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value) or date.fromisoformat(value).isoformat() != value):
        raise ValueError(f'invalid ISO date: {value}')

def note_path(root, value):
    if not value:
        raise ValueError('note path is required')
    path = (root / value).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('note path escapes workspace')
    if not path.is_file():
        raise ValueError(f'missing note: {value}')
    return path

def load(root):
    root = Path(root).resolve()
    roles = table(root / 'Job Tracker.md', ROLE_COLUMNS)
    practice = table(root / 'interviews/Question Tracker.md', PRACTICE_COLUMNS)
    for rows, pattern, dates in [(roles, r'J[0-9]{3,}', ['verified_on', 'due_on']), (practice, r'Q[0-9]{3,}', ['last_practiced', 'review_on'])]:
        ids = set()
        for row in rows:
            if not re.fullmatch(pattern, row['id']) or row['id'] in ids:
                raise ValueError(f'invalid or duplicate ID: {row["id"]}')
            ids.add(row['id'])
            note_path(root, row['note'])
            for key in dates:
                valid_date(row[key])
    identities = set()
    for row in roles:
        for key, allowed in [('decision', DECISIONS), ('stage', STAGES), ('route', ROUTES), ('ownership', OWNERSHIP)]:
            if row[key] not in allowed:
                raise ValueError(f'{row["id"]}: invalid {key}: {row[key]}')
        if not row['employer'] or not row['role']:
            raise ValueError(f'{row["id"]}: employer and role required')
        identity = tuple(row[k].casefold() for k in ['employer', 'board', 'requisition'])
        if row['board'] and row['requisition']:
            if identity in identities:
                raise ValueError(f'duplicate exact role identity: {row["id"]}')
            identities.add(identity)
    for row in practice:
        if row['status'] not in PRACTICE_STATES:
            raise ValueError(f'{row["id"]}: invalid practice status')
        if row['score'] and (row['score'] not in {'0', '1', '2', '3'} or row['status'] != 'completed'):
            raise ValueError(f'{row["id"]}: score must be 0–3 on a completed attempt only')
        if row['score'] and (not row['last_practiced'] or not row['assistance']):
            raise ValueError(f'{row["id"]}: scored attempt needs practice date and assistance record')
    return roles, practice
