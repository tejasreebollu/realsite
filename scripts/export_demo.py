"""Export the running portal's active synthetic inventory for client demos."""
import json
from pathlib import Path
from urllib.request import urlopen

root = Path(__file__).resolve().parents[1]
properties = []
for purpose in ('sale', 'rent'):
    with urlopen(f'http://localhost:8090/api/properties?q=&purpose={purpose}&page_size=100', timeout=20) as response:
        result = json.load(response)
    if result['total'] > 100:
        raise RuntimeError('Inventory exceeds this export page size; use a paginated export.')
    properties.extend(p for p in result['items'] if p['demo'])
properties.sort(key=lambda p: p['id'])
document = {'synthetic': True, 'market': 'India', 'notice': 'Fictional demo listings. Illustrative photos, prices and coordinates; not real offers.', 'count': len(properties), 'properties': properties}
destination = root / 'data/demo-properties.json'
destination.parent.mkdir(exist_ok=True)
destination.write_text(json.dumps(document, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'Exported {len(properties)} synthetic properties to {destination}')
