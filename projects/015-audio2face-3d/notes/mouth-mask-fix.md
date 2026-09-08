# 口腔融合错误修复（mask-v3，2026-09-08）

用户否定 stable-v2 的嘴部质量后，检查实际 ParseNet 分割输出发现一个明确的接入错误：原代码使用 MuseTalk BiSeNet 的类别 `[1,11,12,13]`，但本机替代模型 ParseNet 的类别是 `1=皮肤、10=口腔、11=上唇、12=下唇、13=头发`。这导致原视频的口腔/牙齿没有被充分覆盖，与新生成的嘴型混合。

诊断图 `.cache/complete/parsing-diagnostic.jpg` 逐类显示实际模型输出，类别 10 覆盖口腔，类别 13 覆盖头发。修正 `scripts/musetalk_complete.py` 的映射为 `[1,10,11,12]`，其他时序与编码参数沿用 v2，重生成三个片段到各自 `mask-v3` 目录，保留旧文件。

## 回归证据

执行 `scripts/verify_mouth_mask.py`，结果在 `notes/mouth-mask-verification.json`：

- 检查全 19 类映射：仅皮肤、口腔和上下唇进入覆盖区域，头发不进入。
- 调皮片段三个张嘴样本的口腔平均融合权重由 0.32～0.45 提升到 1.0；轻松回应由 0.37～0.48 提升到 1.0。即抽查区域原先残留约一半以上旧画面，现被完整覆盖。
- 欢迎片段原动作基本闭嘴，口腔区域很少，修复对此段的收益有限，不能声称所有嘴部问题由这一个错误导致。
- 三段均 120 帧；与 v2 解码音频逐采样相同；编码前第 410 行以下身体像素最大差为 0。
- 三组源动作/v2/v3 放大截图位于各 `mask-v3/comparison.jpg`。调皮和轻松回应的旧牙齿残留得到修正，仍可见模型生成牙齿模糊和手部靠脸时的融合缺陷。

上一次「时序残差降低 8%～14%」不能作为质量验收：残留不动的原牙齿也可能降低时序变化。用户已否定 v2，不能继续把它描述为合格结果。

## 播放

8020 默认播放 mask-v3，按钮为「口腔修正版 / 上一版」，上一版准确指向用户本次否定的 stable-v2。合集为 `.cache/complete/showcase-mask-v3.mp4`。尚未实现自然真人级嘴型质量；本次明确修复的是口腔分割映射错误。

复现：

```powershell
.cache/sadtalker-venv/Scripts/python.exe scripts/stabilize_complete.py
.cache/sadtalker-venv/Scripts/python.exe scripts/verify_mouth_mask.py
```

`stabilize_complete.py` 当前默认输出 `mask-v3`，旧 v2 文件保持保留。
