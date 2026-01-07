from pathlib import Path
p = Path('backend/data/raw_docs')
files = sorted([x for x in p.glob('doc_*.txt')])
print('Count:', len(files))
if files:
    print('\n--- Sample doc_001.txt ---')
    print(files[0].read_text()[:800])
    print('\n--- Manifest head ---')
    manifest = p / 'manifest.tsv'
    if manifest.exists():
        print('\n'.join(manifest.read_text().splitlines()[:5]))
