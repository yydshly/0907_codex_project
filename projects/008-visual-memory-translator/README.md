# 008 · Visual Memory Translator / 影像转译编辑器

> 将照片与句子转化为具有艺术出版气质的视觉作品；研究重点是如何把审美判断沉淀为可复用的创作规则。

| 项目 | 内容 |
| --- | --- |
| 编号 | 008 |
| 原始仓库 | [TanShilongMario/visual-memory-translator-SKILL](https://github.com/TanShilongMario/visual-memory-translator-SKILL) |
| 官方文档 | [SKILL.md](https://github.com/TanShilongMario/visual-memory-translator-SKILL/blob/98a18ef20ba98a124161be7b8caa8e0a7cdaf13b/visual-memory-translator/SKILL.md) |
| 研究版本 | `98a18ef20ba98a124161be7b8caa8e0a7cdaf13b`；主技能标注 1.5.0 |
| 研究日期 | 2026-09-07 |
| 状态 | 已完成（简单记录，暂不深入；生图未实测） |
| 技术栈 | Markdown 技能说明、YAML 参数示例；依赖宿主 AI 与外部图像模型 |
| 上游许可证 | [MIT](https://github.com/TanShilongMario/visual-memory-translator-SKILL/blob/98a18ef20ba98a124161be7b8caa8e0a7cdaf13b/LICENSE) |
| Web 演示 | [中文能力展示](../../docs/demos/008-visual-memory-translator/index.html)（本地静态展示，未声明上线） |

## 简要结论

**照片的主要流程：提取关键元素 → 简化或改变艺术表达 → 重新构图呈现。** 例如保留人物姿态、山景层次和道路走向，再用线条、色块、留白与文字组织成记忆页。部分模板只改变局部媒介，整体构图基本不变。

它用技能规则指导 AI 理解输入并调用外部图像模型，没有自带抠图、独立图层或精确排版程序。“记忆”指视觉表达，不是长期记忆系统；元素位置与外观不能保证完全一致。

## 主要能力与场景

| 能力 | 适合场景 |
| --- | --- |
| 照片元素概括与重新构图 | 旅行纪念、艺术相册、个人分享配图 |
| 六格风格预览，选号后从原图重生成 | 设计方向探索与偏好沟通 |
| 一句话提炼成一个视觉隐喻 | 文章观点卡、研究成果分享 |
| 邮票、票据、贴纸、唱片等视觉形式 | 文创概念与封面创意探索 |

## 对我们的意义与处理决定

借鉴“输入要求 → 创作规则 → 候选选择 → 检查修正”的经验组织方法；有项目封面或观点配图需求时可以参考。准确架构图、流程图和数据图需要另外的表达规则。

**当前仅简单记录，保留已有展示，暂不安装、不做生图实测、不继续深入研究。** 后续有实际需求再考虑专属视觉规范、原图合成、独立文字排版等扩展，无需现在投入。

## 展示说明

已有中文页面为能力导览，流程切换不调用模型。公开样张来自上游固定提交，通过远程链接展示，需联网；原图未公开，不能作为我们的保真测试结果。页面中的扩展方向仅为备查建议，不代表实施计划。

## 资料导航

- [源码依据与能力边界](notes/capability-boundaries.md)
- [展示源码与复现方式](demo/README.md)
- [第三方来源与许可说明](demo/THIRD_PARTY_NOTICES.md)
- [中文能力展示](../../docs/demos/008-visual-memory-translator/index.html)
- [返回总索引](../../README.md)
