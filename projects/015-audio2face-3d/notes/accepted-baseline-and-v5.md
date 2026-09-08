# 保存已认可能力并优化（2026-09-08）

## 已保存的基线

用户认可的 tail-v4 已在修改前保存到 `.cache/releases/accepted-tail-v4`，另有同名 ZIP。快照共 100 个文件，压缩包约 13.9 MB，逐文件 SHA256 已验证。包括原成片与合集、匹配待机、输入语音与动作、模型来源记录、代码及检查报告。不包含密钥、Python 运行环境或大体积模型权重。

保存版独立运行于 `http://127.0.0.1:8021/`，直接使用快照内 UI、服务端代码和媒体；不依赖优化版的动态播放清单。已有模型及运行环境是重新进行神经网络生成的前提，不能把此 ZIP 当作包含全部模型的安装包。

```powershell
# 启动独立的原版播放，先校验快照完整性
D:/software/python310/python.exe scripts/serve_avatar_baseline.py
# 如需让 8020 回到原 UI/媒体（新代码和成片仍保留）
D:/software/python310/python.exe scripts/restore_avatar_playback.py
```

## 本次优化

1. 提取 `scripts/avatar_timing.py`：对干净的合成语音生成开口、停顿、收尾的权重与时间轴。超过 0.6 秒的句中静音才进入完整释放；短停顿不强制闭嘴。全静音不生成嘴部权重；轻声尾音有保留测试。
2. 增加配置 `config/companion-timing.json` 与入口 `scripts/render_avatar_timing.py`：从媒体读取帧率、时长、分辨率，不再在处理核心写死三个场景和 120 帧。读取现有已合成的帧与同一动作底片，输出成片、待机、时间轴和输入/输出哈希。
3. 当前三段实际句中停顿较短，因此没有修改这些停顿。新成片的可见变化集中在开口前：静音开始时先保持原姿态，再平滑进入说话状态。有效语音开始之后至片尾与 tail-v4 PNG 逐像素一致，音频相同，已认可待机视频直接复用。
4. 新播放器 `demo/complete-v5.js` 在媒体准备期间保留上一画面，用 220 毫秒过渡覆盖开口或切换的突变；打断时立即停声，并定位到当前动作底片的相同时刻，随后接对应待机。快速切换会取消过期加载，防止旧场景覆盖新场景。
5. 使用 `active-release.json` 原子切换播放清单，让片段、合集、待机指向同一版本。原 result.json 和 tail-v4 媒体保留。

不同场景之间仍可能有姿态差异，短暂画面过渡不能替代真正连续的人物表演。长停顿策略通过测试音频验证，当前三段短句没有足够长的句中静音，不能声称已在三段上展示长停顿效果。

## 复用和检查

```powershell
.cache/sadtalker-venv/Scripts/python.exe scripts/render_avatar_timing.py config/companion-timing.json
.cache/sadtalker-venv/Scripts/python.exe scripts/test_avatar_timing.py
D:/software/python310/python.exe scripts/activate_avatar_release.py
```

六组行为测试覆盖短停顿、长停顿释放与恢复、25/30/60 FPS、轻声尾音、全静音、音频持续到片尾和三段真实回归。其中变量帧率与静音场景测试针对时间轴模块，不代表完整模型推理已覆盖所有输入类型。

真实回归：有效语音开始到片尾最大像素差为 0；解码音频一致；已认可待机字节一致。记录在 `notes/timing-v5-verification.json`。

浏览器已检查新版播放、约一秒位置打断并回到对应无声动作、快速连续选择三个场景后只有最后一个生效、照片模式停止两路视频。连续播放与保存版由最终交付检查确认。

当前通用化的是离线时间处理与播放控制，尚未封装成完整的「任意照片＋任意台词」SDK。模型推理、动作选择、身份保持、噪声下语音活动判断和实时生成仍是后续工作。继续保持基线回放和真实观感验收，不以像素平滑指标替代用户判断。
