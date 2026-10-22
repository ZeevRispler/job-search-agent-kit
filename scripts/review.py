"""Print due actions and unresolved ownership without external actions."""
import argparse
from datetime import date
from pathlib import Path
from check_workspace import check

def review(root, today=None):
    today = today or date.today()
    roles, practice = check(root)
    lines = [f'Review as of {today.isoformat()}']
    for row in roles:
        active = row['decision'] not in {'declined', 'deferred'} and row['stage'] not in {'rejected', 'withdrawn', 'closed'}
        if not active:
            continue
        if row['ownership'] == 'unresolved':
            lines.append(f'{row["id"]}: resolve application ownership before direct application')
        if row['due_on'] and date.fromisoformat(row['due_on']) <= today:
            lines.append(f'{row["id"]}: due {row["due_on"]}: {row["next_action"] or "clarify next action"}')
    for row in practice:
        if row['status'] not in {'deferred', 'void'} and row['review_on'] and date.fromisoformat(row['review_on']) <= today:
            lines.append(f'{row["id"]}: practice review due {row["review_on"]}: {row["topic"]}')
    if len(lines) == 1:
        lines.append('No due ledger actions or unresolved active ownership found. Company triggers and interview notes require agent review.')
    return '\n'.join(lines)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('workspace', type=Path)
    parser.add_argument('--as-of', type=date.fromisoformat, help='ISO date in your local timezone')
    args = parser.parse_args()
    try:
        print(review(args.workspace, args.as_of))
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Review failed: {exc}\n')
