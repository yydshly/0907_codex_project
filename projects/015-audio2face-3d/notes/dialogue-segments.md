# 可打断的分段对话 v2

2026-09-08。本地 `/chat` 默认采用分段模式；`/chat-classic` 保留整段播放流程。MiniMax 对话模型和语音模型保持原配置。此版本缩短首句等待，尚未实现实时、无停顿对话。

## 实测结果

浏览器新会话：`d71ead5ddd7944ccaa16eb78cf3aaa3a`，任务 `aa2daa2696b14e4fb5a0673b98470d6a`。

- 用户输入：我今天修了一整天网页，很累。
- MiniMax 回复：修一整天真的很累诶，辛苦了～好好休息一下吧。
- 首段服务端就绪 14.785 秒，浏览器实际开播 15.071 秒。
- 全部画面准备约 22.3 秒。首段不必再等到全部完成。
- 浏览器实测两段之间等待 **4.109 秒**。首段播放时间不足以覆盖第二段生成时间，这是当前明确的体验缺口。
- 第二条真实请求首段就绪 16.159 秒，全部准备 23.189 秒；这条是 API 测试，没有把服务端就绪时间写成浏览器开播时间。
- MiniMax 对话请求期间取消，资源释放 0.343 秒；新对话随即提交并成功生成。
- GPU 生成期间取消，资源释放 0.359 秒；旧子任务的请求文件已清除。

这些是少量本机样例，不是平均值或服务承诺。旧版 19–25 秒记录使用不同回复，不能据此宣称相同比较条件下的固定提升比例。

机器证据：[API 验收](dialogue-segments-live.json)、[浏览器测量](dialogue-segments-browser.json)、[画面/静音/音轨检查](performance-verification.json)。全部六类模板、十九条真实音频生成视频通过检查。这些检查不能代替人物自然度的主观验收。

## 流程与复用接口

`MiniMax 完整回复 → 标点分段 → 第一句 TTS → 第一句 GPU 视频 → 发布第一片段 → 第二句 GPU 视频 → 发布第二片段`。

第二句 TTS 与第一句 GPU 视频同时处理。每轮最多两个片段，按中文标点和最小片段长度分割，不在词语中间硬切；没有合适停顿则保留整句。LLM 和 TTS 均是完整 HTTP 响应，浏览器接收的是逐段完整 MP4，**并非逐 token、逐音频帧或逐视频帧流式推理**。

```json
POST /api/dialogue/turn
{"session":"32位会话ID","text":"我今天有点累。","mode":"segmented"}
```

轮询 `/api/jobs/<id>`，读取 `segments` 数组（完成一个追加一个）、`segment_count`、`first_segment_s`、`status`。每个片段提供 `video`、`audio`、`text`、`state`、`ready_s` 和耗时。前端按片段顺序去重消费；媒体尚未就绪时等待，取消时通过会话代号丢弃迟到结果。`done` 表示生成完成，不代表用户已经听完。

- `scripts/dialogue_segments.py`：分段策略、TTS 预取、串行 GPU 调度、父子任务和取消清理。
- `scripts/minimax_dialogue.py`：MiniMax 对话/语音及可取消等待；远程 HTTP 请求最多同时两个。
- `scripts/performance_worker.py`：使用累计 `frame_offset` 轮转源视频、潜变量、裁剪框与掩码，片段接续同一条动作时间线。
- `demo/dialogue-segmented.js`：逐段播放队列、重播、打断、首句开播与句间等待测量。
- `mode: "classic"` 仍使用原整段协议；未传模式的 API 请求也保持旧行为。

可取消等待并不等于撤销 MiniMax 已收到的远程计算或费用：本地立即放弃旧请求的结果，但远程请求直到返回或 60 秒网络超时仍占并发槽。连续快速打断时，新请求可能需要等待槽位；不会无限启动远程请求。取消不能保证在模型初始化、FFmpeg 转码、网络故障等所有阶段都达到上述两条样例的耗时。

每轮 GPU 所有权在旧请求清理完后才释放。嘴部静音包络、光流稳定、融合掩码和编码质量保持原实现。此次增加动作时间线接续，没有增加新手势或新的身体动作模型。片段等待时停在前段闭口末帧，仍会显得停顿。

分段回复只在全部生成成功后写入服务端 assistant 历史；取消中的完整回复不会成为已完成回复。界面可能已显示那段文字，刷新后以服务端历史为准。目前没有“用户已听到哪几个字”的播放确认协议，也没有长期记忆。

## 验证与回退

```powershell
& D:/software/python310/python.exe scripts/test_minimax_dialogue.py
& D:/software/python310/python.exe scripts/test_dialogue_segments.py
node scripts/test_segmented_player.cjs
# 以下会发起真实 MiniMax 请求，消耗账户额度：
& D:/software/python310/python.exe scripts/verify_segmented_live.py
& ./.cache/sadtalker-venv/Scripts/python.exe scripts/verify_performance.py
```

单元检查覆盖：格式与上下文、分段不丢字、远程并发上限、迟到语音不落盘、重复轮询不重播、迟到媒体 Promise、部分片段重播。实际界面验证覆盖新请求开播、刷新恢复、重播和停止。

改动前代码已保存到 `.cache/releases/dialogue-v1-before-segments/`，包含 SHA-256 清单。直接使用 `/chat-classic` 可回到整段体验；若需完全回退，将快照清单中的文件覆盖回原路径，在服务空闲时重启服务及 worker。快照不包含密钥和大模型权重。

## 下一步判断

目前不应继续靠切得更碎来宣称实时化。首个实测片段的画面处理耗时约 7.3 秒，片长约 3 秒；吞吐不足使后段必然积压。下一轮应单独验证小批量视频输出、推理吞吐优化或更快渲染方案，并同时验收嘴部质量、首句时间和播放欠载。若吞吐无法达到播放速度，则需要明确选择更短回复或增加播放缓冲；缓冲会延后首句，不能把这个代价隐藏起来。
