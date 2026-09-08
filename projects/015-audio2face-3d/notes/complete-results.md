# 动作 + 语音 + 新嘴型：完整效果

2026-09-08。三段各 4 秒的真实有声视频已生成，并导出 12 秒合集。浏览器入口 `http://127.0.0.1:8020/`，启动 `./start-complete.ps1`。

## 实际链路

1. 已生成的 LTX-Video 半身动作提供头部、身体、手臂和背景画面。
2. Edge TTS `zh-TW-HsiaoChenNeural` 合成三句新台词，每句约 3.1 秒，在末尾补静音以匹配视频长度。
3. RetinaFace 逐帧检测，FAN 98 点转 68 点关键点，形成经过中心平滑的脸部框。
4. Whisper-tiny 提取音频特征；MuseTalk 1.5 的官方 VAE、位置编码和 UNet 根据音频生成脸部。
5. ParseNet 分割皮肤与嘴部，用上游融合函数只融合下半脸，原视频其余区域保留。
6. 编码 H.264/AAC 视频，512×768、30 FPS、120 帧，输出 4 秒。合集是三段顺序拼接，不声称无缝表演。

MuseTalk 官方代码：`0a89dec45a0192b824e3cf4daf96c239440c5ed8`，MIT。核心模型来自官方 HF 仓库；模型及辅助权重适用各自许可，模型卡标示 CreativeML OpenRAIL-M。权重修订、URL、大小与 SHA256 记录于本机 `vendor/musetalk-models/manifest.json`。

本地适配替换了官方 DWPose/MMCV 预处理及面部分割模块，复用现有 facexlib RetinaFace/FAN/ParseNet；因此是基于官方 MuseTalk 核心模型的集成，并非原样运行官方完整脚本。没有使用 Audio2Face 驱动这些照片视频。

## 结果

| 场景 | 实际台词 | 动作素材 | 嘴型渲染耗时 |
|---|---|---|---|
| 欢迎回来 | 你來啦，今天還好嗎？ | listen-v2 | 26.0 秒 |
| 调皮提醒 | 被我發現了吧，你又熬夜喔！ | playful | 25.1 秒 |
| 轻松回应 | 好啦，逗你的，別緊張嘛。 | annoyed | 23.8 秒 |

第三个素材虽原名 annoyed，实际动作偏微笑；成片按实际表演命名为“轻松回应”，没有声称实现生气。语音未使用 MiniMax，也没有专门情绪 TTS 控制。

耗时不含初次权重下载、模型启动、TTS 和人脸跟踪；不是实时推理速度。模型在 RTX 4070 Laptop 8GB 上以 FP16、batch 1 运行。音频编码与图像生成分进程，UNet 权重通过 mmap 加载以减少内存开销。

## 验证

`notes/complete-verification.json` 记录三段输出：均有正确的视频与音频轨道，音频与输入相关系数大于 0.9998；独立抽帧对比发现下半脸发生实际变化，编码前身体区域与原帧像素差为 0；身体区域随时间变化保留。

这些检查证明实际生成、音轨完整和身体画面保留，不等于专业音素口型同步、身份保持或自然度评测。采样画面已检查：头部与嘴型一起运动，调皮的举手、轻松回应的手部动作保留。嘴部和面部细节仍存在模型生成痕迹。

网页支持：连续播放三段、单段选择、打断、静音、完整成片/原始动作/原照片对比、陪伴视图、单段及合集下载。等待状态为静音动作循环。尚未接自由聊天、语音识别或实时动作生成。

## 重跑

```powershell
# 现有 SadTalker 运行环境上增加 MuseTalk 所需包
./.cache/sadtalker-venv/Scripts/python.exe -m pip install -r scripts/musetalk-requirements.txt
python scripts/download_musetalk.py
python scripts/prepare_complete.py
./.cache/sadtalker-venv/Scripts/python.exe scripts/musetalk_complete.py --prepare
./.cache/sadtalker-venv/Scripts/python.exe scripts/musetalk_complete.py --audio
./.cache/sadtalker-venv/Scripts/python.exe scripts/musetalk_complete.py
./.cache/sadtalker-venv/Scripts/python.exe scripts/verify_complete.py
./start-complete.ps1
```

需要已获取官方 MuseTalk 仓库和本地动作素材。所有视频、照片、权重和中间帧保存在 Git 忽略目录 `.cache`、`vendor`，未发布到静态网站。新增 Python 依赖已通过 pip check。
