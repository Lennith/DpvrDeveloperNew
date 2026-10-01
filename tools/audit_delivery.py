#!/usr/bin/env python3
"""Audit an extracted delivery, with optional independent captured-source comparison."""
import argparse,base64,copy,hashlib,json,posixpath,re,sys
from pathlib import Path
from urllib.parse import urljoin,urlsplit,urlunsplit,unquote,urldefrag,quote
from collections import Counter
from lxml import html
R=Path(__file__).resolve().parents[1]
def norm(s):return re.sub(r'\s+',' ',s).strip()
def parse(s):return html.fromstring(s)
def prune(e):
 e=copy.deepcopy(e)
 for x in e.xpath('.//*[@data-editorial-note]|.//*[contains(concat(" ",normalize-space(@class)," ")," source-downloads ")]'):x.drop_tree()
 return e

def metric(e):
 return {'text':norm(e.text_content()),'headings':[(x.tag,norm(x.text_content())) for x in e.xpath('.//h1|.//h2|.//h3|.//h4|.//h5|.//h6')], 'code':[x.text_content() for x in e.xpath('.//pre')], 'tables':[norm(x.text_content()) for x in e.xpath('.//table')], 'paragraphs':[norm(x.text_content()) for x in e.xpath('.//p')], 'lists':[norm(x.text_content()) for x in e.xpath('.//li')], 'images':[(x.get('src'),x.get('alt')) for x in e.xpath('.//img')], 'links':[x.get('href') for x in e.xpath('.//a[@href]')]}
def canon(u):
 p=urlsplit(u);return urlunsplit((p.scheme,p.netloc,re.sub('/+','/',p.path),p.query,p.fragment))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--site',type=Path,default=R/'public');ap.add_argument('--evidence',type=Path);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 data=json.loads((R/'content/pages.json').read_text());pages=data['pages'];trees={'/'+str(f.relative_to(a.site)):parse(f.read_text()) for f in a.site.rglob('*.html')};issues=[];externals={};rows=[];sources=[]
 for path,tree in trees.items():
  for el in tree.xpath('//*[@href or @src or @poster]'):
   for attr in ['href','src','poster']:
    v=el.get(attr)
    if not v or v.startswith(('mailto:','tel:','data:')):continue
    u=urlsplit(urljoin('https://delivery.invalid'+path,v))
    if u.netloc!='delivery.invalid':externals.setdefault(urldefrag(urlunsplit(u))[0],set()).add(path);continue
    target=unquote(u.path);target+= 'index.html' if target.endswith('/') else '';f=a.site/target.lstrip('/')
    if v.startswith('/') or '\\' in v:issues.append({'page':path,'target':v,'reason':'nonportable_url'})
    if not f.is_file():issues.append({'page':path,'target':v,'reason':'missing_file_or_case_mismatch'});continue
    if u.fragment and target in trees and not trees[target].xpath('//*[@id=$v or @name=$v]',v=unquote(u.fragment)):issues.append({'page':path,'target':v,'reason':'missing_anchor'})
    if urlsplit(urljoin((a.site/path.lstrip('/')).as_uri(),v)).scheme!='file':issues.append({'page':path,'target':v,'reason':'file_resolution'})
 for p in pages:
  imp=prune(parse((R/p['content']).read_text()));gen=prune(trees[p['path']].xpath('//article[contains(concat(" ",normalize-space(@class)," ")," article-body ")]')[0])
  for el in gen.xpath('.//*[@href or @src or @poster]'):
   for attr in ['href','src','poster']:
    v=el.get(attr)
    if v and not v.startswith(('#','http:','https:','data:','mailto:','tel:')):el.set(attr,urljoin(p['path'],v))
  x,y=metric(imp),metric(gen);diff=[k for k in x if x[k]!=y[k]]
  lang=trees[p['path']].xpath('//a[@class="language-link"]/@href');translated=urljoin(p['path'],lang[0]) if lang else None
  rows.append({'path':p['path'],'source':p['source'],'generatedDifferences':diff,'translationMatches':translated==p.get('translation'),'counts':{k:len(v) for k,v in x.items() if isinstance(v,list)},'bodySHA256':hashlib.sha256(x['text'].encode()).hexdigest()})
 if a.evidence:
  responses=json.loads((a.evidence/'raw/responses.json').read_text());urlmap=data['urlMap'];assets=data['assets']
  for p in pages:
   src=p['source'];resp=responses.get(src);raw=None
   if 'resources/doc_' in src:raw=parse((a.evidence/('raw/'+p['language']+'-'+urlsplit(src).fragment+'.html')).read_text())
   elif p['original']['format']=='markdown':raw=parse((a.evidence/('raw/'+p['id']+'.md.html')).read_text())
   elif '/gui-user-manual' in p['path']:
    raw=parse((a.evidence/('raw/'+p['language']+'-gui.html')).read_text())
   else:
    if not resp:resp=responses.get(src.replace('&language=en',''))
    if resp:
     b=(base64.b64decode(resp['body']).decode('utf-8-sig') if resp.get('encoding')=='base64' else resp['body']).replace('\r\n','\n');fmt=p['original']['format']
     if fmt=='markdown':
      import markdown
      raw=parse('<article>'+markdown.markdown(b,extensions=['tables','fenced_code'])+'</article>')
     elif fmt=='json':raw=parse('<article><h1>'+p['title']+'</h1><pre><code></code></pre></article>');raw.xpath('.//code')[0].text=b
     else:
      t=parse(b);nodes=t.xpath('//article') or t.xpath('//*[@class="container"]') or t.xpath('//body');raw=nodes[0] if nodes else t
   if raw is None:sources.append({'path':p['path'],'status':'UNVERIFIED','reason':'capture_not_resolved'});continue
   imp=prune(parse((R/p['content']).read_text()));raw=prune(raw)
   # Remove language controls only from GUI comparison; they are shell, not manual content.
   if '/gui-user-manual' in p['path']:
    for t in [raw,imp]:
     for el in t.xpath('.//*[@id="langBtn" or @id="langFab"]'):el.drop_tree()
   for ev in p.get('evidence',[]):
    if ev['type']=='verified_path_correction':
     for el in raw.iter():
      if el.text:el.text=el.text.replace(ev['original'],ev['corrected'])
      if el.tail:el.tail=el.tail.replace(ev['original'],ev['corrected'])
   unresolved=[]
   def mapped(v):
    if not v or v.startswith(('#','data:','mailto:','tel:')):return v
    if '#member=' in src and not urlsplit(v).scheme:
     archive,member=src.split('#member=',1);member=unquote(member).split('&language=',1)[0];part=urlsplit(v);resolved=posixpath.normpath(posixpath.join(posixpath.dirname(member),unquote(part.path)));absolute=archive+'#member='+quote(resolved,safe='');anchor=part.fragment
    else:absolute=urljoin(src,v);anchor=urlsplit(absolute).fragment
    key=canon(absolute)
    if key in urlmap:return urlmap[key]
    if key in assets:return assets[key]
    base,frag=urldefrag(key)
    if base in urlmap:return urlmap[base]+('#'+frag if frag else '')
    if base in assets:return assets[base]+('#'+frag if frag else '')
    if '#member=' in key:
     if anchor:
      plain=key.split('#member=')[0]+'#member='+quote(resolved,safe='')
      if plain in urlmap:return urlmap[plain]+'#'+anchor
     return base
    return absolute
   for el in raw.iter():
    for attr in ['href','src','poster']:
     if el.get(attr):el.set(attr,mapped(el.get(attr)))
   x,y=metric(raw),metric(imp);diff=[k for k in x if x[k]!=y[k]]
   sources.append({'path':p['path'],'status':'PASS' if not diff else 'DIFFERENCE','differences':diff,'source':src,'details':{k:{'raw':x[k],'imported':y[k]} for k in diff},'allowedCorrections':p.get('evidence',[])})
  media=[]
  for u,target in data['assets'].items():
   resp=responses.get(u);local=(a.site/target.lstrip('/')).read_bytes();sha=hashlib.sha256(local).hexdigest();expected=hashlib.sha256(base64.b64decode(resp['body']) if resp.get('encoding')=='base64' else resp['body'].encode()).hexdigest() if resp else None
   media.append({'url':u,'path':target,'sha256':sha,'status':'PASS' if sha==expected else 'UNVERIFIED' if expected is None else 'DIFFERENCE'})
  (a.output/'source-comparison.json').write_text(json.dumps({'pages':sources,'media':media},ensure_ascii=False,indent=2))
 idx=(a.site/'assets/search-index.js').read_text();index=json.loads(idx[len('window.DPVR_SEARCH='):-1]);indexed={x['url'] for x in index};missing=[p['path'] for p in pages if p['path'] not in indexed]
 result={'htmlPages':len(trees),'sourceArticles':len(rows),'articleGeneratedFailures':sum(bool(x['generatedDifferences']) for x in rows),'translationFailures':sum(not x['translationMatches'] for x in rows),'localIssues':issues,'searchEntries':len(index),'searchMissing':missing,'byProductLanguage':dict(Counter(p['product']+'/'+p['language'] for p in pages)),'sourceStatus':dict(Counter(x['status'] for x in sources)),'articles':rows}
 (a.output/'static-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));(a.output/'external-links.json').write_text(json.dumps([{'url':u,'pages':sorted(ps)} for u,ps in sorted(externals.items())],ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ['articles','localIssues']},ensure_ascii=False));print('Local issues:',len(issues),issues[:5])
if __name__=='__main__':main()
