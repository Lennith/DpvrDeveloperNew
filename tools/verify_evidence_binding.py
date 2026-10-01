#!/usr/bin/env python3
"""Fail unless every browser result is bound to the exact delivered ZIP bytes."""
import argparse,hashlib,json,zipfile
from pathlib import Path
sha=lambda b:hashlib.sha256(b).hexdigest()
def digest(m):return sha(json.dumps(sorted(m.items()),ensure_ascii=False,separators=(',',':')).encode())
def verify(zip_path,evidence):
 with zipfile.ZipFile(zip_path) as z:
  names=[i.filename for i in z.infolist() if not i.is_dir()]
  assert len(names)==len(set(names)), 'Duplicate ZIP members'
  actual={n:sha(z.read(n)) for n in names}
  declared=json.loads(z.read('SHA256SUMS.json'))
  assert declared=={n:h for n,h in actual.items() if n!='SHA256SUMS.json'}, 'ZIP internal manifest mismatch'
 root=json.loads((evidence/'tested-static-sha256.json').read_text())
 assert root==actual, 'Tested root manifest differs from final static ZIP'
 sub=json.loads((evidence/'tested-sub-sha256.json').read_text())
 manifests={'root':root,'sub':sub};trees={k:digest(v) for k,v in manifests.items()}
 pages={n for n in root if n.endswith('.html')}
 assert {n for n in sub if n.endswith('.html')}==pages, 'Subdirectory page coverage mismatch'
 for n,h in root.items():
  if n.startswith('assets/'):assert sub.get(n)==h, 'Subdirectory asset mismatch: '+n
 rows=json.loads((evidence/'browser-pages.json').read_text());seen=set()
 for r in rows:
  key=(r['mode'],r['size'],r['page']);assert key not in seen, 'Duplicate browser result';seen.add(key)
  m=manifests[r['mode']]
  assert r.get('treeSha256')==trees[r['mode']], 'Stale/unbound tree result: '+str(key)
  assert r.get('pageSha256')==m[r['page']]==r.get('responseSha256'), 'Page/served bytes mismatch: '+str(key)
  assert r['status']=='PASS', 'Failed browser page: '+str(key)
 assert seen=={(mode,size,p) for mode in ['root','sub'] for size in ['desktop','mobile'] for p in pages}, 'Missing/extra browser results'
 tasks=json.loads((evidence/'browser-tasks.json').read_text())
 assert len(tasks)==17 and len({t['name'] for t in tasks})==17, 'Missing/duplicate interaction tasks'
 for t in tasks:
  assert t.get('treeSha256')==trees, 'Stale/unbound task: '+t['name']
  assert t['status'] in ['PASS','BLOCKED'], 'Failed task: '+t['name']
  if t['status']=='BLOCKED':assert t['name']=='file:// execution attempt' and 'net::ERR_BLOCKED_BY_ADMINISTRATOR' in t.get('error',''), 'Unrecognized blockage'
 summary=json.loads((evidence/'browser-summary.json').read_text())
 assert summary['tasks']==tasks and summary['pageVisits']==len(rows) and summary['pageFailures']==0,'Summary mismatch'
 return {'status':'PASS','staticZipSha256':sha(zip_path.read_bytes()),'zipMembers':len(actual),'treeSha256':trees,'pages':len(pages),'boundPageResults':len(rows),'boundTasks':len(tasks),'limitations':'Binding proves byte identity, not hardware correctness or file:// execution.'}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('zip',type=Path);ap.add_argument('evidence',type=Path);a=ap.parse_args()
 try:print(json.dumps(verify(a.zip,a.evidence),indent=2))
 except (AssertionError,KeyError,ValueError,OSError) as e:print(json.dumps({'status':'FAIL','error':str(e)}));raise SystemExit(1)
