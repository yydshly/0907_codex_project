# 新台词生成加速 v2

2026-09-08。8022 已使用新 worker，保留原视频与 8021 认可基线。工作台新增三组「优化前 / 加速版」播放对照。

## 改动与验证

1. 相邻帧每个方向的 Farneback 光流只计算一次，前后帧共用；复用灰度图。原稳定算法的加权、失配拒绝和邻帧合成顺序不变。四个 CPU 工作线程处理独立帧，OpenCV 单任务内部线程数设为 1。
2. 合成帧直接通过管道输入 FFmpeg，省去逐帧 PNG 压缩、落盘、读取。统一 RGB24 输入路径，与原 PNG 解码的颜色转换保持一致；仍使用 H.264 CRF 18、25 fps、512×768 和原音频。
3. 普通任务只保存 4–5 个诊断 PNG，另为每一帧保存 SHA-256 与嘴型权重到 frame-audit.json。需要完整 PNG 可在本机任务协议中设置 keep_frames=true。测试任务可设 audit=true 保留原始推理脸帧，普通请求不保留。
4. 新增嘴部稳定、合成编码、编码收尾的分项耗时，以及 pipeline_version=performance-v2。encode_s 在 v2 指管道关闭后等待编码器收尾，不能直接与 v1 的完整编码耗时比较；比较整体应看 postprocess_s 或 render_s。

两组算法对照使用完全相同的原始推理脸帧、动作源、遮罩和音频。安慰 109 帧与轻微不满 120 帧，优化前后送入编码器的帧哈希全部一致；最终 MP4 解码后的像素也全部一致（MSE=0）。对照脚本对此做硬断言。这验证了这次后处理加速没有改变这两组测试画面，不是任意输入的质量保证。

最终复测后处理耗时：安慰 7.640 → 2.844 秒，轻微不满 8.515 → 3.032 秒。早期测量曾有不同耗时，最终报告见 performance-v2-benchmark-comfort.json 和 performance-v2-benchmark-annoyed.json。

## 新语音完整链路

三个请求都重新合成语音，在模型预热后提交。旧版是上一轮已保存的测量，新版是本轮实测，非并发压测或 p95；TTS 网络和本机负载会影响结果。

| 场景 | 原等待 | 新等待 | 减少 | 新视频处理 / 视频长度 |
| --- | ---: | ---: | ---: | ---: |
| 安慰 | 16.842 s | 12.116 s | 28.1% | 9.688 / 4.36 s |
| 轻微不满 | 16.562 s | 11.305 s | 31.7% | 9.000 / 4.80 s |
| 思考 | 16.807 s | 11.446 s | 31.9% | 9.344 / 4.52 s |

数据保存在 performance-v2-live-benchmark.json；demo/performance-comparison.json 是供页面读取的副本。另有两条 benchmark_replay_of 任务只复用旧音频用于算法对照，不计入此表，页面历史列表不展示这类任务。

回归检查覆盖六个动作源、八条已完成视频（含两条同音频测试）。逐帧哈希确认静音释放后恢复动作源；抽样 PNG 与记录哈希一致；视频音轨与输入 PCM 同步。GPU 推理阶段及稳定后处理阶段取消均已实际测试，分别在 0.438 秒和 0.329 秒内释放任务。详情见 performance-api-check.json、performance-api-check-v2-postprocess.json。

另在 FFmpeg 已创建编码文件后实际取消，0.172 秒内释放任务；临时编码文件被移除，没有产出完整视频。记录见 performance-api-check-v2-encoding.json。

## 复用与回退

- 核心优化模块：scripts/performance_postprocess.py。接口 render 接收推理脸帧、动作帧、框、遮罩、时间权重和取消检查函数，返回分项耗时。
- 完整语音实测：scripts/benchmark_performance_live.py，会真实提交三条 TTS 任务。
- 同音频推理重放：scripts/replay_performance_audio.py <旧任务 ID>。仅在本地服务空闲时运行；只复用音频，仍实际进行嘴型推理。
- 精确算法对照：scripts/benchmark_performance_postprocess.py <含 inference-faces.npy 的任务 ID>。比较旧算法与新算法，保存两套视频并校验每一帧。
- 效果回归：scripts/verify_performance.py；取消回归：scripts/check_performance_api.py，可添加 --postprocess 或 --encoding。

脚本使用项目的 .cache/sadtalker-venv/Scripts/python.exe；HTTP 基准及取消检查可使用基础 Python。启动仍为 ./start-performance.ps1。

修改前的 worker、服务、页面与验证脚本保存在 .cache/releases/performance-v1-code；所有旧样例保留原路径。若需恢复旧推理流程，先等当前任务结束，停止 worker，将该目录的 performance_worker.py 复制回 scripts，再启动 worker。只回退 worker 时，当前页面仍能播放旧格式的结果。该目录是本机代码快照，不包含模型权重或独立运行环境。

## 下一步判断

现在主要时间在嘴型推理（约 5.3–5.9 秒）和合成编码（约 2.3–2.5 秒），语音另需约 2 秒。虽然等待减少，视频处理仍为片长的 1.88–2.22 倍，尚未满足连续实时输出。应继续测批次大小、推理精度/后端与分块编码的收益，再决定在线驱动路线。仅把 HTTP 改成流式无法使持续处理速度自动超过播放速度。

本轮没有改变表情强度、增加手臂动作或接入自由聊天。动作语义、跨表情衔接与对话产品闭环仍是后续工作。
