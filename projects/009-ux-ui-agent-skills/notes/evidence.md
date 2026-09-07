# 源码依据与能力边界

日期：2026-09-07。所有源码链接固定到研究提交，避免后续上游修改导致结论与依据不一致。

## 依据表

| 研究结论 | 源码依据 |
| --- | --- |
| 入口依靠模型理解路由和规则 | [CLAUDE.md](https://github.com/plugin87/ux-ui-agent-skills/blob/2ffb677aa02b225c8a3da1b7f31d9ebb7c38f1dd/CLAUDE.md) |
| 安装器主要复制文件；支持跳过现有文件等行为 | [bin/cli.js](https://github.com/plugin87/ux-ui-agent-skills/blob/2ffb677aa02b225c8a3da1b7f31d9ebb7c38f1dd/bin/cli.js) |
| 框架协议定义五类映射，缺失适配可由模型生成 | [adapter-protocol.md](https://github.com/plugin87/ux-ui-agent-skills/blob/2ffb677aa02b225c8a3da1b7f31d9ebb7c38f1dd/frameworks/adapter-protocol.md) |
| 截图转换追求设计语言一致，不承诺像素级复制 | [image-to-code/SKILL.md](https://github.com/plugin87/ux-ui-agent-skills/blob/2ffb677aa02b225c8a3da1b7f31d9ebb7c38f1dd/.claude/skills/image-to-code/SKILL.md) |
| Linear 目录是品牌启发的设计文档 | [linear-app/DESIGN.md](https://github.com/plugin87/ux-ui-agent-skills/blob/2ffb677aa02b225c8a3da1b7f31d9ebb7c38f1dd/design-systems/library/linear-app/DESIGN.md) |
| 总检查大量固定指向 examples | [accuracy_report.mjs](https://github.com/plugin87/ux-ui-agent-skills/blob/2ffb677aa02b225c8a3da1b7f31d9ebb7c38f1dd/scripts/accuracy_report.mjs) |
| 浏览器渲染依赖 Playwright，并有跳过分支 | [measure_render.mjs](https://github.com/plugin87/ux-ui-agent-skills/blob/2ffb677aa02b225c8a3da1b7f31d9ebb7c38f1dd/scripts/measure_render.mjs) |
| 评测器可指定产物目录，当前选择顶层 HTML 文件 | [evals/run.mjs](https://github.com/plugin87/ux-ui-agent-skills/blob/2ffb677aa02b225c8a3da1b7f31d9ebb7c38f1dd/evals/run.mjs) |
| 评测记录区分会话内生成与盲测 | [evals/RESULTS.md](https://github.com/plugin87/ux-ui-agent-skills/blob/2ffb677aa02b225c8a3da1b7f31d9ebb7c38f1dd/evals/RESULTS.md) |
| Figma 集成为映射说明与外部工具流程 | [figma-integration.md](https://github.com/plugin87/ux-ui-agent-skills/blob/2ffb677aa02b225c8a3da1b7f31d9ebb7c38f1dd/workflows/figma-integration.md) |
| 版本、开发依赖及 MIT 声明 | [package.json](https://github.com/plugin87/ux-ui-agent-skills/blob/2ffb677aa02b225c8a3da1b7f31d9ebb7c38f1dd/package.json) |

## 接入前需处理的具体问题

### 1. 示例检查与产品检查分开

`accuracy_report.mjs` 中的多个命令固定针对上游示例。检查通过证明的是这些目标通过相应检查，不能直接证明新页面通过。项目应建立自己的入口，覆盖真实页面、主题与重要状态。评测器的 `--dir` 提供部分参考，但目前选择指定目录顶层的 HTML，不能直接等同于完整应用路由测试。

### 2. 跳过不能当作通过

`measure_render.mjs` 在 Playwright 未安装时，根据 `DS_REQUIRE_BROWSER` 决定失败还是跳过；总检查设置该变量为 `1`。但在浏览器启动两次均失败的分支中，仍打印 SKIPPED 并以零状态退出。未发现 HTML 文件时也以零状态退出。

这属于静态源码发现，未做运行复现。采用时应让缺少必需环境、没有测试目标和未执行检查明确失败，避免单凭进程退出码解释成功。

### 3. 运行环境有要求

知识文档不需要应用运行时；完整检查需要 Python、Node、Playwright 及浏览器。评测器还调用 `head -1`，并使用 URL pathname 构建本地路径，因此 Windows 上需验证工具与路径兼容性。本次未安装依赖或运行检查。

### 4. 审美规则与客观检查分开

入口包含禁止 Emoji、强调主视觉、限制相同卡片布局等要求。这些是作者的设计偏好，不能普遍等同于可用性或无障碍标准。企业数据工具可能需要均匀布局和较高信息密度，应按实际用途调整。

### 5. 自动交互检查不证明业务正确

作者记录中新增了检查“声称可切换状态却点击无变化”的能力。能够检测状态变化仍不意味着排序正确、请求成功、权限有效或数据保存正确，需要场景测试补充。

## 作者评测与我们的验证

作者的记录包括会话内生成的样例，以及两次盲测子代理取得 14/14 检查结果。作者明确承认会话内样例受先前知识影响，并记录了盲测暴露的主题构建和检查缺陷。

这说明有可追溯的初步实验记录；尚不足以证明所有任务的首次成功率、审美质量或效率收益。我们未复跑这些实验，也未做基线对照。

## 研究与引用方式

研究文档和概念图为原创整理，未将所读上游指令安装为当前工作区规则。新增效果体验页收录八个原始示例与依赖文件，保留内容和注释，哈希与研究提交一致。来源、许可声明及 Lucide 官方许可正文见 [第三方说明](../demo/THIRD_PARTY_NOTICES.md)。已验证六个样例的主要交互，未复跑完整上游评测，未开展新需求生成对照实验。

[返回项目概览](../README.md)
