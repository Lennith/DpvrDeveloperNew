"""Build the current DPVR resource portal. No network or publishing."""
from pathlib import Path
import json,html,re,shutil,sys,posixpath
from collections import defaultdict
from urllib.parse import urlsplit
from lxml import html as H
R=Path(__file__).resolve().parents[1];OUT=R/'public'
if OUT.exists():shutil.rmtree(OUT)
OUT.mkdir()
BASE=''
if '--base' in sys.argv:
 BASE=sys.argv[sys.argv.index('--base')+1].rstrip('/')
 if BASE and (not BASE.startswith('/') or any(x in BASE for x in ['..','"','<','>','?','#'])):raise SystemExit('Use a safe absolute URL prefix, e.g. /dpvr-resources')
E=lambda x:html.escape(str(x),quote=True)
data=json.loads((R/'content/pages.json').read_text());pages=data['pages'];urlmap=data['urlMap'];products=json.loads((R/'content/products.json').read_text());journeys=[j for j in json.loads((R/'content/journeys.json').read_text()) if j['id']!='dms-start'];
if (R/'content/go-guide.json').exists():journeys.append(json.loads((R/'content/go-guide.json').read_text()))
prod={p['id']:p for p in products};by_path={p['path']:p for p in pages}
T=lambda cn,en,l:cn if l=='cn' else en
L=lambda obj,l:obj.get(l,obj.get('en','')) if isinstance(obj,dict) else obj
search=[]
def emit(path,s):
 # Relative links travel together with the static tree: file://, root HTTP and
 # arbitrary deployment prefixes all resolve without a server rewrite.
 parent=posixpath.dirname(path.lstrip('/')) or '.'
 root=posixpath.relpath('.',parent)+'/'
 def relative(m):
  value=m.group(2)
  if not value.startswith('/') or value.startswith('//'):return m.group(0)
  parts=urlsplit(html.unescape(value));target=posixpath.relpath(parts.path.lstrip('/') or '.',parent)
  return m.group(1)+'="'+E(target+('?' + parts.query if parts.query else '')+('#'+parts.fragment if parts.fragment else ''))+'"'
 s=re.sub(r'(href|src|poster)="([^"\n]*)"',relative,s)
 s=s.replace('<body ', '<body data-root="'+root+'" data-base="'+E(BASE)+'" ',1)
 f=OUT/path.lstrip('/');f.parent.mkdir(parents=True,exist_ok=True);f.write_text(s,encoding='utf-8')
def overview(pid,l):return f'/{l}/resources/{pid}.html'
def guide(jid,l):return f'/{l}/guides/{jid}.html'
def mapdoc(src,l):
 target=urlmap.get(src,src)
 p=by_path.get(target)
 if p and p['language']!=l and p.get('translation'):target=p['translation']
 return target

def shell(title,body,l,path,translation=None,product=None):
 other='en' if l=='cn' else 'cn';tr=f'/{other}/index.html' if translation is None else translation
 return f'''<!doctype html><html lang="{'zh-CN' if l=='cn' else 'en'}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{E(title)} · DPVR Developer Center</title><link rel="stylesheet" href="/assets/site.css"><script defer src="/assets/search-index.js"></script><script defer src="/assets/app.js"></script></head><body data-language="{l}" data-product="{product or ''}"><a class="skip-link" href="#main">{T('跳至正文','Skip to content',l)}</a><header class="site-header"><a class="brand" href="/{l}/index.html"><img src="/assets/logo.png" alt="DPVR"><span>DPVR DEVELOPER CENTER</span></a><button class="global-toggle" aria-label="{T('官网导航','Website navigation',l)}" aria-expanded="false" aria-controls="global-nav">☰</button><nav id="global-nav" class="global-nav"><a href="https://developer.dpvr.com/home.html">HOME</a><a href="https://developer.dpvr.com/sdk.html">SDK</a><details><summary>SOLUTIONS</summary><div><a href="https://developer.dpvr.com/solutions-DPVR-starLink.html">StarLink</a><a href="https://developer.dpvr.com/solutions-DPVR-remote-control.html">Remote Control</a></div></details><a aria-current="page" href="/{l}/index.html">RESOURCES</a><details><summary>ASSISTANT</summary><div><a href="https://product.dpvr.com/assistant/download.html">Assistant</a><a href="https://product.dpvr.com/assistant4">Assistant4</a></div></details></nav></header><div class="utility-bar"><a class="breadcrumb" href="/{l}/index.html">{T('开发者资源','Developer resources',l)}</a><div class="utility-actions"><button class="search-open">{T('搜索文档','Search docs',l)} <kbd>⌘ K</kbd></button><a class="language-link" hreflang="{other}" href="{E(tr)}">{'English' if l=='cn' else '简体中文'}</a><select class="theme" aria-label="{T('外观','Appearance',l)}"><option value="light">{T('浅色','Light',l)}</option><option value="dark">{T('深色','Dark',l)}</option><option value="auto">{T('跟随系统','System',l)}</option></select></div></div>{body}<footer class="site-footer"><p>© Copyright DPVR. All Rights Reserved</p><p>沪ICP备2022019614号-1 Shanghai Lexiang Technology Co. Ltd</p></footer><dialog class="search-dialog" aria-label="{T('搜索文档','Search documentation',l)}"><form class="search-form"><input id="search-query" name="q" type="search" placeholder="{T('搜索产品、操作或接口…','Search a product, task or API…',l)}" aria-label="{T('关键词','Search terms',l)}"><button type="button" class="search-close" aria-label="{T('关闭搜索','Close search',l)}">✕</button></form><div class="search-status" role="status"></div><div class="search-results"></div></dialog></body></html>'''

def addsearch(title,text,path,l,pid,kind):search.append({'title':title,'text':' '.join(text.split()),'url':path,'language':l,'product':L(prod[pid]['title'],l) if pid in prod else T('使用帮助','Support',l),'productId':pid,'kind':kind})
def readlinks(pid,l,limit=None):
 ps=[p for p in pages if p['product']==pid and p['language']==l]
 return ps[:limit] if limit else ps

def page_label(p,l):
 title=p['title'];path=p['path']
 if 'ReleaseNote' in path:return T('更新日志','Release notes',l)
 if path.endswith('/Introduction.html'):return T('功能与调用模型','Concepts & capabilities',l)
 if '/GettingStarted/android/' in path:return T('Android · ','Android · ',l)+title
 if '/GettingStarted/unity/' in path:return T('Unity · ','Unity · ',l)+title
 if l=='cn':
  if 'ReleaseNote' in path:return '更新记录'
  if path.endswith('/Introduction.html'):return '功能与调用模型'
  if title in ['Apis','API','Api List']:return 'API分类索引'
  if title=='Getting Started':return '环境与授权要求'
  if title=='Android Developer':return 'Android接入'
  if title=='Unity Developer':return 'Unity接入'
  if title in CAT:return CAT[title]+'接口'
  if title.lower()=='index':return '分类概览'
 return title
def doclist(ps,l):return '<ul class="reading-list">'+''.join(f'<li><a href="{E(p["path"])}">{E(page_label(p,l))}</a></li>' for p in ps)+'</ul>'
def stephtml(steps,l):
 s='<div class="steps">'
 for i,x in enumerate(steps):
  href=mapdoc(x.get('docMatch',''),l);title=x['title'].lower()
  if href.endswith('/copy-tool-guide.html'):href+='#section-'+('1' if any(k in title for k in ['json','配置','task','任务']) else '2')
  if href.endswith('/videoplay-config.html'):href+='#section-'+('2' if any(k in title for k in ['放置','交付','place','deploy']) else '0')
  link=f'<a class="text-link" href="{E(href)}">{T("阅读：","Read: ",l)}{E(x["title"])} →</a>' if href else ''
  code='<pre><code>'+E(x['code'])+'</code></pre>' if x.get('code') else ''
  s+=f'<article class="step"><span class="step-number">{i+1:02}</span><div><h3>{E(x["title"])}</h3><p>{E(x["body"])}</p>{code}{link}'+(f'<figure><img src="{E("/"+x["image"].lstrip("/"))}" alt="{E(L(x.get("imageAlt",""),l))}"><figcaption>{E(L(x.get("imageAlt",""),l))}</figcaption></figure>' if x.get('image') else '')+'</div></article>'
 return s+'</div>'
def group_label(key,l):
 d={'GettingStarted':('接入与基础概念','Getting started'),'Apis':('API参考','API reference'),'Events':('事件参考','Events'),'Types':('数据类型','Data types'),'Examples':('代码示例','Examples'),'lib_dev':('C# 服务端开发','C# server development'),'client_usage':('头显端设置','Headset configuration'),'client_app':('自定义应用透传','Custom app messaging'),'server_dev':('通信协议','Communication protocol'),'Guides':('操作指南','Guides'),'Assets':('首次接入','Getting started'),'CLI Version':('命令行与开发参考','CLI & developer reference'),'GUI Version':('图形界面操作','GUI workflow')}
 return T(*d[key],l) if key in d else key
CAT={'activityJobs':'应用活动','bluetoothJobs':'蓝牙','displayJobs':'显示','fileJobs':'文件','inputJobs':'输入','mediaJobs':'媒体与投屏','networkJobs':'网络','packageJobs':'应用安装与管理','powerJobs':'电源','remotecontrolJobs':'RDC通信','sensorJobs':'传感器','systemInfoJobs':'设备信息','systemJobs':'系统设置','wifiJobs':'Wi-Fi','wifidisplayJobs':'系统投屏','storageJobs':'存储','batteryJobs':'电池','controllerJobs':'控制器','authorityJobs':'授权','messageJobs':'消息','settingJobs':'系统设置','otaJobs':'固件升级','daemonJobs':'后台服务','locationJobs':'定位','index':'全部API分类','downloadJobs':'下载','messengerJobs':'应用消息','sampleJobs':'调用样例'}
def sidenav(pid,l,current):
 name=L(prod[pid]['title'],l) if pid in prod else T('设备使用帮助','Device support',l)
 s=f'<aside class="product-nav" id="product-nav"><h2>{E(name)}</h2><nav><a class="nav-overview" href="{overview(pid,l) if pid in prod else "/"+l+"/index.html"}">{T("用途与开始使用","Overview & start",l)}</a>'
 for j in journeys:
  if pid in j.get('products',[]) and (pid!='encryption' and pid!='copy'):
   s+=f'<a href="{guide(j["id"],l)}">{E(L(j["title"],l))}</a>'
 groups=defaultdict(list)
 for p in readlinks(pid,l):
  if pid=='dm' and p['path'].endswith('/docs/dm/index.html'):continue
  section=p.get('section','');key=section.split('/')[0] if section else 'Overview';groups[key].append(p)
 order=['Overview','GettingStarted','Apis','Events','Types','Examples','client_usage','lib_dev','client_app','server_dev']
 for key in sorted(groups,key=lambda x:(order.index(x) if x in order else 99,x)):
  ps=groups[key];active=any(p['path']==current for p in ps);label=group_label(key,l)
  if key in ['Overview','ReleaseNote','Introduction']:
   for p in ps:s+=f'<a class="{"active" if p["path"]==current else ""}" href="{p["path"]}">{E(page_label(p,l))}</a>'
   continue
  s+=f'<details {"open" if active else ""}><summary>{E(label)}</summary>'
  if key=='Apis':
   cats=defaultdict(list)
   for p in ps:cats[p['section'].split('/')[1] if '/' in p['section'] else 'index'].append(p)
   for cat,items in cats.items():
    s+=f'<details {"open" if any(p["path"]==current for p in items) else ""}><summary>{E(CAT.get(cat,cat) if l=="cn" else cat)}</summary><ul>'
    for p in items:s+=f'<li><a class="{"active" if p["path"]==current else ""}" href="{p["path"]}">{E(page_label(p,l))}</a></li>'
    s+='</ul></details>'
  elif key=='GettingStarted':
   for p in ps:
    if '/android' not in p['path'] and '/unity' not in p['path']:s+=f'<a href="{p["path"]}">{E(page_label(p,l))}</a>'
   for platform,label in [('android','Android'),('unity','Unity')]:
    items=[p for p in ps if '/'+platform in p['path']]
    s+=f'<details {"open" if any(p["path"]==current for p in items) else ""}><summary>{label}</summary><ul>'
    for p in items:s+=f'<li><a class="{"active" if p["path"]==current else ""}" href="{p["path"]}">{E(page_label(p,l))}</a></li>'
    s+='</ul></details>'
  else:
   s+='<ul>'+''.join(f'<li><a class="{"active" if p["path"]==current else ""}" href="{p["path"]}">{E(page_label(p,l))}</a></li>' for p in ps)+'</ul>'
  s+='</details>'
 return s+'</nav></aside>'

def reader(content,title,pid,l,path,source=None,notes=None,translation=None,pagination='',editorial=False):
 source_link=f'<a href="{E(source)}">{T("官方来源","Official source",l)} ↗</a>' if source else ''
 ns=''.join(f'<p>{E(L(n,l) if isinstance(n,dict) else n)}</p>' for n in notes or [])
 body=f'<div class="reader-controls"><button class="reader-menu" aria-controls="product-nav" aria-expanded="false">☰ {T("文档导航","Documentation",l)}</button><button class="toc-menu" aria-controls="page-toc" aria-expanded="false">{T("本页目录","On this page",l)} ☷</button></div><div class="reader-layout">'+sidenav(pid,l,path)+f'<main id="main" class="article-main"><div class="breadcrumbs"><a href="/{l}/index.html">{T("资源","Resources",l)}</a> / <a href="{overview(pid,l) if pid in prod else "/"+l+"/index.html"}">{E(L(prod[pid]["title"],l) if pid in prod else T("使用帮助","Support",l))}</a></div><header class="article-header"><span class="eyebrow">{T("操作引导","Practical guide",l) if editorial else T("技术文档","Documentation",l)}</span>{source_link}</header>'+ (f'<aside class="editorial-note">{ns}</aside>' if ns else '')+f'<article class="article-body">{content}</article>{pagination}</main><aside class="page-toc" id="page-toc"><h2>{T("本页目录","On this page",l)}</h2><nav></nav></aside></div><button class="drawer-scrim" aria-label="{T("关闭目录","Close navigation",l)}"></button>'
 result=shell(title,body,l,path,translation,pid)
 if translation=='':result=re.sub(r'<a class="language-link"[^>]*>.*?</a>', '<span class="language-unavailable">'+T('暂无对应英文','No matching Chinese page',l)+'</span>',result)
 return result

# Static assets are authored independently; no copied legacy application shell.
shutil.copytree(R/'assets',OUT/'assets',dirs_exist_ok=True)
for l in ['cn','en']:
 groups=[('develop',T('开发头显应用','Build headset applications',l),T('在自己的应用中调用系统能力、播放媒体或接入手势。','Add system controls, media playback or gesture input to your app.',l),['dm','player','gesture']),('deploy',T('部署与播放内容','Prepare and deploy content',l),T('配置播放体验、制作授权内容，再按需要分发到设备。','Configure playback, authorize content and distribute it when needed.',l),['encryption','playback','copy']),('operate',T('连接与管理设备','Connect and manage devices',l),T('直接使用电脑工具与投屏，或开发自己的局域网群控。','Use PC tools and casting, or build your own LAN control system.',l),['go2','go','cast','rdc'])]
 body=f'<main id="main" class="hub container"><header class="page-intro"><span class="eyebrow">DPVR / {T("开发者资源","RESOURCES",l)}</span><h1>{T("开发者资源","Developer resources",l)}</h1><p>{T("从设备管理到应用开发，先选资源，再按步骤开始。","From device operations to app development: choose a resource, then follow its guide.",l)}</p></header>'
 devices=sorted({d for p in products for d in p['devices']})
 body+=f'<section class="catalog-toolbar"><div><h2>{T("全部资源","All resources",l)}</h2><p id="filter-status" role="status">{T("10项当前资源 · 按需求选择","10 current resources · Choose by task",l)}</p></div><label>{T("你的设备","Your headset",l)} <select id="device-filter"><option value="">{T("全部型号","All models",l)}</option>'+''.join(f'<option>{E(d)}</option>' for d in devices)+'</select></label></section>'
 for key,title,desc,ids in groups:
  body+=f'<section class="catalog-section" id="{key}"><h2>{title}</h2><p>{desc}</p><div class="resource-grid">'
  for pid in ids:
   p=prod[pid];title=L(p['title'],l)
   body+=f'<article class="resource-card" data-devices="{E(json.dumps(p["devices"]))}"><span class="resource-kind">{E(L(p["kind"],l))}</span><h3><a class="resource-title" href="{overview(pid,l)}">{E(title)}</a></h3><p>{E(L(p["summary"],l))}</p><div class="device-tags">'+''.join(f'<span>{E(d)}</span>' for d in p['devices'])+f'</div><div class="card-actions"><a class="text-link" href="{overview(pid,l)}">{T({'dm':'接入设备能力','player':'集成播放器','gesture':'运行手势示例','encryption':'制作授权视频','playback':'配置自动播放','copy':'部署文件与应用','go':'安装与管理设备','go2':'连接并操作设备','cast':'选择投屏方式','rdc':'开发局域网群控'}[pid],{'dm':'Integrate device controls','player':'Embed a player','gesture':'Run the gesture sample','encryption':'Authorize video content','playback':'Configure playback','copy':'Deploy files & apps','go':'Install & manage devices','go2':'Connect your headset','cast':'Choose a casting method','rdc':'Build LAN device control'}[pid],l)} →</a></div></article>'
  body+='</div></section>'
 body+=f'<section class="support-links"><h2>{T("设备使用帮助","Device help",l)}</h2>'+''.join(f'<a href="{p["path"]}">{E(p["title"])} →</a>' for p in pages if p['language']==l and p['product'] in ['firmware','troubleshooting'])+'</section></main>'
 hub=shell(T('开发者资源','Developer resources',l),body,l,f'/{l}/index.html')
 emit(f'/{l}/index.html',hub)
 if l=='cn':
  emit('/index.html',hub);emit('/resource.html',hub)
 for pid,p in prod.items():
  path=overview(pid,l);title=L(p['title'],l);steps=L(p['steps'],l);pre=L(p['prerequisites'],l);trouble=L(p['troubleshooting'],l);caution=L(p.get('caution',''),l)
  dl_label=T({'dm':'下载设备管理SDK','rdc':'下载远程控制开发包','go':'下载Windows安装包','go2':'下载Windows便携工具','cast':'下载电视接收端APP','encryption':'下载加密工具','playback':'下载JSON示例','copy':'下载设备端APK与配置','player':'下载Unity播放器插件','gesture':'下载Unity手势集成包'}[pid],{'dm':'Download Device Manager SDK','rdc':'Download remote control kit','go':'Download Windows installer','go2':'Download portable Windows tool','cast':'Download receiver app','encryption':'Download encryption tools','playback':'Download JSON example','copy':'Download headset app & config','player':'Download Unity player plugin','gesture':'Download Unity gesture kit'}[pid],l)
  first=next((j for j in journeys if (pid,j['id']) in [('dm','dms-android'),('gesture','gesture-start'),('playback','video-deploy'),('rdc','rdc-csharp'),('go','go-start')]),None)
  cta=guide(first['id'],l) if first else '#start'
  if pid=='dm':cta='#platform'
  body=f'<main id="main" class="container product-layout"><article class="product-main"><span class="eyebrow">{E(L(p["kind"],l))}</span><h1>{E(title)}</h1><p class="lead">{E(L(p["summary"],l))}</p><p class="compatibility"><strong>{T('适用设备：','Supported headsets: ',l)}</strong>{E(' · '.join(p['devices']))}</p><p class="product-limit">{E(caution)}</p><div class="actions"><a class="button primary" href="{cta}">{T("选择Android或Unity","Choose Android or Unity",l) if pid=="dm" else T("开始使用","Get started",l)} →</a><a class="button" href="{E(p["download"])}">{dl_label} ↗</a></div>'
  body+=f'<dl class="product-context"><dt>{T("适合谁","Who it is for",l)}</dt><dd>{E(L(p["audience"],l))}</dd><dt>{T("运行在哪里","Where it runs",l)}</dt><dd>{E(L(p["runtime"],l))}</dd></dl>'
  if pid=='dm':body+=f'<section id="platform"><h2>{T("选择开发平台","Choose your platform",l)}</h2><div class="platform-options">'+''.join(f'<a class="task-card" href="{guide("dms-"+plat,l)}"><h3>{name}</h3><p>{desc}</p></a>' for plat,name,desc in [('android','Android',T('AIDL服务绑定与异步调用','AIDL binding and asynchronous calls',l)),('unity','Unity',T('导入插件，通过Java bridge调用','Import the plugin and use the Java bridge',l))])+'</div></section>'
  if pid=='rdc':body+=f'<div class="topology" aria-label="{T("一个控制端连接多台头显","One controller connects to multiple headsets",l)}"><strong>{T("你的控制端","Your controller",l)}</strong><span>⟷ TCP / LAN ⟷</span><strong>{T("多台DPVR头显","Multiple DPVR headsets",l)}</strong></div>'
  body+=f'<section><h2>{T("开始前确认","Before you begin",l)}</h2><ul>'+''.join(f'<li>{E(x)}</li>' for x in pre)+'</ul></section>'
  if pid!='dm':body+=f'<section id="start"><h2>{T("按步骤完成","Follow the workflow",l)}</h2>'+stephtml(steps,l)+'</section>'
  if trouble:body+=f'<section><h2>{T("遇到问题时","When something goes wrong",l)}</h2><ul>'+''.join(f'<li>{E(x)}</li>' for x in trouble)+'</ul></section>'
  refs=readlinks(pid,l)
  if refs:
   if pid=='dm':refs=[x for x in refs if not x['path'].endswith('/docs/dm/index.html') and (x['section'] in ['Overview','Introduction','ReleaseNote'] or x['path'].endswith('/Apis/index.html') or x['path'].endswith('/GettingStarted/index.html'))]
   body+=f'<section id="reference"><h2>{T("文档与参考","Documentation & reference",l)}</h2>'+doclist(refs,l)+'</section>'
  body+='</article><aside class="product-facts">'
  body+=f'<section class="fact-card"><h3>{T("相关资源","Related resources",l)}</h3>'+''.join(f'<a href="{overview(x,l)}">{E(L(prod[x]["title"],l))} →</a>' for x in {'dm':['rdc','player'],'rdc':['dm','cast'],'go':['go2'],'go2':['go','cast'],'cast':['go2','rdc'],'encryption':['playback','copy'],'playback':['copy','encryption'],'copy':['playback','encryption'],'player':['encryption','gesture'],'gesture':['player']}[pid])+'</section></aside></main>'
  context=re.search(r'<dl class="product-context">.*?</dl>',body).group(0)
  body=body.replace(context,'').replace('<div class="actions">',context+'<div class="actions">',1)
  if pid=='dm':
   section=re.search(r'<section><h2>'+T('开始前确认','Before you begin',l)+r'.*?</section>',body).group(0)
   body=body.replace(section,'').replace('<section id="platform">',section+'<section id="platform">')
  emit(path,shell(title,body,l,path,overview(pid,'en' if l=='cn' else 'cn'),pid));addsearch(title,H.fromstring(body).text_content(),path,l,pid,T('资源概览','Resource overview',l))
 for j in journeys:
  pid='playback' if j['id']=='video-deploy' else j['products'][0];path=guide(j['id'],l);title=L(j['title'],l)
  body=f'<h1>{E(title)}</h1><p class="lead">{E(L(j["summary"],l))}</p>'
  if j['id']=='dms-start':body+=f'<div class="platform-options"><a class="button primary" href="{guide("dms-android",l)}">Android / AIDL →</a><a class="button" href="{guide("dms-unity",l)}">Unity →</a></div>'
  body+=f'<h2>{T("准备条件","Prerequisites",l)}</h2><ul>'+''.join(f'<li>{E(x)}</li>' for x in L(j['prerequisites'],l))+'</ul>'+stephtml(L(j['steps'],l),l)
  body+=L(j.get('verificationTable',''),l)
  caution=L(j.get('caution',''),l)
  if caution:body+=f'<aside class="editorial-note">{E(caution)}</aside>'
  note=T('以下为依据官方资料整理的操作顺序；各步骤链接保留完整技术原文。','This workflow is organized from official documentation. Step links retain the full technical reference.',l)
  tutorial=R/'content/tutorials'/f'{j["id"]}.{l}.html'
  if tutorial.exists():body=tutorial.read_text()
  if j['id']=='rdc-csharp':
   controller=T('C# 控制端','C# controller',l);headset=T('头显','Headset',l)
   diagram=f'<svg class="rdc-diagram" viewBox="0 0 620 180" role="img" aria-label="{controller} TCP LAN {headset} 1 2 3"><rect x="15" y="65" width="170" height="55" rx="8" fill="#292929"/><text x="100" y="98" text-anchor="middle" fill="white" font-size="18">{controller}</text><path d="M185 93 H310 M310 30 V150 M310 30 H420 M310 90 H420 M310 150 H420" fill="none" stroke="#e72d12" stroke-width="2"/><text x="245" y="75" text-anchor="middle" fill="#777" font-size="13">TCP / LAN</text>'+''.join(f'<rect x="420" y="{y}" width="180" height="44" rx="6" fill="#f4f4f4" stroke="#ddd"/><text x="510" y="{y+28}" text-anchor="middle" fill="#333" font-size="16">{headset} {i+1}</text>' for i,y in enumerate([8,68,128]))+'</svg>'
   body=body.replace('</h1>','</h1>'+diagram,1)
  emit(path,reader(body,title,pid,l,path,notes=[],translation=guide(j['id'],'en' if l=='cn' else 'cn'),editorial=True));addsearch(title,H.fromstring(body).text_content(),path,l,pid,T('使用引导','Practical guide',l))
# Representative mode keeps the same navigation/data but renders a focused slice first.
selected=pages
if '--representative' in sys.argv:selected=[p for p in pages if any(k in p['path'] for k in ['GettingStarted/','GetSerialNo.html','GetRunningPackages.html','videoplay','SampleScene']) or p['product'] in ['playback','gesture','copy']]
for p in selected:
 l=p['language'];path=p['path'];content=(R/p['content']).read_text();tree=H.fromstring(content)
 for i,h in enumerate(tree.xpath('.//h2|.//h3')):
  if not h.get('id'):h.set('id','section-'+str(i))
 content=H.tostring(tree,encoding='unicode');notes=[] # importer places sourced editorial notes in the article
 if '/Apis/' in path and not path.endswith('/index.html'):
  category=path.split('/Apis/',1)[1].split('/')[0];method=path.rsplit('/',1)[1][:-5]
  if category!=method:
   details=f'<aside class="api-call-info" data-editorial-note="true"><p><code>jobCat = {E(category)}</code> · <code>jobType = {E(method)}</code></p>'
   if method=='GetSerialNo':
    details+=f'<p>{T("无参数：jobParams可为空。","No parameters: jobParams may be null.",l)} <a href="{guide("dms-android",l)}">{T("完整Android首调用示例","Complete first Android call",l)}</a> · <a href="{guide("dms-unity",l)}">Unity</a></p>'
    # Clarify the empty source Params section without changing its original heading.
    for h in tree.xpath('.//h2'):
     if 'Params' in h.text_content():
      note=H.Element('p');note.set('data-editorial-note','true');note.text=T('无参数（jobParams可为空）。','No parameters (jobParams may be null).',l);h.addnext(note)
    content=H.tostring(tree,encoding='unicode')
   content=details+'</aside>'+content
 if not tree.xpath('.//h1'):
  content='<h1 data-editorial-note="navigation-title">'+E(p['title'])+'</h1>'+content
 if p.get('downloads'):
  downloads=list({x['url']:x for x in p['downloads']}.values())
  content+='<section class="source-downloads" data-editorial-note="true"><h2>'+T('本页下载','Page downloads',l)+'</h2><ul>'+''.join('<li><a href="'+E(x['url'])+'">'+E(('Download official package' if x.get('sourceMember') else x['title']) if l=='en' else x['title'])+'</a></li>' for x in downloads)+'</ul></section>'
 pagination='<nav class="page-turn">'+''.join(f'<a href="{E(p[k])}"><small>{T(cn,en,l)}</small><span>{E(by_path.get(p[k],{}).get("title",""))}</span></a>' for k,cn,en in [('previous','上一篇','Previous'),('next','下一篇','Next')] if p.get(k) in by_path)+'</nav>'
 if '/Apis/' in path:
  category_path=path.rsplit('/',1)[0]+'/index.html'
  related=[x for x in pages if x['language']==l and x['product']=='dm' and x['section']==p['section'] and x['path']!=path and not x['path'].endswith('/index.html')][:2]
  pagination='<nav class="page-turn">'+(f'<a href="{category_path}">{T("返回本类接口","Back to this API category",l)}</a>' if category_path in by_path else '')+''.join(f'<a href="{x["path"]}"><small>{T("同类参考","Related reference",l)}</small><span>{E(page_label(x,l))}</span></a>' for x in related)+'</nav>'
 emit(path,reader(content,p['title'],p['product'],l,path,p['source'],notes,p.get('translation') or '',pagination));addsearch(p['title'],H.fromstring(content).text_content(),path,l,p['product'],T('API参考','API reference',l) if '/Apis/' in path else T('技术文档','Documentation',l))
for l in ['cn','en']:
 body=f'<main id="main" class="container search-page"><h1>{T("搜索文档","Search documentation",l)}</h1><p>{T("按产品、任务或API名称搜索当前内容。","Search current content by product, task or API name.",l)}</p><form class="inline-search"><input name="q" type="search" aria-label="{T("搜索词","Search query",l)}"><button class="button primary">{T("搜索","Search",l)}</button></form><div class="inline-results"></div></main>'
 emit(f'/{l}/search.html',shell(T('搜索','Search',l),body,l,f'/{l}/search.html',f'/{"en" if l=="cn" else "cn"}/search.html'))
# Compatibility starts in Chinese. The entry remains real content rather than a blank redirect.
(OUT/'assets/search-index.js').write_text('window.DPVR_SEARCH='+json.dumps(search,ensure_ascii=False)+';')
print(json.dumps({'documents':len(selected),'resources':len(products)*2,'guides':len(journeys)*2,'searchEntries':len(search),'html':len(list(OUT.rglob('*.html')))},ensure_ascii=False))
