#!/usr/bin/env python3
"""Independent local acceptance: raw source -> imported articles -> generated site.
Reports are written outside the repository. No source snapshots are copied.
"""
import argparse,copy,hashlib,json,re
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit,urljoin,unquote,urldefrag,urlunsplit
from lxml import html
R=Path(__file__).resolve().parents[1]
def canonical(u):
 p=urlsplit(u);return urlunsplit((p.scheme,p.netloc,re.sub('/+','/',p.path),p.query,p.fragment))
def norm(s):return re.sub(r'\s+',' ',s).strip()
def prune(node):
 node=copy.deepcopy(node)
 # These are the only explicit editorial/generated source additions excluded.
 for e in node.xpath('.//*[@data-editorial-note] | .//*[contains(concat(" ",normalize-space(@class)," ")," source-downloads ")]'):e.drop_tree()
 return node

def metrics(e):
 return {'body':norm(e.text_content()),'headings':[(n.tag,norm(n.text_content()))for n in e.xpath('.//h1|.//h2|.//h3|.//h4|.//h5|.//h6')],'code':[n.text_content()for n in e.xpath('.//pre')],'inline_code':[n.text_content()for n in e.xpath('.//code[not(ancestor::pre)]')],'tables':[norm(n.text_content())for n in e.xpath('.//table')],'paragraphs':[norm(n.text_content())for n in e.xpath('.//p')],'lists':[norm(n.text_content())for n in e.xpath('.//li')],'images':[dict(n.attrib)for n in e.xpath('.//img')],'links':[n.get('href')for n in e.xpath('.//a[@href]')]}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',default='/workspace/dpvr-static');ap.add_argument('--output',default='/workspace/dpvr-new-review');ap.add_argument('--allow-partial',action='store_true');args=ap.parse_args();out=Path(args.output);out.mkdir(parents=True,exist_ok=True);S=Path(args.source);P=R/'public';m=json.loads((R/'content/pages.json').read_text());old=json.loads((S/'source/build-manifest.json').read_text());oldids={p['id']:p for p in old['pages']};urlmap=m['urlMap'];assets=m['assets'];trees={};broken=[];content_rows=[];languages=[];pending=[];media_checks=[]
 for f in P.rglob('*.html'):trees['/'+str(f.relative_to(P))]=html.fromstring(f.read_text(encoding='utf-8'))
 for path,doc in trees.items():
  for el in doc.xpath('//*[@href or @src or @poster]'):
   for attr in ['href','src','poster']:
    value=el.get(attr)
    if not value or value.startswith(('mailto:','tel:','data:','javascript:')):continue
    u=urlsplit(urljoin('https://local.invalid'+path,value))
    if u.netloc!='local.invalid':continue
    target=unquote(u.path);target=target+'index.html'if target.endswith('/')else target
    file=P/target.lstrip('/')
    if not file.is_file():broken.append({'from':path,'target':value,'type':'missing_file'});continue
    if u.fragment and file.suffix=='.html':
     d=trees.get(target);fragment=unquote(u.fragment)
     if d is not None and not d.xpath('//*[@id=$id or @name=$id]',id=fragment):broken.append({'from':path,'target':value,'type':'missing_anchor'})
 def expected_link(v,oldp,is_image=False):
  if not v or v.startswith(('#','data:','mailto:','tel:','javascript:')):return v
  info=oldp.get('resolved_links',{}).get(v)
  if info:target=info['url'];anchor=info.get('anchor','');query=info.get('query','')
  else:
   absolute=urljoin(oldp['url'],v)
   if oldp.get('archive'):target=absolute;anchor='';query=''
   else:target,anchor=urldefrag(absolute);query=urlsplit(absolute).query
  key=canonical(target);full=canonical(target+('#'+anchor if anchor and '#'not in target else ''))
  if full in urlmap:return urlmap[full]
  if key in urlmap:return urlmap[key]+(('?'+query)if query else '')+('#'+anchor if anchor else '')
  base,frag=urldefrag(key)
  if base in urlmap:return urlmap[base]+('#'+frag if frag else '')
  if key in assets:return assets[key]+('#'+anchor if anchor else '')
  if base in assets:return assets[base]+('#'+anchor if anchor else '')
  if '#member='in key:return key.split('#member=',1)[0]
  return target+('#'+anchor if anchor else '')
 for p in m['pages']:
  oldp=oldids[p.get('original',{}).get('id',p['id'])];raw=html.fromstring((S/oldp['fragment']).read_text(encoding='utf-8'));imp=prune(html.fromstring((R/p['content']).read_text(encoding='utf-8')));expected=copy.deepcopy(raw)
  # Exact, auditable technical correction only. No generic text cleanup.
  for e in p.get('evidence',[]):
   if e.get('type')!='verified_path_correction':continue
   assert e['original']=='Assets/GestureSdk/Plugins/Android' and e['corrected']=='Assets/Plugins/Android',e
   for n in expected.iter():
    if n.text:n.text=n.text.replace(e['original'],e['corrected'])
    if n.tail:n.tail=n.tail.replace(e['original'],e['corrected'])
  for n in expected.iter():
   for attr in ['href','src','poster']:
    if n.get(attr):n.set(attr,expected_link(n.get(attr),oldp,attr!='href'))
  a,b=metrics(expected),metrics(imp);diff=[k for k in a if a[k]!=b[k]]
  row={'path':p['path'],'source':p['source'],'import_status':'PASS'if not diff else 'FAIL','import_differences':diff,'evidence_corrections':p.get('evidence',[]),'body_sha256':hashlib.sha256(b['body'].encode()).hexdigest(),'counts':{'headings':len(b['headings']),'pre':len(b['code']),'inlineCode':len(b['inline_code']),'tables':len(b['tables']),'paragraphs':len(b['paragraphs']),'listItems':len(b['lists']),'images':len(b['images']),'links':len(b['links'])}}
  if p['path']not in trees:row['generated_status']='NOT_TESTED';pending.append(p['path']);content_rows.append(row);continue
  generated=trees[p['path']];article=generated.xpath('//article[contains(concat(" ",normalize-space(@class)," ")," article-body ")]');assert len(article)==1,p['path'];actual=prune(article[0]);g=metrics(actual);changed=[k for k in b if b[k]!=g[k]];row['generated_status']='PASS'if not changed else 'FAIL';row['generated_differences']=changed
  # Every original ID/name remains present; newly generated static heading IDs are allowed.
  for node in imp.xpath('.//*[@id or @name]'):
   for attr in ['id','name']:
    if node.get(attr) and not actual.xpath('.//*[@'+attr+'=$id]',id=node.get(attr)):row['generated_status']='FAIL';row.setdefault('anchor_differences',[]).append(node.get(attr))
  ls=generated.xpath('//a[contains(concat(" ",normalize-space(@class)," ")," language-link ")]/@href');expect=p.get('translation');ok=(ls==[expect])if expect else not ls
  if expect and expect not in trees:languages.append({'path':p['path'],'status':'NOT_TESTED','translation':expect,'reason':'target_not_generated'})
  else:languages.append({'path':p['path'],'status':'PASS'if ok else 'FAIL','translation':expect,'actual':ls})
  content_rows.append(row)
 # Imported media bytes must equal corresponding captured official assets, not just load.
 oldassets={canonical(k):v for k,v in old['assets'].items()}
 for url,target in assets.items():
  srcfile=S/'site'/oldassets.get(canonical(url),oldassets.get(urldefrag(canonical(url))[0],''));local=R/target.lstrip('/');pub=P/target.lstrip('/');a=hashlib.sha256(srcfile.read_bytes()).hexdigest();b=hashlib.sha256(local.read_bytes()).hexdigest();c=hashlib.sha256(pub.read_bytes()).hexdigest()if pub.is_file()else None;media_checks.append({'source':url,'target':target,'source_sha256':a,'import_sha256':b,'public_sha256':c,'status':'PASS'if a==b==c else 'FAIL'})
 failed_content=[x for x in content_rows if x['import_status']=='FAIL'or x.get('generated_status')=='FAIL'];failed_lang=[x for x in languages if x['status']=='FAIL'];result={'scope':'Independent raw captured fragment -> imported body -> generated article. Only exact data-editorial-note and source-downloads additions excluded. Verified AAR path correction explicitly whitelisted. No device or external download testing.','htmlFiles':len(trees),'sourcePages':len(content_rows),'contentPassed':sum(x['import_status']=='PASS'and x.get('generated_status')=='PASS'for x in content_rows),'contentFailed':len(failed_content),'notGenerated':pending,'localLinkIssues':broken,'translationChecks':languages,'contentChecks':content_rows,'mediaChecks':media_checks,'failedMedia':sum(x['status']!='PASS'for x in media_checks)}
 (out/'site-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));summary={'htmlFiles':len(trees),'sourcePages':len(content_rows),'contentPassed':result['contentPassed'],'contentFailed':len(failed_content),'notGenerated':len(pending),'brokenLinks':len(broken),'failedTranslations':len(failed_lang),'failedMedia':result['failedMedia']};(out/'site-verification.md').write_text('# 全量静态站核验\n\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n\n比较原始来源正文、导入正文及生成正文的文本、标题、代码、表格、段落、列表、图片属性与链接目标；保留原锚点。仅排除明确data-editorial-note与source-downloads。4篇手势AAR路径证据更正逐项白名单。详细差异、图片字节hash及未生成页面见JSON。外部下载、真实设备运行未测。\n');print(json.dumps(summary,ensure_ascii=False));
 if failed_content:print('Content differences',[(x['path'],x.get('import_differences'),x.get('generated_differences'))for x in failed_content[:10]])
 if broken:print('Link issues',broken[:10])
 if failed_content or failed_lang or result['failedMedia'] or (not args.allow_partial and (pending or broken)):raise SystemExit(1)
if __name__=='__main__':main()
