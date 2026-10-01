#!/usr/bin/env python3
"""Attempt every distinct external URL; proxy failures are not origin 404s."""
import concurrent.futures,json,sys,urllib.request,urllib.error,time
from pathlib import Path
src=Path(sys.argv[1]);out=Path(sys.argv[2]);links=json.loads(src.read_text())
def check(x):
 u=x['url'];start=time.time()
 try:
  req=urllib.request.Request(u,headers={'User-Agent':'DPVR-documentation-link-audit/1.0','Range':'bytes=0-1023'})
  with urllib.request.urlopen(req,timeout=15) as r:body=r.read(1024);return {'url':u,'status':'REACHABLE','http':r.status,'finalURL':r.url,'mime':r.headers.get('Content-Type'),'sampleBytes':len(body),'seconds':round(time.time()-start,2)}
 except urllib.error.HTTPError as e:return {'url':u,'status':'HTTP_ERROR','http':e.code,'detail':str(e),'seconds':round(time.time()-start,2)}
 except Exception as e:return {'url':u,'status':'UNVERIFIED_NETWORK','detail':str(e),'seconds':round(time.time()-start,2)}
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:results=list(pool.map(check,links))
out.write_text(json.dumps(results,ensure_ascii=False,indent=2));from collections import Counter;print(dict(Counter(x['status'] for x in results)))
