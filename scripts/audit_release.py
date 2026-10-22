"""Flag common private-data patterns in Git-tracked kit files. Review content too."""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    'email address': re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'),
    'personal home path': re.compile(r'/(?:Users|home)/[^\s/]+/'),
    'private key': re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
    'GitHub token': re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})'),
}

def audit():
    result = subprocess.run(['git', 'ls-files', '-z'], cwd=ROOT, check=True, capture_output=True)
    paths = [p for p in result.stdout.decode().split('\0') if p]
    findings = []
    for relative in paths:
        path = ROOT / relative
        if path.is_symlink():
            findings.append((relative, 'symlink requires review'))
            continue
        try:
            text = path.read_text(encoding='utf-8')
        except UnicodeError:
            findings.append((relative, 'binary file requires review'))
            continue
        for label, pattern in PATTERNS.items():
            if pattern.search(text):
                findings.append((relative, label))
    return paths, findings

if __name__ == '__main__':
    paths, findings = audit()
    for path, reason in findings:
        print(f'{path}: {reason}')
    print(f'Checked {len(paths)} tracked files, {len(findings)} findings. This cannot detect all identifying narratives or secrets.')
    raise SystemExit(bool(findings))
