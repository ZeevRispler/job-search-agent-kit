import importlib.util
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from init_workspace import initialize
from check_workspace import check
from build_index import build
from review import review
from datetime import date

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = initialize(Path(self.temp.name) / 'private-search')
    def tearDown(self):
        self.temp.cleanup()
    def add_role(self, ident='J001', req='r1', note='jobs/J001.md'):
        (self.root / note).parent.mkdir(parents=True, exist_ok=True)
        (self.root / note).write_text('# Fictional role\n')
        row = f'| {ident} | Example Employer | Specialist | demo | {req} | https://example.invalid/job | pursue | verified | direct | unresolved | 2030-01-01 | Review evidence | 2030-01-02 | {note} |\n'
        with (self.root / 'Job Tracker.md').open('a') as file:
            file.write(row)
    def test_fresh_workspace(self):
        self.assertEqual(check(self.root), ([], []))
        self.assertTrue((self.root / 'skills/job-search/SKILL.md').is_file())
        self.assertEqual((self.root / '.gitignore').read_text().splitlines()[-1], '*')
    def test_no_overwrite(self):
        sentinel = self.root / 'user.txt'
        sentinel.write_text('preserve')
        with self.assertRaises(FileExistsError):
            initialize(self.root)
        self.assertEqual(sentinel.read_text(), 'preserve')
    def test_index_and_due_review(self):
        self.add_role()
        path = build(self.root)
        with sqlite3.connect(path) as db:
            self.assertEqual(db.execute('SELECT id FROM roles').fetchall(), [('J001',)])
        report = review(self.root, date(2030, 1, 3))
        self.assertIn('resolve application ownership', report)
        self.assertIn('Review evidence', report)
    def test_invalid_input_preserves_index(self):
        self.add_role()
        path = build(self.root)
        before = path.read_bytes()
        with (self.root / 'Job Tracker.md').open('a') as file:
            file.write('| malformed | row |\n')
        with self.assertRaises(ValueError):
            build(self.root)
        self.assertEqual(path.read_bytes(), before)
    def test_duplicate_identity_rejected(self):
        self.add_role()
        self.add_role('J002', note='jobs/J002.md')
        with self.assertRaisesRegex(ValueError, 'duplicate exact role'):
            check(self.root)
    def test_unknown_dates_and_requisitions_allowed(self):
        self.add_role(req='')
        p = self.root / 'Job Tracker.md'
        p.write_text(p.read_text().replace('2030-01-01', '').replace('2030-01-02', ''))
        self.assertEqual(len(check(self.root)[0]), 1)
    def test_invalid_date_rejected(self):
        self.add_role()
        p = self.root / 'Job Tracker.md'
        p.write_text(p.read_text().replace('2030-01-02', '2030-02-30'))
        with self.assertRaises(ValueError):
            check(self.root)
    def test_external_note_rejected(self):
        self.add_role()
        p = self.root / 'Job Tracker.md'
        p.write_text(p.read_text().replace('jobs/J001.md', '../outside.md'))
        with self.assertRaisesRegex(ValueError, 'escapes'):
            check(self.root)
    def test_unattempted_practice_cannot_have_score(self):
        (self.root / 'interviews/exercises/Q001.md').write_text('# Fictional exercise')
        with (self.root / 'interviews/Question Tracker.md').open('a') as file:
            file.write('| Q001 | Topic | prepared | 3 | none | 2030-01-01 | | interviews/exercises/Q001.md |\n')
        with self.assertRaisesRegex(ValueError, 'completed attempt'):
            check(self.root)
    def test_deferred_role_not_surfaced(self):
        self.add_role()
        p = self.root / 'Job Tracker.md'
        p.write_text(p.read_text().replace('| pursue |', '| deferred |'))
        self.assertNotIn('J001:', review(self.root, date(2030, 1, 3)))

if __name__ == '__main__':
    unittest.main()
