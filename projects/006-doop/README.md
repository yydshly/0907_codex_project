# 006 · Doop：人和 AI 共用的设计画布

> 结论：同类设计协作产品，了解定位即可。当前新增价值有限，暂不部署、不继续深挖；以后出现多人评审、元素反馈定位和 Agent 任务接续的实际需求时再评估。

[返回总索引](../../README.md) · [原始仓库](https://github.com/kgoedecke/doop) · [固定研究版本](https://github.com/kgoedecke/doop/tree/86a42f1d20b18393306121c8b417f252cca69609)

![Doop 架构与同类产品对比：人确定目标和验收，AI 经统一操作层修改 HTML 画板；对比 OpenDesign、Claude Design 和 M3E Canvas 的工作中心](assets/doop-overview.png)

*原创架构与定位示意，非产品截图或官方架构图。[可缩放原图](assets/doop-overview.svg) · [图片说明](assets/README.md)*

## 项目是什么

Doop 是完整的设计协作应用。用户在浏览器画布中摆放和编辑多个 Frame；每个 Frame 保存名称、位置、尺寸和 HTML，并在沙箱 iframe 中渲染。外部 Agent 通过 MCP 操作同一份画布，内置 Agent 则可以处理任务卡片、元素评论和反馈。

人确定目标、提出反馈并验收，AI 在授权任务内生成或修改设计。Doop 将这个过程变得可见、可定位、可接续，但这不意味着模型本身的设计能力增强，也不意味着系统能够独立确定产品目标。

## 已有能力与底层原理

| 部分 | 实现与作用 | 边界 |
| --- | --- | --- |
| HTML 画板 | Frame 存储 HTML、坐标和尺寸；浏览器渲染并支持编辑 | HTML 设计稿不等于带完整业务逻辑的生产应用 |
| 实时协作 | 统一 actions 更新状态、记录活动，通过 WebSocket 广播修改与在线状态 | 广播同步不等于任意并发修改都能无冲突合并 |
| AI 接入 | MCP 暴露画布读取、创建、修改、截图、状态等工具；内置 Agent 复用操作层 | AI 工作仍由人的目标、任务卡和反馈驱动 |
| 任务接续 | 设计、文案、品牌、无障碍等角色按任务链处理；一般内置任务在同一画布串行执行 | 角色划分主要依靠指令与调度，不代表各有专门训练的模型 |
| 视觉验证 | Puppeteer 调用浏览器渲染截图；内置执行循环跟踪修改与截图验证 | 获得截图不保证模型发现所有视觉或功能问题 |
| 设计记忆 | 保存样稿与决策，模型提出长期规则，人工接受后加入指南 | 外部规则与上下文管理，不是模型权重训练 |
| 导入和输出 | 网页快照、应用采集、GitHub 源码导入；读取 HTML、输出图片 | GitHub 导入主要是单次读取与页面重建，不是设计到源码的自动双向同步 |

架构可以概括为：**人 / 外部 Agent / 内置 Agent → 统一操作层 → 内存状态与数据库、WebSocket → 实时画布；画板 → 浏览器截图 → Agent 继续修改。**

核心栈为 React/Vite 前端、Node/Express 服务端、WebSocket、MCP、PGlite/PostgreSQL 与 Puppeteer。服务端使用内存 Map 维护热点状态，并将修改写入数据库；核心字段更新直接应用 patch，多实例一致性和同一画板并发编辑应单独验证。

实现依据：[Frame 数据结构](https://github.com/kgoedecke/doop/blob/86a42f1d20b18393306121c8b417f252cca69609/shared/types.ts)、[统一操作层](https://github.com/kgoedecke/doop/blob/86a42f1d20b18393306121c8b417f252cca69609/server/actions.ts)、[状态存储](https://github.com/kgoedecke/doop/blob/86a42f1d20b18393306121c8b417f252cca69609/server/store.ts)、[MCP 工具](https://github.com/kgoedecke/doop/blob/86a42f1d20b18393306121c8b417f252cca69609/server/mcp.ts)、[Agent 执行循环](https://github.com/kgoedecke/doop/blob/86a42f1d20b18393306121c8b417f252cca69609/server/resident.ts)、[截图](https://github.com/kgoedecke/doop/blob/86a42f1d20b18393306121c8b417f252cca69609/server/screenshot.ts)、[设计记忆](https://github.com/kgoedecke/doop/blob/86a42f1d20b18393306121c8b417f252cca69609/server/distill.ts)、[GitHub 导入](https://github.com/kgoedecke/doop/blob/86a42f1d20b18393306121c8b417f252cca69609/server/githubRecon.ts)。

## 类似产品：差别在工作中心

OpenDesign 存在多个同名仓库，本记录明确比较 **nexu-io/open-design**。旧技能清单只记录了 Open Design 名称，不能据此确认当时指向同一仓库。下面比较定位和公开能力，不是效果排名。

| 产品 | 工作中心 | 人与 AI 的关系 | 主要产物 / 可借鉴点 |
| --- | --- | --- | --- |
| Doop | 共享 HTML 画板、评论、任务和参与者 | 人布置和验收；内外部 Agent 修改画板，过程实时广播 | HTML 与图片；实时协作、反馈任务、设计记忆 |
| OpenDesign | 本地项目文件、Skills、模板和 DESIGN.md | 人提供需求；本地 Agent 或模型生成文件，工作台预览和交付 | 原型、网页、演示与媒体；设计规则组合、运行时适配 |
| Claude Design | 托管的对话与画布、品牌系统和交付 | 人描述、编辑和评论；Claude 生成设计，可衔接 Claude Code | 原型、演示、文档；设计系统导入、视觉编辑与交接体验 |
| M3E Canvas | 结构化组件、主题、布局和导航关系 | 人搭建结构，规则编译实现说明，外部编程 Agent 接手 | Prompt、JSON、PNG 与预览；结构化需求到实现规格 |

**MCP 已不是 Doop 独有的区别。** Doop 的工具可以直接修改共享画板；OpenDesign 当前文档描述的 MCP 主要让外部 Agent 读取与搜索项目文件，默认只读，其内部启动的 Agent 另行生成文件；Claude Design 也公开支持从 Claude Code 经 MCP 创建和编辑设计，以及设计系统同步。三者的接口职责不同，不能仅按“有无 MCP”判断能力。

来源：[OpenDesign 官方仓库及架构](https://github.com/nexu-io/open-design)、[OpenDesign 外部 Agent 接入](https://github.com/nexu-io/open-design#use-opendesign-from-your-coding-agent)、[Claude Design 产品说明](https://claude.com/product/design)、[Claude Design 使用指南](https://support.claude.com/en/articles/14604416-get-started-with-claude-design)、[M3E Canvas](https://github.com/lnkiai/m3e-canvas)。OpenDesign 与 Claude Design 为 2026-09-07 查阅的公开说明；未做此次实测，闭源产品内部实现不作推断。

## 与已有研究的重叠

- **M3E Canvas**：此前已验证多屏组件搭建、导航预览、Prompt 编译与 JSON 导出；侧重把人的设计意图变成结构化实现说明。上游核对版本为 `de5eb2025e5eb7ac6cb8e4746eb519887057f066`。
- **DESIGN.md Evidence Lab**：此前已研究真实网站与样例的六维复核，将设计判断翻译成 Token、组件规则和 Agent 实现简报，并用浏览器验证；覆盖设计知识积累与复用。
- **AtlasNote 技能清单**：此前收录 Open Design 与“本地 Claude Design”相关条目；属于能力清单研究，不能视为完整产品部署验证。

本次核对的历史文件位置（其他研究仓库，非本仓库内链接）：

```text
E:/0904_codex_project/projects/100-m3e-canvas/README.md
F:/0801_codex_project/awesome-design-md-lab/README.md
E:/0830_codex_project/projects/atlasnote-skills-page-analysis/docs/06-capability-inventory-81.md
```

## 对我们的取舍

**当前仅归档，不安排部署或继续深挖。** 我们已有设计规则、Agent 执行和浏览器验证流程；目前没有明确的多人实时设计评审需求，因此 Doop 的协作功能尚不足以抵消引入新系统的学习、维护和集成成本。这是当前工作场景下的优先级判断，不代表它对其他团队无价值。

如以后反复出现“元素反馈说不清、多人同时评审困难、Agent 处理进度不可见”的问题，可重新评估统一操作层、评论转任务和经人工确认的设计记忆。单纯为了“让 AI 生成网页”无需再增加一套平台。

可扩展方向仅作为备忘，**不是开发计划或现有功能承诺**：接入团队设计规范、加入确定性的视觉检查、对接真实组件库、补足版本与冲突处理。设计到 React/Vue 源码双向同步涉及业务逻辑与组件语义，不能视为轻量扩展。

## 来源与验证范围

| 项目 | 记录 |
| --- | --- |
| 研究日期 | 2026-09-07 |
| Doop 研究提交 | `86a42f1d20b18393306121c8b417f252cca69609` |
| 状态 | 已完成（源码与对比归档；暂不深挖） |
| 已核实 | README、核心数据结构、操作层、Agent 循环、截图、记忆与导入模块；同类产品公开说明；历史研究记录 |
| 未验证 | Doop 部署、设计质量、协作冲突、性能、成本与长期稳定性；OpenDesign / Claude Design 本次实际运行 |
| 上游许可 | [AGPL-3.0-only 声明](https://github.com/kgoedecke/doop/blob/86a42f1d20b18393306121c8b417f252cca69609/package.json)；未复制上游代码 |
| Web 演示 | 暂无；交付研究文档与一张架构 / 对比图 |

补充边界：当前 `export_frame` 工具明确提供无需认证的公开图片 URL；私有画布访问控制不能被理解为所有图片出口都私有。此项为代码观察，未进行线上安全测试，详见上述 MCP 实现。
