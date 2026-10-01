#!/usr/bin/env python3
"""Materialize ONLY audit references from the two authorized source capture ZIPs."""
import argparse,base64,json,zipfile,subprocess
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--core',type=Path,required=True);ap.add_argument('--supplement',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();raw=a.output/'raw';raw.mkdir(parents=True,exist_ok=True)
core=zipfile.ZipFile(a.core);supp=zipfile.ZipFile(a.supplement);responses={}
for z,name in [(core,'dpvr-resource-source-bundle.json'),(supp,'dpvr-source-supplement.json')]:
 for x in json.loads(z.read(name))['responses']:responses[x['url']]=x
(raw/'responses.json').write_text(json.dumps(responses,ensure_ascii=False))
def decode(x):return base64.b64decode(x['body']).decode('utf-8-sig') if x.get('encoding')=='base64' else x['body']
for lang in ['cn','en']:(raw/('doc_'+lang+'.html')).write_text(decode(responses['https://developer.dpvr.com/resources/doc_'+lang+'.html']))
x=next(x for x in responses.values() if 'GUI%20Version' in x['url'] and 'User' in x['url'] and x.get('contentType')=='text/html');(raw/'gui.html').write_text(decode(x))
R=Path(__file__).resolve().parents[1]
for p in json.loads((R/'content/pages.json').read_text())['pages']:
 if p['original']['format']!='markdown':continue
 x=responses.get(p['source'])
 if x:body=decode(x)
 else:
  import io
  z=zipfile.ZipFile(io.BytesIO(core.read('gesture/doc_'+p['language']+'.zip')));member=p['original']['member'];actual=next(n for n in z.namelist() if n==member or (p['language']=='cn' and n.encode('cp437').decode('gbk')==member));body=z.read(actual).decode('utf-8-sig')
 (raw/(p['id']+'.md')).write_text(body)
subprocess.run(['node',str(R/'tools/render_reference.cjs'),str(raw)],check=True)
print('Prepared captured sources; live availability is a separate check.')
