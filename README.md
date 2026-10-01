# DPVR 开发者资源

10 项当前资源按三种任务组织：开发头显应用、部署播放内容、连接管理设备。中文默认，每篇文章切换到对应英文；保留完整正文、代码、JSON、表格、图片、全文搜索、复制代码、图片放大和手机目录。官网黑红样式；未部署官网。

> 日常浏览请使用独立的 `DPVR-resources-static-20261001.zip`，全部解压后直接打开根层 `index.html`。源码包的 `content/articles/*.html` 是无样式正文片段，不是网站入口，不能直接用于浏览验收。

## Windows 打开源码包中的预览

1. 在 ZIP 上选择“全部解压”，保留整个 `DpvrDeveloperNew` 目录。不要只拖出一个 HTML，也不要在压缩软件里直接预览。
2. 入口是 `DpvrDeveloperNew\public\index.html`（或 `public\resource.html`）。CSS、JS、图片与所有站内链接使用相对路径；搜索索引由本地普通脚本加载，不依赖 fetch、CDN、构建服务或互联网。
3. `file://` 路径解析已全量检查，但本次云环境的受管浏览器禁止本地文件导航，**没有完成 Windows 双击打开的浏览器实测**。HTTP 浏览已实际验证。若电脑策略也禁止本地网页，在 `DpvrDeveloperNew` 目录打开终端，使用已安装的 Python：

```powershell
py -m http.server 8080 --directory public
```

浏览器打开 `http://localhost:8080/`。无需 npm。该命令只用于本机预览，不是部署官网。复制操作如被浏览器权限拒绝，可选中代码手动复制。

Windows 文件系统路径可用反斜杠；网页 URL 仍用正斜杠。保留文件名大小写和目录层级，不改名 `AutoPlayDisposition.json` 等正文示例。所有文件为 UTF-8。下载 SDK、官方来源和页头其他官网栏目需要联网。

## 重建与子目录部署

```bash
python3 -m pip install -r requirements.txt
python3 tools/build.py
python3 tools/build.py --base /dpvr-resources
```

最后一条构建适用于 `/dpvr-resources/`。由于站内链接都为相对地址，构建产物同时可移到其他完整目录；`--base` 保留部署标识，不再把资源固定到网站根目录。将 **public 内的全部内容** 放到目标子目录即可。项目不会自动发布。

如果官网维护者将旧的根 `/resource.html` 指向新的子目录，应保留 query/hash：

```html
<!doctype html><meta charset="utf-8"><title>DPVR Resources</title>
<a href="/dpvr-resources/index.html">打开开发者资源</a>
<script>location.replace('/dpvr-resources/resource.html'+location.search+location.hash)</script>
```

`resource.html#content-device-manager` 等 10 个原入口跳到对应当前产品；网站没有旧版入口。

## 源码和覆盖

- `content/products.json`：10 个产品的用途、人群、运行位置、型号、条件与流程。
- `content/articles/` 与 `pages.json`：474 篇正文及来源/译文/下载映射。
- `content/tutorials/`、`journeys.json`：任务教程；原文与整理内容区分维护。
- `assets/`：样式、交互、文档图片；`public/`：512 个生成 HTML 和本地资源。
- `tools/build.py`：日常构建无需原始采集包。`tools/import_content.py` 是旧采集格式的维护工具，不是构建前置。
- [覆盖表](docs/content-coverage.csv)、[验收报告](docs/verification.md)、[缺陷与修复](docs/defects.md)、[原文与编排边界](docs/source-consistency.md)。

不纳入 Git 或源码 ZIP：原始采集快照、测试截图、大型 SDK、缓存、旧 DMS/RDC 安装包中的历史文档。当前 GO 与 GO2、当前 GUI 2.0.0 手册、Release Note 都保留。

## 复核

静态核验针对解压后的 `public`，而不是只针对开发目录：

```bash
python3 tools/audit_delivery.py --site /path/to/unpacked/DpvrDeveloperNew/public --output /tmp/dpvr-audit
python3 tools/check_external.py /tmp/dpvr-audit/external-links.json /tmp/dpvr-audit/external-results.json
python3 tools/package_delivery.py /tmp/DPVR-resources-static.zip --kind static
python3 tools/package_delivery.py /tmp/DPVR-resources-source.zip --kind source
```

ZIP 含逐文件 `SHA256SUMS.json`。全量独立原文核验需要两份授权采集包，不随源码再分发；先运行 `tools/prepare_reference.py --core CORE.zip --supplement SUPPLEMENT.zip --output EVIDENCE`，再给 `audit_delivery.py` 传 `--evidence EVIDENCE`。参考渲染需要 Node、`playwright`、`marked` 和 Chromium；可用 `CHROMIUM_BIN` 指定浏览器。

`tools/audit_browser.cjs` 验证解压目录，默认根预览端口 8767、子目录端口 8768。先分别运行静态服务，使用 `DPVR_SITE` 指定解压后的 public，`DPVR_AUDIT` 指定报告输出目录。它保存逐页 CSS/图片/运行错误/宽度检查和桌面手机截图；`DPVR_TASKS_ONLY=1` 仅复跑交互旅程。报告和截图放在独立证据 ZIP。

本次验收不等于在头显运行 SDK，也未证明被网络代理阻断的官方外链当前可用，详见验收报告。
