# 独立视觉复核 · 2026-10-01

两位独立审查代理实际查看图像像素，未以截图存在或自动化结果代替看图。

## 实际查看覆盖

- 18/18代表性完整PNG：index、go、dms、serial、tf、playback、rdc、gesture、encryption，各desktop/mobile。
- 为避免长图缩览掩盖问题，额外查看18张原像素切条拼图：GO/DMS/Playback/Encryption桌面正文全高，以及Index/GO/DMS/TF/Playback/RDC/Encryption手机全高。
- 16/16总览图：contact-sheets/desktop-00.jpg至07、mobile-00.jpg至07，覆盖512页×桌面/手机的1,024个首屏缩略画面。
- 放大核查原首屏：root-desktop/{040,070,246,257}.jpg；root-mobile/{008,070,189,246,301,389}.jpg。
- 实际对照已有官网资源页及页脚参考截图，未访问新增Library输入。

## 发现与处理

无P0/P1布局故障。黑页头、完整标识、五组桌面导航、红色RESOURCES、灰底白内容及黑底两行页脚一致。正文和两侧目录分区清晰，手机目录按钮未覆盖正文；任务入口、DMS首例、TF流程、RDC说明及Gesture动作表可读。未发现丢样式、列消失或文字重叠。

已修复一处P3实际缺陷：英文加密手册的①②及来源链接↗在受管Linux浏览器显示空心方框。核实源码字符正确后，在现有字体栈末端补充DejaVu Sans回退；实际裁片显示①②恢复，保留原文字符。共享CSS变化触发全量浏览器回归、截图刷新及证据指纹重建。独立代理另外实际查看修复后桌面/手机首屏与Launch共4张局部截图，确认①②↗显示正常、无新增遮挡或换行问题；证据包visual-fix目录保留这4张图。

保留的P3排版打磨项：手机四列表格中的description/packageName等较密集词内换行；UnregisterConfigureObserver标题末尾r独占一行；空查询搜索页下方灰底空白较多。均完整可读、无覆盖，并非阻断交付缺陷。长代码需横滚，手机软件截图需放大；截图本身不能证明这些交互有效，交互验收另列。

原文资料缺口：英文加密手册真实保留“Screenshot placeholder: single-add dialog & encryption progress dialog”。未伪造图片补齐，也不将该手册声称为全部截图齐全。

## 边界

总览用于比较首屏结构，不能逐字判读所有缩略小字；没有人工查看512篇长页全部屏幕。此次视觉审查不包括暗色模式、所有断点、展开菜单与sticky滚动状态、硬件、file://运行或实时外链。GO整本PDF缺口仍在。
