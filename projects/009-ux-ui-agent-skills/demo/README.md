# 中文 Web 能力导览

原创静态研究页面，整理 17 项技能、工作原理、场景、扩展方向和固定提交的源码依据。页面不调用模型、不连接 Figma、不执行上游技能。主题切换为本页自制的 Token 概念示例。

## 文件与发布

- `standards.html`：公开标准、社区规范、实践指南、设计方法与作者偏好的区分；六案例与 Skill 的能力映射；强模型条件下的采用判断。公开依据于 2026-09-07 核对，页面链接到 WCAG、APG、DTCG 原文。映射不声称逐案例的生成过程，价值判断未做对照实测。

- `index.html`：语义结构与研究内容。
- `styles.css`：响应式布局；无外部字体和图片依赖。
- `app.js`：技能筛选与搜索、详情、主题示意、场景切换。
- `effects.html` / `effects.css` / `effects.js`：六个原始示例的中文体验导航。
- `samples/`：从上游固定提交原样收录的八个示例与依赖文件，内容哈希与上游一致。
- `THIRD_PARTY_NOTICES.md` / `LUCIDE_LICENSE.txt`：来源说明与图标许可。
- `build.ps1`：将静态页面、样例与许可复制到 `docs/demos/009-ux-ui-agent-skills/`。
- `verify.cjs`：本地浏览器验证；依赖 Playwright 和 Chromium 或 Edge，仅验证本页。

从工作区根目录执行：

```powershell
./projects/009-ux-ui-agent-skills/demo/build.ps1
python -m http.server 8099 --bind 127.0.0.1 --directory docs
```

本地访问 `http://127.0.0.1:8099/demos/009-ux-ui-agent-skills/`。页面为纯静态文件，资源采用相对路径，可放入 GitHub Pages 子路径；GitHub Pages 已配置从 main 分支的 /docs 自动发布。

另开终端运行：

```powershell
node projects/009-ux-ui-agent-skills/demo/verify.cjs
```

Playwright 需在 Node 的模块搜索路径中。可传入另一个本地页面地址作为参数。截图输出到工作区忽略目录 `.cache/009-web-qa/`。

## 内容与来源

内容来自本子项目的源码研究笔记。页面源码链接固定到 `2ffb677aa02b225c8a3da1b7f31d9ebb7c38f1dd`；未使用上游图片、字体或复制其技能正文。上游 package.json 声明 MIT，根目录未见独立许可正文。

研究结论与本页功能验证分开：本页可交互不意味着上游技能效果已实测。

新增的 [真实示例体验](https://yydshly.github.io/0907_codex_project/demos/009-ux-ui-agent-skills/effects.html) 直接加载上游页面，可体验其已有产物，不是用新需求执行技能的生成实验。模拟邮件、删除、保存及固定状态均在中文侧栏标注。样例原始内容中的 verified 等措辞不代表本研究认证。

`verify-effects.cjs` 已检查六个样例加载、明暗主题、模拟导出、输入确认、表单选择、真实排序、全选、弹窗焦点约束与返回、窄屏预览及重置；四种窗口宽度下外层页面无横向溢出，未捕获脚本或 HTTP 错误。已检查桌面与手机截图。未运行上游完整 gate 或全面无障碍审计。

## 本页验证记录 · 2026-09-07

已通过浏览器检查：17 项技能及六类筛选结果、关键词搜索、无结果提示、重置、详情展开和键盘操作、三种主题、示例按钮、五个场景、试验详情、页内锚点及导航高亮。1440、1024、768、390、320 像素宽度下未发现页面横向溢出，未捕获页面脚本异常。已查看桌面、手机和原理区域截图。此记录不包含完整无障碍审计或上游功能实测。

[打开发布版](https://yydshly.github.io/0907_codex_project/demos/009-ux-ui-agent-skills/index.html) · [返回研究概览](../README.md)
