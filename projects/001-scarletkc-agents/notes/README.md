# 研究笔记与源码入口

研究日期：2026-09-07。上游版本：`11a51de4d951c2bf1a5288054a3ca628be3b8bc4`。

结论与场景对照统一保存在 [项目研究页](../README.md)。以下入口用于按需查看约束如何落地：

- [scoped-change](https://github.com/scarletkc/agents/blob/11a51de4d951c2bf1a5288054a3ca628be3b8bc4/skills/scoped-change/SKILL.md)：修改边界、关联检查与失败反例。
- [写作技能](https://github.com/scarletkc/agents/blob/11a51de4d951c2bf1a5288054a3ca628be3b8bc4/skills/talk-like-scarletkc/SKILL.md)：场景选择、资源读取、执行步骤与优先级。
- [场景规则](https://github.com/scarletkc/agents/blob/11a51de4d951c2bf1a5288054a3ca628be3b8bc4/skills/talk-like-scarletkc/references/surface-profiles.md)：区分聊天、社交、项目文档等场景。
- [文风检查脚本](https://github.com/scarletkc/agents/blob/11a51de4d951c2bf1a5288054a3ca628be3b8bc4/skills/talk-like-scarletkc/scripts/lint_style.py)：正则检查，只提示、不自动改写。
- [写作评测案例](https://github.com/scarletkc/agents/blob/11a51de4d951c2bf1a5288054a3ca628be3b8bc4/skills/talk-like-scarletkc/evals/evals.json)：输入、期望表现与语义断言；案例文件本身不自动执行评测。

以上为源码观察。收益判断属于本次评估，未进行模型效果对照实验。
