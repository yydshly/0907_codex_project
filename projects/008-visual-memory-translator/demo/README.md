# 中文能力展示

此目录是展示源码；发布副本位于 `docs/demos/008-visual-memory-translator/`。页面为原生 HTML/CSS/JavaScript，无安装依赖。

## 更新与预览

修改本目录 `index.html` 后，将其与 `THIRD_PARTY_NOTICES.md` 同步到发布目录。从仓库根目录运行：

```powershell
Copy-Item projects/008-visual-memory-translator/demo/index.html docs/demos/008-visual-memory-translator/index.html
Copy-Item projects/008-visual-memory-translator/demo/THIRD_PARTY_NOTICES.md docs/demos/008-visual-memory-translator/THIRD_PARTY_NOTICES.md
python -m http.server 8008 --directory docs
```

访问 `http://localhost:8008/demos/008-visual-memory-translator/`。静态发布无需构建；所有站内链接使用相对路径。不要把预计 Pages 地址当作已上线地址。

## 交互与边界

- 三个输入按钮切换照片、文本与图文混合的流程说明；这是规则演示，不生成图片。
- 样张引用固定提交的上游图片，需联网；失败时显示提示并保留来源链接。
- 页面包含响应式布局、键盘焦点、按钮选中状态、减少动画偏好支持。
- 能力事实、公开案例和扩展建议分别标注，扩展项不代表上游已实现。
