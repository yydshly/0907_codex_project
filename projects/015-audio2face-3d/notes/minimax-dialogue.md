# MiniMax 单角色对话闭环

2026-09-08。产品入口：http://127.0.0.1:8022/chat 。原工作台 8022/、完整片段 8020 和认可基线 8021 保留。

本文最初的验收数据使用 MiniMax-M2.7-highspeed；当前首句配置和十轮实测见 [首句响应 v4](first-response-v4.md)。

## 已接通的流程

用户输入文字 → MiniMax 根据最近六轮上下文生成短回复与表情意图 → MiniMax 情绪语音 → 本机 MuseTalk 嘴型与 LivePortrait 动作模板 → 同步播放有声回应 → 回到倾听。文字回复先显示，声音和画面准备好后一起播放。

本产品入口对话和语音均使用 MiniMax，没有隐式回退到 Edge、其他语言模型或预设回答。效果工作台原有的 Edge 样例和旧测试入口继续保留用于对照；它们与新产品对话入口不同。

页面包括自由文字输入、上下文延续、新对话、倾听/思考/说话状态、停止与后台取消、重播、下载，以及「我完成了一个任务」的鼓励入口。任务完成入口是用户主动报告的一项事件，目前未读取外部任务系统，也未实现定时提醒。

## 模型与配置

对话当前默认 MiniMax-M3（thinking=disabled），语音默认 speech-2.8-hd；系统女声 Chinese (Mandarin)_Warm_Girl。情绪映射为 comfort/listen/think → calm，playful/affirm → happy，annoyed → angry，配合轻微语速、音高变化。台湾华语口语通过角色提示引导，实际口音取决于音色，目前未验收台湾口音。

依据官方 [Chat Completions 文档](https://platform.minimaxi.com/docs/api-reference/text-chat-openai)接入对话、[同步语音文档](https://platform.minimaxi.com/docs/api-reference/speech-t2a-http)接入声音；[系统音色列表](https://platform.minimax.io/docs/faq/system-voice-id)用于选取女声。模型和音色均可在配置中修改，具体权限需以账户实际调用为准。

当前按用户指定读取 F:/codex_project/.env.minimax，通过项目本地 .env.companion 的 MINIMAX_CONFIG_FILE 引用；没有复制或展示密钥。配置支持 MINIMAX_API_KEY、MINIMAX_API_BASE，亦支持分别指定对话/语音 key、模型、音色及官方接口地址。可参考项目 .env.companion.example。配置每次请求重新读取，改完后不必重启服务。

API Key 只用于服务端请求，不发送到浏览器、写入任务 JSON 或纳入版本控制。发给 MiniMax 的是当前用户输入、最近六轮对话和角色提示；语音接口接收生成的短回复。照片和嘴型处理仍在本机。

## 可复用的分层

- scripts/minimax_dialogue.py：配置读取、MiniMax HTTP、角色提示、回复/表情解析、情绪语音。
- scripts/dialogue_service.py：会话上下文、业务事件、任务状态、取消及音频到既有 worker 的衔接。
- scripts/serve_performance.py：/api/dialogue/* 接口；与旧工作台共用 GPU 任务锁。
- scripts/performance_worker.py 和 performance_postprocess.py：已验证的嘴型、收口与编码，复用 v2。
- demo/dialogue.html/css/js：产品对话页面，按任务标识隔离迟到的回复和视频；刷新时恢复当前会话及未完成任务。

对话模型只能选择既有六种意图，不会因为返回一个动作名称就产生新动作。输出限定短回复，校验非法意图、格式、长度和思考内容；格式不合规时最多请求 MiniMax 修复一次，仍失败则明确报错。无关键词拼接的伪 AI 回答，也不把 reasoning_content 朗读出来。

## 接口与存储

- GET /api/dialogue/status：配置就绪情况、模型名、GPU 服务状态和忙碌状态；不返回密钥。
- POST /api/dialogue/session：创建新会话。
- GET /api/dialogue/session/<id>：读取本机会话文字。
- POST /api/dialogue/turn：提交 session、text，可选 event=task_done。
- GET /api/jobs/<id> 与 POST /api/cancel/<id>：复用任务查询和取消接口。

会话保存在 .cache/dialogue-sessions；媒体任务保存在 .cache/performance-jobs，kind=dialogue。浏览器仅保存当前会话 ID；「新对话」开启新的上下文，不会删除本机历史文件。目前没有长期偏好记忆、历史管理或自动清理策略。

启动命令仍为 ./start-performance.ps1。此脚本使用模型 venv 的基础 Python 启动服务、使用 venv 启动 GPU worker。

## 验证与当前边界

scripts/test_minimax_dialogue.py 是独立单元测试，包含格式错误、思考内容隔离、上下文边界、缺 key、有限重试和取消后禁止继续合成。测试替身仅在测试进程中使用，不接入产品服务。

scripts/verify_dialogue_live.py 使用真实 MiniMax 和本机 GPU，验证疲惫安慰、第二轮引用前文、任务完成鼓励、模型阶段取消。运行会产生实际接口用量；结果记录在 notes/minimax-dialogue-live.json。scripts/verify_performance.py 校验实际媒体与收口。

已有预设台词的 11～12 秒生成耗时不适用于完整对话：现在增加了语言模型调用，回复也可能更长。初次两轮完整实测为约 24、25 秒，后续样本以验收报告为准。页面分别记录语言模型、语音、画面和总等待时间。

最终三轮真实验收：安慰回应 25.103 秒（视频 7.28 秒）、上下文回忆 21.362 秒（视频 4.92 秒）、任务完成鼓励 19.275 秒（视频 5.64 秒）。第二轮准确回复「你今天修了一整天的网页」，第三轮为 affirm 意图和 happy 语音。模型请求阶段打断后，5.203 秒内释放后台任务，没有继续生成语音或视频。六项单元测试通过；媒体回归检查通过六个动作模板和十四条实际视频。

这是一个真实但异步的单角色对话原型，尚未实现实时连续音视频、语音输入、自然跨表情转场、动态身体手势或长期记忆。动作模板为 4 秒循环，较长回应会重复。停止播放立即生效；GPU 工作可在批次之间取消；已发出的同步 MiniMax 请求需等待该请求返回或超时，取消会阻止后续语音/GPU阶段及迟到播放，不能保证供应商端立即停止生成或免除用量。
