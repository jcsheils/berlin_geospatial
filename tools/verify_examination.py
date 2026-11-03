"""Verify the frozen examination package using the Python standard library."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote

ROOT=Path(__file__).resolve().parents[1]


def verify(root=ROOT):
    manifest=json.loads((root/'examination/release_manifest.json').read_text())
    errors=[];checked=0
    for entry in manifest['files']:
        p=(root/entry['path']).resolve()
        if not p.is_relative_to(root.resolve()):
            errors.append(f'Path escapes checkout: {entry["path"]}');continue
        if not p.is_file():
            errors.append(f'Missing: {entry["path"]}');continue
        with p.open('rb') as handle:actual=hashlib.file_digest(handle,'sha256').hexdigest()
        if actual != entry['sha256'] or p.stat().st_size != entry['bytes']:errors.append(f'Changed: {entry["path"]}')
        if p.stat().st_size >= 100*1024*1024:errors.append(f'Exceeds ordinary GitHub file limit: {entry["path"]}')
        checked+=1
    docs=[root/'README.md',*sorted((root/'examination').rglob('*.md')),root/'data/README.md',root/'docs/analysis_plan.md',root/'docs/repository_architecture.md']
    links=0
    for doc in docs:
        for target in re.findall(r'\]\(([^\n)]+)\)',doc.read_text()):
            if re.match(r'[a-zA-Z]+:',target) or target.startswith('#'):continue
            target=unquote(target.split('#',1)[0]).strip('<>')
            if not target:continue
            resolved=(doc.parent/target).resolve()
            if not resolved.exists():errors.append(f'Broken link in {doc.relative_to(root)}: {target}')
            links+=1
    return checked,links,errors


if __name__=='__main__':
    checked,links,errors=verify()
    for error in errors:print('ERROR:',error)
    print(f'Examination package: {checked} file checksums, {links} local links, {len(errors)} errors.')
    sys.exit(bool(errors))
