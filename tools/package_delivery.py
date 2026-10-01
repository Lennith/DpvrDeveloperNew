#!/usr/bin/env python3
"""Separate end-user static ZIP from maintainable source ZIP; never ship captures."""
import argparse,hashlib,json,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);ap.add_argument('--kind',choices=['static','source'],default='source');a=ap.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
if a.kind=='static':
 files={str(p.relative_to(R/'public')):p.read_bytes() for p in (R/'public').rglob('*') if p.is_file()}
 files['START_HERE.txt']=('''DPVR 开发者资源 — 静态站点使用说明\n\n1. 先“全部解压”整个ZIP，保留index.html、assets、cn、en的相对位置。\n2. 入口就是本目录的index.html（中文默认），或resource.html。不要在压缩软件内预览。\n3. 本包只有可使用的网站，不包含无样式源码片段。搜索数据、CSS、JS、图片都在包内。\n4. 浏览器如果允许本地file://网页，可双击index.html。本次受管云浏览器禁止file://导航，因此没有完成Windows双击实测；相对路径静态检查通过不等于浏览器实测通过。\n5. 已实际通过HTTP根目录及/dpvr-resources/子目录的桌面/手机检查。若本机策略禁用本地网页，在解压目录打开终端（需Python）：\n   py -m http.server 8080\n   然后打开 http://localhost:8080/ 。无需npm。\n6. SDK下载和官方来源等外链需要互联网。本次运行环境代理阻止了外链探测，不能保证当前下载可达。\n7. 使用正斜杠URL；不要改文件名大小写或拆散目录。文本为UTF-8。代码复制受浏览器权限影响，可手动选中复制。\n8. SHA256SUMS.json记录本包文件哈希。未部署官网，未在头显运行SDK。详细覆盖与已知边界见单独证据包。\n''').encode('utf-8-sig')
else:
 paths=[p for d in ['assets','content','docs','public','tools'] for p in (R/d).rglob('*') if p.is_file() and '__pycache__' not in p.parts]+[R/'README.md',R/'requirements.txt',R/'.gitignore']
 files={'DpvrDeveloperNew/'+str(p.relative_to(R)):p.read_bytes() for p in paths}
 files['SOURCE_README.txt']='源码包：正常浏览请下载单独静态站点ZIP；本包预览入口为DpvrDeveloperNew/public/index.html。content/articles/*.html是用于构建的无样式正文片段，不是网站页面，请勿直接打开作为网站验收。详细说明见DpvrDeveloperNew/README.md。\n'.encode('utf-8-sig')
manifest={n:hashlib.sha256(b).hexdigest() for n,b in sorted(files.items())}
with zipfile.ZipFile(a.output,'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in sorted(files.items()):z.writestr(n,b)
 z.writestr('SHA256SUMS.json',json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'file':str(a.output),'kind':a.kind,'bytes':a.output.stat().st_size,'sha256':hashlib.sha256(a.output.read_bytes()).hexdigest(),'files':len(files)}))
