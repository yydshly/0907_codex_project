# 能力边界与外部资产来源核对

状态：已获用户确认并授权整理提交。基于本地固定版本 cf78a39b171419ac567662e0932a5c563ed4a47b 的源码检查，不代表新增效果实测。

## 确认的能力边界

- 外部动作来源不仅是文字生成，也包括已有动作文件与其他模型/工具的动作输出。
- 已有兼容动作的导入不要求运行 Kimodo 生成后端；浏览器三维显示仍需要图形能力。
- 任意外部动作不能直接通用：需符合内部数据结构、骨架、单位和旋转约定。
- 角色列表当前由 X Bot、Y Bot 两个模型 ID 构成。没有确认任意 FBX/GLB 导入入口，因此自定义三维人物应标记为需开发适配。
- 图片资产可以用作场景图片卡片、背景等，不等于完整三维人物。

## 代码依据

| 检查项 | 源文件 | 结论 |
| --- | --- | --- |
| 已有动作文件/URL | `src/workflow/WorkflowBuilder.jsx` 的 MotionInputNode | 本地 .npz 选择器、Motion URL 和目标角色连接；文件选择器允许的扩展名不等于所有内容均可解码 |
| 动作数据绑定 | `src/workflow/motion-input.js` | 动作输出通过 characterId 与 motionRef 绑定角色 |
| 格式限制 | `src/ardy/npz.js` | NPZ 内容、维度、旋转等均会校验，不是任意 NPZ 即可用 |
| 特定来源转换 | `tools/kimodo/soma77-to-cskel27.mjs`、`tools/ardy/bvh-cskel27.mjs` | 已有特定骨架转换实现，不代表通用 BVH/FBX 导入器 |
| 三维角色 | `src/scenes.js`、`src/asset-pane.jsx` | 当前角色目录来自 y-bot-tpose / x-bot-tpose |
| 图片与视频 | `src/App.jsx`、`src/scene-assets.js` | 图片场景素材与姿态提取、视频动作提取是不同用途；提取效果尚未验收 |

图中“外部动作来源”表示来源范围与适配边界，不表示已经接入所有外部 AI 服务。
