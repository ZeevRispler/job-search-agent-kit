"""Create a fresh private workspace without overwriting an existing path."""
import argparse
from pathlib import Path
import shutil

KIT = Path(__file__).resolve().parents[1]

def initialize(destination):
    destination = Path(destination).resolve()
    if destination.is_relative_to(KIT):
        raise ValueError('Choose a private workspace outside the template repository')
    destination.mkdir(parents=True, exist_ok=False)
    shutil.copytree(KIT / 'workspace-template', destination, dirs_exist_ok=True)
    (destination / 'gitignore.template').rename(destination / '.gitignore')
    shutil.copytree(KIT / 'skills', destination / 'skills')
    shutil.copytree(KIT / 'docs', destination / 'kit-docs')
    for folder in ['interviews/exercises', 'interviews/sessions', 'interviews/coding', 'interviews/solutions', 'resumes/original', 'resumes/tailored', 'resumes/materials', 'data', 'archive']:
        (destination / folder).mkdir(parents=True, exist_ok=True)
    return destination

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    try:
        print(f'Created private workspace: {initialize(args.destination)}')
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Initialization failed: {exc}\n')
