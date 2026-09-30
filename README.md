# DPVR 开发者资源

围绕真实任务组织的静态资源站：10项当前产品/工具，中文默认，同篇英文切换。官网黑红品牌页头与页脚；产品概览、操作引导和技术参考分层。没有部署或开通服务。

## 本地预览

```bash
python3 -m http.server 8080 --directory public
```

访问 http://localhost:8080 。`public/` 是可以直接托管的静态HTML/CSS/JS，无运行时框架或后端。

## 重建

```bash
python3 -m pip install -r requirements.txt
python3 tools/build.py
```

`content/products.json` 与 `journeys.json` 是有来源的双语编排；`content/articles/` 保留当前技术正文；`content/pages.json` 维护来源、显式语言映射和下载。`assets/` 是独立编写的样式、交互与所需正文图像。`public/` 是生成结果。

`tools/import_content.py` 用于维护者从仓库外证据重新导入，不是日常构建前置。仓库不包含原始抓取快照、旧DM/RDC文档、测试输出或大型SDK。当前官方软件包与SDK链接直接指向对应原下载，不用历史同名文件替代。

## 部署路径

默认把public内容作为官网资源区的根路径结构使用：`/cn/`、`/en/`、`/assets/`及`/resource.html`。为避免覆盖官网现有assets，正式集成时推荐使用独立子目录构建：运行 `python3 tools/build.py --base /dpvr-resources`，把public内文件上传到官网 `/dpvr-resources/`。保留官网根 `/resource.html` 时使用下述兼容入口。请由官网维护者备份原入口后部署；本项目只提交代码，不发布网站。

## 内容边界

保留440份现行DMS/RDC技术正文、14份共享指南、当前加密手册、当前手势入门/参数以及JSON示例。手势同流程合并为一份当前入门；GO与GO2都仍发布，型号不同，均保留。当前Release Note保留，GUI 2.0.0与加密V3不当作同一版本维度。资料中的待核实差异明确标注，未以文档重构冒充真机或SDK测试。

### 保留官网旧入口

生产构建时 `--base /dpvr-resources` 隔离资源路径，避免覆盖官网 assets。根目录旧resource.html可使用一个保留hash的跳转：

```html
<!doctype html><meta charset="utf-8"><title>DPVR Resources</title>
<a href="/dpvr-resources/cn/index.html">打开开发者资源</a>
<script>location.replace('/dpvr-resources/resource.html'+location.search+location.hash)</script>
```

此兼容页交由官网维护者部署，不会自动修改官网。更新静态文件后需保持完整目录结构；本地默认根路径构建无需此跳转。

信息架构和真实任务验收目标见 `docs/information-architecture.md`。
