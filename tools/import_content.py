#!/usr/bin/env python3
"""Import current DPVR article content only; source captures stay outside this repository."""
import argparse,copy,hashlib,json,posixpath,re,shutil
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit,urljoin,urldefrag,quote,unquote
from lxml import html,etree
ROOT=Path(__file__).resolve().parents[1]
EXCLUDE={'Device Manager V2 · 历史归档','RDC v2 · 安装包归档'}
OLD_BEGINNERS={'6fa3f274cb2ec08f':'614471854ce44c59','88634cc9fb5ff86b':'8e7043a5a57074bd'}
GUIDE_PRODUCTS={'screen-casting':'cast','video-encryption':'encryption','videoplay-config':'playback','copy-tool-guide':'copy','unity-player-plugin-guide':'player','local-upgrade':'firmware','connection-issue':'troubleshooting'}
PRODUCT_NAMES={'dm':'Device Manager V2','rdc':'RDC v2','cast':'DPVR Screen Cast','encryption':'视频加密工具 V3','playback':'视频播放配置','copy':'TF 卡复制工具','player':'Unity Player Plug-in','firmware':'本地固件升级','troubleshooting':'连接问题','gesture':'Unity Gesture Plug-in'}
def canonical(u):
 p=urlsplit(u);return urlunsplit((p.scheme,p.netloc,re.sub('/+','/',p.path),p.query,p.fragment))
def norm(s):return re.sub(r'\s+',' ',s).strip()
def layout(p):
 lang=p['language'];family=p['family'];old=p['output']
 if family=='Device Manager V2':product='dm';tail=old.split('/'+lang+'/',1)[1]
 elif family=='RDC v2':product='rdc';tail=old.split('/'+lang+'/',1)[1]
 elif family=='Resource Guides':tail=urlsplit(p['url']).fragment+'.html';product=GUIDE_PRODUCTS[tail[:-5]]
 elif family.startswith('手势'):product='gesture';tail='beginner.html' if p['id'] in OLD_BEGINNERS.values() else 'parameters.html'
 elif family.startswith('视频加密'):
  product='encryption';member=p['archive_member']
  tail='gui-user-manual.html' if member.startswith('GUI') else 'runtime/'+member.rsplit('/',1)[1] if '/runtime_tool_v3/' in member else 'cli-user-manual.html'
 elif family.startswith('视频播放配置'):product='playback';tail='configuration-example.html'
 elif family.startswith('TF卡'):product='copy';tail='configuration-example.html'
 else:raise ValueError(family)
 return product,f'/{lang}/docs/{product}/{tail}'
def metrics(e):return {'text':norm(e.text_content()),'headings':[norm(x.text_content())for x in e.xpath('.//h1|.//h2|.//h3|.//h4|.//h5|.//h6')],'code':[x.text_content()for x in e.xpath('.//pre')],'tables':[norm(x.text_content())for x in e.xpath('.//table')],'images':len(e.xpath('.//img')),'links':len(e.xpath('.//a[@href]'))}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',default='/workspace/dpvr-static');args=ap.parse_args();src=Path(args.source);manifest=json.loads((src/'source/build-manifest.json').read_text(encoding='utf-8'));allpages=manifest['pages'];byid={p['id']:p for p in allpages}
 selected=[copy.deepcopy(p) for p in allpages if p['family']not in EXCLUDE and p['id']not in OLD_BEGINNERS and not p['output'].endswith(('/search.html','/genindex.html'))];assert len(selected)==472,len(selected)
 for p in list(selected):
  if p.get('source_format')=='json':
   mirror=copy.deepcopy(p);mirror.update(id=p['id']+'-en',language='en',_source_id=p['id'],_derived_mirror=True,translations=[p['id']]);p['translations']=[mirror['id']];selected.append(mirror)
 assert len(selected)==474,len(selected)
 outdir=ROOT/'content/articles';outdir.mkdir(parents=True,exist_ok=True);media=ROOT/'assets/media';media.mkdir(parents=True,exist_ok=True)
 urlmap={};paths={};products={}
 for p in selected:
  product,path=layout(p);paths[p['id']]=path;products[p['id']]=product
  if p.get('_derived_mirror'):continue
  for u in [p['url']]+p.get('aliases',[]):urlmap[canonical(u)]=path
  if p['url'].endswith('/'):urlmap[canonical(p['url']+'index.html')]=path
 for p in allpages:
  if p['id']in OLD_BEGINNERS:urlmap[canonical(p['url'])]=paths[OLD_BEGINNERS[p['id']]]
  if p['family']not in EXCLUDE and p['output'].endswith(('/search.html','/genindex.html')):urlmap[canonical(p['url'])]=f'/{p["language"]}/search.html'
 for lang in ['cn','en']:urlmap[f'https://developer.dpvr.com/resources/doc_{lang}.html']=urlmap[f'https://developer.dpvr.com/resources/doc_{lang}.html#screen-casting']
 inventory=json.loads((src/'source/bundles/supplement/archive-inventories/unity-gesture.unity-inventory.json').read_text(encoding='utf-8'));assert any(x.get('path')=='Assets/Plugins/Android/gesturesdk-release.aar' for x in inventory),'Gesture AAR path evidence missing'
 assetlookup={canonical(k):v for k,v in manifest.get('assets',{}).items()};assetmap={};issues=[];checks=[];pages=[]
 def copy_media(url):
  key=canonical(url);file=assetlookup.get(key)
  if not file:
   # Some originals use a fragment on an image link.
   file=assetlookup.get(urldefrag(key)[0])
  if not file:raise ValueError('Missing captured media '+url)
  data=(src/'site'/file).read_bytes();ext=Path(file).suffix.lower();assert ext in ['.png','.jpg','.jpeg','.gif','.webp','.svg','.ico'],(url,file)
  target='assets/media/'+hashlib.sha256(data).hexdigest()[:20]+ext;dest=ROOT/target
  if not dest.exists():dest.write_bytes(data)
  assetmap[key]='/'+target;return '/'+target
 def resolve(value,p):
  if value.startswith('#'):return p['url'],value[1:],''
  info=p.get('resolved_links',{}).get(value)
  if info:return info['url'],info.get('anchor',''),info.get('query','')
  # Ordinary online URLs have ordinary fragment identifiers. Archive source identity contains #member.
  absolute=urljoin(p['url'],value)
  if not p.get('archive'):base,frag=urldefrag(absolute);return base,frag,urlsplit(absolute).query
  return absolute,'',''
 def rewrite(value,p,is_image=False):
  if not value or value.startswith(('data:','mailto:','tel:','javascript:')):return value
  if value.startswith('#'):return value
  target,anchor,query=resolve(value,p);key=canonical(target)
  full=canonical(target+('#'+anchor if anchor and '#'not in target else ''))
  if full in urlmap:return urlmap[full]
  if key in urlmap:return urlmap[key]+(('?'+query)if query else '')+('#'+anchor if anchor else '')
  base,frag=urldefrag(key)
  if base in urlmap:return urlmap[base]+('#'+frag if frag else '')
  candidate=assetlookup.get(key)or assetlookup.get(base)
  if is_image or(candidate and Path(candidate).suffix.lower()in ['.png','.jpg','.jpeg','.gif','.webp','.svg','.ico']):return copy_media(key)+('#'+anchor if anchor else '')
  # SDK binaries remain official links. An archive-member identity is not a direct downloadable URL.
  if '#member='in key:
   issues.append({'page':paths[p['id']],'original':value,'source':key,'action':'official_package_download','member':unquote(key.split('#member=',1)[1])});return key.split('#member=',1)[0]
  if key.startswith('https://static.dpvr.com/') and re.search(r'\.(html?)(?:[?#]|$)',key):issues.append({'page':paths[p['id']],'original':value,'source':key,'action':'unmapped_official_page'})
  return target+('#'+anchor if anchor else '')
 for p in selected:
  original=(src/p['fragment']).read_text(encoding='utf-8');doc=html.fromstring(original);before=metrics(doc);evidence=[];notes=[]
  if p.get('_derived_mirror'):
   evidence.append({'type':'language_neutral_code_mirror','sourceId':p['_source_id'],'basis':'Unchanged language-neutral JSON from the official package; no translation of code.'})
   notes.append({'type':'language_neutral_code_mirror','text':'This is the unchanged language-neutral JSON example from the official package. Only this explanatory caption is English; this page is not an official translated manual.'})
  if products[p['id']]=='gesture':
   wrong='Assets/GestureSdk/Plugins/Android';correct='Assets/Plugins/Android'
   for e in doc.iter():
    if e.text and wrong in e.text:e.text=e.text.replace(wrong,correct)
    if e.tail and wrong in e.tail:e.tail=e.tail.replace(wrong,correct)
   if wrong in original:evidence.append({'type':'verified_path_correction','original':wrong,'corrected':correct,'basis':'GestureDemoPlugin.zip > Gesture.unitypackage asset pathname inventory includes Assets/Plugins/Android/gesturesdk-release.aar','source':'https://dl.dpvr.com/resources/gesture/GestureDemoPlugin.zip','assetPath':'Assets/Plugins/Android/gesturesdk-release.aar'})
   notes.append({'type':'source_difference','text':'不同说明中的 zDistanceFromCameraImage 距离语义与计算表述存在差异；正文按各来源保留，未统一改写算法。' if p['language']=='cn' else 'The sources describe zDistanceFromCameraImage depth and calculation differently. Their original descriptions are retained; no algorithm is silently changed.'})
  for e in doc.iter():
   for attr in ['href','src','poster']:
    if e.get(attr):e.set(attr,rewrite(e.get(attr),p,attr!='href'))
  page_issues=[x for x in issues if x['page']==paths[p['id']]]
  if page_issues:
   notes.append({'type':'source_download_unavailable','text':'原文引用的子工具文件未在已核查的官方 V3 工具包中找到。相应链接提供官方完整工具包入口，不代表该子文件可单独下载。' if p['language']=='cn' else 'The source references tool subfiles that were not found in the verified official V3 package. These links open the official complete package; they do not claim that the named subfiles are available separately.','references':page_issues})
  # Explicit editorial notices are separate from source text and excluded only from source-preservation metrics.
  for note in notes:
   aside=etree.SubElement(doc,'aside',{'class':'source-note','data-editorial-note':note['type']});aside.text=note['text']
  # Keep article body intact, including source anchor IDs and authored heading text.
  content='content/articles/'+p['id']+'.html';(ROOT/content).write_text(etree.tostring(doc,encoding='unicode',method='html',with_tail=False),encoding='utf-8')
  title=p['title'];title=re.sub(r'\s+Contents Menu Expand.*$','',title).strip();title=title.rstrip('#¶').strip()
  translation=next((paths[x]for x in p.get('translations',[])if x in paths),None)
  downloads=[]
  for d in p.get('downloads',[]):downloads.append({'title':d['title'],'url':d['url'].split('#member=',1)[0],'sourceMember':p.get('archive_member')})
  pages.append({'id':p['id'],'title':title,'language':p['language'],'product':products[p['id']],'path':paths[p['id']],'content':content,'source':p['url'],'translation':translation,'section':p.get('section',''),'original':{'id':p.get('_source_id',p['id']),'category':p['family'],'path':p['output'],'url':p['url'],'member':p.get('archive_member'),'format':p.get('source_format','html')},'downloads':downloads,'downloadContext':page_issues,'notes':notes,'evidence':evidence,'previous':rewrite(p['prev'],p)if p.get('prev')else None,'next':rewrite(p['next'],p)if p.get('next')else None})
  comparison=copy.deepcopy(doc)
  for editorial in comparison.xpath('.//*[@data-editorial-note]'):editorial.drop_tree()
  after=metrics(comparison);expected=copy.deepcopy(before)
  if evidence:
   for k,v in expected.items():
    if isinstance(v,str):expected[k]=v.replace('Assets/GestureSdk/Plugins/Android','Assets/Plugins/Android')
    elif isinstance(v,list):expected[k]=[x.replace('Assets/GestureSdk/Plugins/Android','Assets/Plugins/Android')for x in v]
  assert expected==after,(p['url'],'Content metrics changed unexpectedly')
  checks.append({'id':p['id'],'path':paths[p['id']],'unchanged_except_evidence':True,'text_sha256':hashlib.sha256(after['text'].encode()).hexdigest(),'images':after['images'],'links':after['links'],'headings':len(after['headings']),'code':len(after['code']),'tables':len(after['tables'])})
 for u in ['https://developer.dpvr.com/resource/img/logo.png']+[x['image']for r in manifest['resources']for x in r.get('deviceModels',[])]+[x['url']for r in manifest['resources']for x in r.get('screenshots',[])]:copy_media(u)
 # Deterministic default-Chinese order; explicit translations are not inferred from similar names.
 pages.sort(key=lambda p:(p['language']!='cn',p['product'],p['path']))
 data={'schemaVersion':1,'defaultLanguage':'cn','pages':pages,'urlMap':urlmap,'assets':assetmap,'counts':{'pages':len(pages),'byProduct':{x:sum(p['product']==x for p in pages)for x in sorted(set(p['product']for p in pages))},'mediaFiles':len(set(assetmap.values()))}}
 (ROOT/'content/pages.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 if not (ROOT/'content/products.json').exists():(ROOT/'content/products.json').write_text(json.dumps({'names':PRODUCT_NAMES,'resources':[{**r,'additionalDocs':[d for d in r.get('additionalDocs',[]) if canonical(d['url']) in urlmap]}for r in manifest['resources']]},ensure_ascii=False,indent=2),encoding='utf-8')
 Path('/workspace/dpvr-current-import-report.json').write_text(json.dumps({'counts':data['counts'],'checks':checks,'links_requiring_context':issues,'excludedSnapshotPages':217,'mergedBeginnerPages':2,'replacedUtilityPages':12},ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(data['counts'],ensure_ascii=False));print('Context links',len(issues))
if __name__=='__main__':main()
