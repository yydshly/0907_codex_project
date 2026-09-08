# 首句响应配置 v4 与十轮真实试跑

2026-09-08。`8022/chat` 当前默认使用 MiniMax-M3，`thinking=disabled`；语音保持 `speech-2.8-hd` 与原女声，人物模型和画面质量设置保持 v3。

结论：新配置具备更短的文字回复延迟，但本轮没有达到稳定即时对话。十轮试跑中九轮完整播放，一轮遇到 Windows 任务文件读取争用；已修复并单独补测成功。成功轮次首句开播中位数 **13.677 秒**、最慢 **29.007 秒**。失败轮次没有被算作零延迟，也没有从成功率分母中删除。

## 为什么调整 MiniMax 配置

官方 [Chat Completions 文档](https://platform.minimaxi.com/docs/api-reference/text-chat-openai)说明 MiniMax-M3 可以通过 `thinking.type=disabled` 直接回答；M2.x 不能通过该参数关闭思考。

初筛在相同角色提示和三个固定场景上比较 M2.7-highspeed、M3 与 M2-her。M3 两条格式有效回复约 2.375、2.500 秒，但上下文场景仍有格式失败；M2-her 在这三个现有 JSON 协议场景中没有返回可直接使用的格式，因此没有采用。初筛记录包含失败，不应作为最终生产成功率：[候选请求记录](minimax-first-reply-benchmark.json)。

实际格式修复：向模型发送历史 assistant 消息时，使用与当前回复一致的 `{"reply":...,"intent":...}` 格式，避免历史纯文本诱导模型放弃 JSON。新会话同时保存真实 intent，旧历史缺少 intent 时使用 listen 作为格式补位，不改变历史原文。保留现有严格解析和最多一次模型格式修复；不把格式失败改成固定回复或关键词拼接。

默认配置：

```dotenv
MINIMAX_CHAT_MODEL=MiniMax-M3
MINIMAX_CHAT_THINKING=disabled
MINIMAX_SPEECH_MODEL=speech-2.8-hd
```

现有明确设置的 `MINIMAX_CHAT_MODEL` 继续生效。M2.7 请求不会携带关闭思考参数。语音音色、情绪映射、人物权重、分段长度策略、FPS、嘴部稳定和闭口包络没有改变。

## 十轮浏览器实测

在同一个独立测试会话连续输入、等待有声 MP4 完整播放后再输入下一轮。计时来自浏览器实际开播事件，包含文字请求、TTS、视频生成和播放器启动；不是文字首 token、服务器准备好时刻或缓存重播。计时表示有声媒体开始播放，并非人工听感标注的第一个音素。

会话：`e368de310ed94ed485d2ce0d0b1bd6c9`。

| 轮次 | 场景 | 首句开播 | 句间等待 | 结果 |
| --- | --- | ---: | ---: | --- |
| 1 | 修网页很累 | 15.801 秒 | 0.037 秒 | 播放完成 |
| 2 | 回忆今天在做什么 | 12.240 秒 | 0.040 秒 | 正确回忆网页 |
| 3 | 暂时休息，不安排计划 | 13.677 秒 | 0.041 秒 | 播放完成 |
| 4 | 轻松玩笑 | 11.597 秒 | 0.823 秒 | 播放完成 |
| 5 | 登录页修好 | 17.322 秒 | 0.039 秒 | 播放完成 |
| 6 | 回忆刚修好的页面 | 13.732 秒 | 0.041 秒 | 正确回忆登录页 |
| 7 | 接下来整理测试记录 | 29.007 秒 | 5.173 秒 | 长尾，播放完成 |
| 8 | 烦躁，要求安静陪伴 | 未开播 | — | 任务文件读取失败 |
| 9 | 回忆下一步整理什么 | 13.523 秒 | 0.636 秒 | 正确回忆测试记录 |
| 10 | 结束对话去休息 | 12.023 秒 | 0.039 秒 | 播放完成 |

成功九轮的句间等待中位数 0.041 秒，最大 5.173 秒。十轮的文字请求中位数 4.094 秒、最大 19.782 秒，格式重试共 0 次。旧版仅有少量不同文本的浏览器样例，不能将本表解读为严格匹配的十轮 A/B 提升比例。

第七轮约 19.8 秒耗在 MiniMax 文字 HTTP 请求；后半句较长，画面又耗时约 10.4 秒，超过前段可覆盖的播放时间。不能用候选初筛的 2.4 秒掩盖这类长尾。

原始记录：[浏览器测量](first-response-browser-measurements.json)、[关联任务、语音与画面分项](first-response-ten-rounds.json)。`scripts/summarize_first_response.py` 可重新汇总，三个上下文检查分别验证网页、登录页和测试记录。

## 失败处理与补测

第八轮在读取 `job.json` 时发生 Windows 短暂文件句柄争用。之前仅保护原子写入，本轮新增公共 `performance_jobs.read()`：最多 12 次有界重试 PermissionError；不吞掉永久权限错误，不重试损坏 JSON。任务服务、API 和 GPU worker 统一使用该读取路径。

修复在第八、九轮之间上线，因此这不是十轮都在同一个完全相同构建上的无失败报告。第八轮同一句在本次会话稍后额外重试，完整开播成功：首句 13.958 秒，句间 0.044 秒，记录独立列于报告 `post_fix_retry`，不回填覆盖原失败。

播放器测量增加终态：完整播放、生成失败和取消可以区分，避免失败轮次被当作上一次重播结果。

MiniMax 新配置取消实测：对话请求阶段约 0.375 秒释放本地资源，GPU 阶段约 0.344 秒；新请求随后成功。远程 HTTP 取消仍表示本地停止等待与丢弃旧结果，不能撤销供应商已经执行的请求。记录：[取消验收](first-response-cancel.json)。

最终验证通过 21 项 Python 测试和播放器状态测试；六类模板、50 条真实音频生成视频通过音轨同步、静音闭口帧及缓存检查。人物自然度仍需主观体验，自动化检查不代表已经达到真人自然表现。

## 复用、检查与回退

- `scripts/minimax_dialogue.py`：默认 M3、思考开关、历史 JSON 格式和旧模型兼容。
- `scripts/dialogue_service.py` / `dialogue_segments.py`：保存实际表情意图，复用原有语音与画面流程。
- `scripts/performance_jobs.py`：任务元数据读写争用保护。
- `demo/dialogue-segmented.js`：可区分失败的浏览器开播测量。
- `.env.companion.example`：配置示例；密钥仍通过原本的本地文件引用，未复制到前端或报告。

```powershell
& ./.cache/sadtalker-venv/Scripts/python.exe -m unittest discover -s scripts -p 'test_*.py'
node scripts/test_segmented_player.cjs
& D:/software/python310/python.exe scripts/summarize_first_response.py
& ./.cache/sadtalker-venv/Scripts/python.exe scripts/verify_performance.py
```

对话层改动前快照在 `.cache/releases/dialogue-first-response-v3/`，附 SHA-256 清单。切回旧模型只需在 `.env.companion` 明确设置 `MINIMAX_CHAT_MODEL=MiniMax-M2.7-highspeed`，下一次请求生效；无需撤销文件锁修复或已验证的嘴部处理。

## 产品判断

目前适合继续验证短回合陪伴原型，尚不适合宣称即时、稳定连续对话。本轮未接入文字 SSE、流式 TTS 或逐视频帧输出，仍需首段完整语音和完整 MP4 就绪后开播。

剩余工作需要针对两个独立问题验收：MiniMax 请求的长尾，以及本地第一段视频的生成耗时。只切换对话模型不足以把首句稳定压到几秒；下一阶段如改用流式首段或更快的图像解码，需要重新测真实音画开播和嘴部质量。
