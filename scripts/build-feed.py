"""Build a declarative, immutable knowledge payload and its checksum manifest."""
from pathlib import Path
from urllib.parse import urlparse
import hashlib,json,re

root=Path(__file__).resolve().parents[1]
release=json.loads((root/'release.json').read_text(encoding='utf-8'))
version=release['releaseVersion']
assert re.fullmatch(r'[0-9]+(?:\.[0-9]+){3}',version),'Release version must use year.month.day.revision'
base=release['baseUrl'];assert base.startswith('https://') and base.endswith('/')
packs=json.loads((root/'catalog.json').read_text(encoding='utf-8'))
assert 0<len(packs)<=100
ids=set()
for pack in packs:
    for key in ['id','name','category','modelVersion','packVersion','summary','defaultLanguage','format','verifiedAt']:
        assert isinstance(pack.get(key),str) and pack[key].strip(),f'{key} is required'
    assert re.fullmatch(r'[a-zA-Z0-9_-]{1,100}',pack['id']) and pack['id'] not in ids
    ids.add(pack['id'])
    for key in ['recommendationVersion','rulesVersion']:
        if key in pack:
            assert isinstance(pack[key],str) and pack[key].strip(),f'{key} must be a nonempty string'
    assert pack['category'] in ['codex','image','video'] and pack['format'] in ['text','json']
    assert 0<len(pack['sections'])<=50 and all(s.get('title') and s.get('content') for s in pack['sections'])
    assert 0<len(pack['sources'])<=30
    for source in pack['sources']:
        parsed=urlparse(source['url']);assert parsed.scheme=='https' and parsed.hostname and not parsed.username and not parsed.password
    for example in pack['examples']:
        if pack['format']=='json':json.loads(example['body'])
    assert len(json.dumps(pack,ensure_ascii=False).encode())<=512*1024
payload=(json.dumps({'schemaVersion':1,'packs':packs},ensure_ascii=False,indent=2)+'\n').encode('utf-8')
filename=f'knowledge-{version}.json'
target=root/'releases'/filename;target.parent.mkdir(exist_ok=True)
if target.exists():assert target.read_bytes()==payload,'Published payloads are immutable; choose a new release version'
target.write_bytes(payload)
manifest={'schemaVersion':1,'releaseVersion':version,'publishedAt':release['publishedAt'],'payloadUrl':base+'releases/'+filename,'sha256':hashlib.sha256(payload).hexdigest(),'packCount':len(packs),'changelog':release['changelog']}
(root/'manifest.json').write_bytes((json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print(f'Validated {len(packs)} packs; built maintenance release {version}.')
