# 句末静音嘴唇颤动修正（tail-v4）

用户指出“还好吗”说完后嘴唇继续颤动。检查发现 welcome 的有效音频约在 2.22 秒结束，而 mask-v3 对整段 4 秒画面都继续生成嘴型，没有句末静音状态。播放器结束后又直接换到通用待机动作，存在姿态跳变。

`scripts/settle_speech_tail.py` 对现有 mask-v3 输出做版本化收尾处理：

- 对干净的 TTS 音频计算 10 毫秒 RMS，使用保守的 -60 dBFS 阈值找最后有效声音，保留 100 毫秒缓冲。
- 只对最后一段静音执行 220 毫秒 smoothstep 过渡，从新生成的嘴型回到同帧原动作。句中停顿不处理，说话段不改动。
- welcome 在 2.32～2.54 秒过渡；playful 在 2.46～2.68 秒过渡；soft 在 2.51～2.73 秒过渡。
- 收尾后仍播放原动作中的头肩、身体和面部表情，未冻结整个人。原动作本身的生成瑕疵仍可能存在。
- 每段生成与结束姿态相同的 3 秒往返待机动作，使用余弦缓动；待机首尾帧与完整片段最后一帧在编码前完全一致。页面播放结束后先启动对应待机视频，再隐藏完整片段，避免直接换到无关姿态。

`scripts/verify_speech_tail.py` 验证三段：说话段 PNG 与 v3 最大像素差为 0；过渡后 PNG 与同帧原动作最大差为 0；身体区域最大差为 0；视频解码音频逐采样一致；完整片段 120 帧，待机 90 帧，待机首尾衔接一致。检查结果在 `notes/speech-tail-verification.json`。welcome 放大对照为 `.cache/complete/welcome/tail-v4/tail-comparison.jpg`。

页面默认「收尾修正版」指向 tail-v4，「上一版」指向用户指出问题的 mask-v3。合集为 `.cache/complete/showcase-tail-v4.mp4`。

这是对离线、干净合成语音的句末处理，不是适用于噪声输入的通用 VAD，也不解决说话期间模型自身的牙齿或嘴角重建问题。

```powershell
.cache/sadtalker-venv/Scripts/python.exe scripts/settle_speech_tail.py
.cache/sadtalker-venv/Scripts/python.exe scripts/verify_speech_tail.py
```
