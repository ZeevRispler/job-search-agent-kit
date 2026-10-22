"""Check ledger shape, dates, identifiers, states, and note references."""
import argparse
from pathlib import Path
from common import load

REQUIRED = ['AGENTS.md', 'INSTRUCTIONS.md', 'CONTEXT.md', 'profile/CANDIDATE.md', 'jobs/Company Search Queue.md', 'Search Log.md', 'interviews/README.md']

def check(root):
    root = Path(root)
    missing = [p for p in REQUIRED if not (root / p).is_file()]
    if missing:
        raise ValueError(f'Missing required files: {missing}')
    return load(root)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('workspace', type=Path)
    args = parser.parse_args()
    try:
        roles, practice = check(args.workspace)
        print(f'Valid: {len(roles)} roles, {len(practice)} practice records. Evidence truth still requires review.')
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Validation failed: {exc}\n')
