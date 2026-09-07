# Web 演示部署指南

## 多个演示的组织方式

GitHub Pages 每个仓库提供一个静态站点。本站使用首页加多个子路径承载不同演示：

```text
docs/index.html                        → /0907_codex_project/
docs/demos/001-project-name/index.html  → /0907_codex_project/demos/001-project-name/
docs/demos/002-project-name/index.html  → /0907_codex_project/demos/002-project-name/
```

默认站点地址预计为 `https://yydshly.github.io/0907_codex_project/`。当前仅准备目录和首页，尚未启用 GitHub Pages，不能将该地址视为已上线。

## 首次启用

1. 将仓库内容推送至 `main`。
2. 在 GitHub 仓库进入 **Settings → Pages**。
3. Source 选择 **Deploy from a branch**，分支选择 `main`，目录选择 `/docs`，保存。
4. 等待 Pages 发布成功，再访问 GitHub 显示的站点地址。
5. 验证首页和每个演示后，将真实在线地址写入主索引与对应研究页。

`docs/.nojekyll` 用于按原样发布静态资源。后续推送 `docs/` 的改动会触发站点更新。

## 新增演示

1. 将源码保存在 `projects/编号-slug/demo/`，记录运行与构建方式。
2. 将构建后的静态文件放入 `docs/demos/编号-slug/`，入口为 `index.html`；发布目录不要嵌套 `dist/` 或 `build/`。
3. 为项目配置 `/0907_codex_project/demos/编号-slug/` 这一资源基础路径，或使用正确的相对路径。不要默认资源位于域名根目录。
4. 在 `docs/index.html` 的演示列表中按编号添加相对链接，例如 `./demos/001-project-name/`，有首个演示时删除空状态提示。
5. 本地使用静态服务器预览 `docs/`，并验证部署后的图片、脚本和页面刷新。

GitHub Pages 只托管静态内容。有服务器、数据库或私密 API 的项目需要另外部署后端，在研究页中记录服务地址及配置方式。单页应用可优先使用 hash 路由；直接访问非静态文件路径时需另行设计回退方式。

未来若需要自动构建多个前端，可统一使用 GitHub Actions 构建并发布整站，届时再增加工作流。

参考：[GitHub Pages 介绍](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)、[发布源配置](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)。
