# 表演与新台词工作台 · 2026-09-08

入口 http://127.0.0.1:8022/ 。8020 保持原完整体验，8021 保持已认可的独立基线。本阶段交付六类动作评审与新台词在线提交、异步生成实验，尚未接入自由聊天或实时视频流。

## 实際交付

| 意图 | 已生成内容 | 当前限制 |
| --- | --- | --- |
| 倾听 | 眨眼、小幅点头 | 固定 4 秒循环 |
| 思考 | 偏头、视线偏移、轻挑眉 | 尚未绑定真实等待事件 |
| 安慰 | 柔和微笑、侧头 | 主观情绪强度仍需评审 |
| 调皮 | 歪头、微笑、短暂眨单眼 | 动作由时间曲线控制，未跟随词义 |
| 轻微不满 | 皱眉、收起笑容、小幅摇头 | 使用同角色 angry.png 参考图；中性图参数编辑不足以得到可信皱眉 |
| 肯定 | 微笑、两次小幅点头 | 本轮没有新增手臂动作 |

LivePortrait 驱动脸部和头部，身体主要保留照片。五类来自 neutral.png，轻微不满来自此前同角色的表情参考图；不声称一张中性照片已经连续表达所有情绪。六段各为 512×768、25 fps、4 秒。首尾原始帧一致，但动作周期仍可察觉。

输入 1–80 字新台词、选择动作后，Edge TTS 生成台湾女声，MuseTalk 依据这条新音频生成嘴型，再经过光流纹理稳定、正确 ParseNet 遮罩及尾音释放，合成有声 MP4。语音超过 12 秒会返回缩短台词提示。语速和音高有变化，未实测专用情绪 TTS，也未接入 MiniMax。

## 实测结果

本机 RTX 4070 Laptop 8 GB；常驻模型预热 4.828 秒。以下等待从提交计到完整 MP4 就绪，包含 TTS，不包含冷启动，也不等于浏览器首声音延迟。三个样本不代表 p95 或并发能力。

| 台词 / 表情 | 语音就绪 | 嘴型推理 | 总等待 | 视频长度 |
| --- | ---: | ---: | ---: | ---: |
| 今天辛苦啦，先休息一下吧。/ 安慰 | 2.218 s | 5.719 s | 16.842 s | 4.36 s |
| 哼，又逗我。好啦，原谅你了。/ 轻微不满 | 2.250 s | 5.297 s | 16.562 s | 4.80 s |
| 我先想一下，等一下再慢慢告诉你。/ 思考 | 2.640 s | 5.437 s | 16.807 s | 4.52 s |

视频处理耗时约为片长的 2.94–3.34 倍。PyTorch 峰值分配约 2327 MB，未计 CUDA 驱动、其他进程等开销。结果可在工作台历史记录中播放和下载。

验证：六个动作源首尾原始帧一致、预处理缓存哈希匹配；三条视频静音释放后的原始帧逐像素等于动作源；合成音轨与输入 PCM 零偏移相关系数均超过 0.9999。它们证明媒体与收尾链路正确，不自动证明真人级嘴型或情绪质量。已抽查说话帧，可见安慰和皱眉差异，牙齿仍有生成纹理。

取消测试在真实 GPU 批次开始后发出，0.313 秒内状态变为取消、任务文件被移除、任务锁释放，未产出完整视频。还检查了输入错误 400、忙碌 409、跨来源提交 403。TTS 阶段取消会等待当前 TTS 调用返回（最长 90 秒），目前只验证了 GPU 阶段快速取消。

数据见 performance-verification.json、performance-api-check.json；这两个报告可用下述脚本重建。

## 复用与启动

在项目目录执行 `./start-performance.ps1`。它复用模型运行环境启动常驻 worker，用该环境的基础 Python（已安装 edge-tts）启动网页服务；后台窗口隐藏，重复启动不会再启动同一 worker。Windows venv 的启动器和基础 Python 子进程可能同时出现在进程列表。

模块分工：

- `scripts/build_performance_assets.py`：动作参数、参考图、LivePortrait 动画。可追加 `annoyed` 等名称只重建一种。
- `scripts/prepare_performance_cache.py`：人脸轨迹、确定性 VAE latent、口腔遮罩缓存；动作 MP4 哈希变化时重建。
- `scripts/performance_worker.py`：常驻模型、新音频嘴型、帧融合、合成、耗时与取消。
- `scripts/avatar_timing.py`：复用已验证的开口与收口时间包络，默认保留尾音 100 ms、释放 220 ms。
- `scripts/serve_performance.py`：文本校验、台湾语音、单任务限流、状态与历史查询。
- `demo/performance.*`：六类对照、新台词提交、语音先听、历史播放和下载。

模型环境 `.cache/sadtalker-venv/Scripts/python.exe` 已包含 torch 2.1.2+cu121、NumPy 1.23.4、SciPy 1.10.1、OpenCV 4.8、diffusers 0.30.2、transformers 4.44.2。依赖 MuseTalk、LivePortrait、已有 facexlib 权重、FFmpeg 和基础 Python 的 edge-tts。不是无需模型的一键独立包。

重建顺序（停止生成服务后更新动作，避免一边推理一边改缓存）：

```powershell
& .cache/sadtalker-venv/Scripts/python.exe scripts/build_performance_assets.py
& .cache/sadtalker-venv/Scripts/python.exe scripts/prepare_performance_cache.py
./start-performance.ps1
```

验证已有结果：`& .cache/sadtalker-venv/Scripts/python.exe scripts/verify_performance.py`。

检查 API 与取消：`& D:/software/python310/python.exe scripts/check_performance_api.py`（会实际合成一条测试语音）。

动作源与缓存保存在 `.cache/performance`，每条新台词输出保存在 `.cache/performance-jobs/<id>`，含 job.json、audio.wav、result.mp4、timeline.json。日志在 `.cache/performance-worker*.log` 和 `.cache/performance-server*.log`。目前无自动清理机制，长期运行需增加任务保留期。

LivePortrait 官方代码 commit `9b294b3d0536135442ea73cb01e6cb3ca7029dd3`；官方模型 `KlingTeam/LivePortrait` revision `82a4fa6735ca58432b6ce39301b4b9ee066dea47`。校验清单保存在 `config/liveportrait-models.json`，可运行 `scripts/download_liveportrait.py` 下载/验证；代码仍需单独放入 vendor/LivePortrait。仅使用官方 wrapper 和编辑函数，不依赖 Gradio/InsightFace。

## 产品化结论

本轮验证了「离线制作动作 + 在线生成新语音与嘴型」可复用，但当前约 17 秒完整等待仍不适合自然连续对话。动作模板不等于按语义实时表演，轻微不满参考图切换也尚未做连续过渡。

下一阶段先压缩帧融合和磁盘写入开销（本次约占处理时间的一半），再验证分块推理、编码和缓冲是否能持续跟上声音；单改成流式 HTTP 无法解决 GPU 处理速度不足。声音先播可以用于快速预览，但正式角色若画面仍未就绪，会造成音画不匹配。

达到延迟门槛后再接入「一句输入 → 上下文回复 + 受限表演意图 → 同步播报 → 可打断 → 回到倾听」，以一个陪伴/任务鼓励场景验证产品价值。后续增加语音识别、流式情绪 TTS、动作转场、多轮上下文，再做可查看和删除的长期记忆。远程更快 GPU 或其他驱动后端应通过同一组台词/动作做对照后选择。
