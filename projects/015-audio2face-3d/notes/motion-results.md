# 照片 → 半身动作验证

2026-09-08。已经真实生成四段无声图生视频，三种动作意图，其中倾听有两版。

输入均为 `.cache/companion/neutral.png`，是此前内置 imagegen 生成的虚构成年女性，不是实拍个人照片。

生成渠道：[LTX-Video 官方 Hugging Face Space](https://huggingface.co/spaces/Lightricks/ltx-video-distilled)。生成时 Space 修订为 `8a42e93469c66b62d794b83a4233f5fc8439e2b5`，官方应用采用 `ltxv-13b-0.9.8-distilled.yaml`。上传原创参考肖像，使用远程 GPU，结果下载到本机；不是本机推理，也不是 CSS 图片平移或 SadTalker 动画。

## 实际结果

| 动作意图 | 文件夹 | 请求参数 | 本次调用耗时 | 观察 |
|---|---|---|---|---|
| 倾听第一版 | `.cache/motion/listen` | CFG 1、多尺度、seed 42 | 15.1 秒 | 有头部和躯干运动，但背景明显漂移 |
| 调皮第一版 | `.cache/motion/playful` | CFG 1、多尺度、seed 43 | 18.0 秒 | 微笑、明显抬手到头顶；超出原本小幅耸肩要求 |
| 佯怒第一版 | `.cache/motion/annoyed` | CFG 1、多尺度、seed 44 | 12.0 秒 | 有侧头和抬手，情绪却偏微笑；佯怒未达标 |
| 倾听第二版 | `.cache/motion/listen-v2` | 简化提示、CFG 3、单尺度、seed 42 | 24.0 秒 | 背景相对稳定，头肩和身体动作有所改善；尚未达到无缝循环和严格身份保持 |

输出均为 512×768、30 FPS、121 帧，时长 4.033 秒，无音轨。上述耗时是本次远程队列、生成及下载耗时，不代表本机性能或稳定服务延迟。

原始提示词、种子和完整参数在 `scripts/generate_motion.py` 及各文件夹 `generation.json`。人工评价在 `.cache/motion/selection.json`，技术完整性检查在 `notes/motion-verification.json`。

## 后续阻塞

第二轮调皮提交被官方 Space 的 ZeroGPU 免费配额拒绝：`You have exceeded your ZeroGPU quota`。没有继续重试、切换账户或绕过配额。第二轮佯怒尚未提交。三种动作不能全部标记为验收通过。

需要可用的远程视频生成额度或合适的本地运行环境，才能继续筛选和优化。当前机器 8GB 显存、16GB 内存，检查时可用内存约 3GB、F 盘剩余约 35GB，因此本轮使用官方在线模型做效果验证。

## 查看与重跑

```powershell
./start-motion.ps1
# http://127.0.0.1:8019/
./.venv/Scripts/python.exe -m pip install -r scripts/motion-requirements.txt
./.venv/Scripts/python.exe scripts/generate_motion.py listen playful annoyed
# 第二轮：保留原片段，另存 -v2；需要服务端可用额度
./.venv/Scripts/python.exe scripts/generate_motion.py listen playful annoyed --refine
```

播放页采用已缓存文件，不需要再次调用在线模型。循环选项只是重复播放，不代表已经做了首尾动作融合。没有接入语音、嘴型重新生成或实时聊天。
