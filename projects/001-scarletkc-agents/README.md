# 001 · Agents

> 深入研究优先级低，值得保留的是方法：发现反复出现的问题，将经验沉淀为具体约束，并在后续任务中复用。

| 项目 | 内容 |
| --- | --- |
| 原始仓库 | [scarletkc/agents](https://github.com/scarletkc/agents) |
| 官方说明 | [README](https://github.com/scarletkc/agents/blob/11a51de4d951c2bf1a5288054a3ca628be3b8bc4/README.md) |
| 研究版本 | `11a51de4d951c2bf1a5288054a3ca628be3b8bc4` |
| 研究日期 | 2026-09-07 |
| 状态 | 已完成（简要评估） |
| 技术栈 | Markdown 规则与技能、Python 辅助脚本 |
| 上游许可证 | [Apache-2.0](https://github.com/scarletkc/agents/blob/11a51de4d951c2bf1a5288054a3ca628be3b8bc4/LICENSE) |
| 图片 / Web 演示 | 暂无 / 暂无 |

## 项目摘要

作者把个人协作习惯、开发规范和表达风格整理成 `AGENTS.md` 与 6 个 Skill，供 AI 工具读取。能力主要来自规则、场景分类和示例对模型行为的引导；文风脚本只检查部分表达特征，无法保证模型遵守全部要求。

## 场景与约束

| 观察到的问题场景 | 沉淀出的约束 | 对应技能 |
| --- | --- | --- |
| 改代码时多改无关内容，或漏改关联位置 | 明确范围，范围内查全，范围外保持不动 | `scoped-change` |
| 复杂开发影响主目录，结果缺少对照 | 按需使用独立 worktree，与原始基线比较后交付 | `worktree-pr` |
| 委派任务不清，只相信 AI 的完成汇报 | 明确目标、范围和验收标准，检查实际 diff 并验证 | `codex-cli` |
| 文档与界面说法不一致、信息过时 | 保留权威来源，行为变化时同步相关文字 | `ux-writing` |
| 宣传夸大效果或披露未公开信息 | 主张可追溯到事实，先确定公开范围 | `marketing-copy` |
| 写作有 AI 腔、混用场景、编造立场 | 按场景读取风格与样本，事实优先，辅以禁用表达检查 | `talk-like-scarletkc` |

对应实现见固定版本的 [技能目录](https://github.com/scarletkc/agents/tree/11a51de4d951c2bf1a5288054a3ca628be3b8bc4/skills)。

## 值得借鉴的方法

**发现问题 → 记录具体失败 → 提炼约束 → 补充边界和示例 → 在后续任务中检验。**

- 把“写得自然”“别乱改”拆成可观察的行为，说明什么时候适用。
- 给规则配反例和正确做法，保留真实纠正经验。
- 按场景组织规则，明确优先级；写作中事实与意图优先于风格。
- 能机械判断的用脚本检查，需要语义理解的写成评测断言。

对我们的意义：将反复纠正 AI 的问题沉淀下来，逐步形成自己的约束与样本。当前无需整体引入或继续深入研究，可在遇到具体问题时参考相应实现。

## 运行与复现

在 Windows 环境的临时源码副本中运行 `python -m unittest discover -s tests`，31 项测试通过；`python scripts/update_readme_skills.py --check` 通过。这些结果验证辅助程序与目录一致性，未验证采用 Skill 后的模型效果提升。

## 资料导航

- [研究笔记与源码入口](notes/README.md)
- [图片说明](assets/README.md)
- [演示说明](demo/README.md)
- [返回总索引](../../README.md)
