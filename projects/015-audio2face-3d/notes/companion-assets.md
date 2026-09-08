# 小晴：素材与能力记录

2026-09-08。本次使用 imagegen 内置工具，未使用 CLI/API fallback。

## 肖像

原创虚构成年女性，27 岁。三张图均由内置 imagegen 生成；两张表情变体以第一张为输入，保持身份、服装、背景和构图。

- `.cache/companion/neutral.png`：来源 `exec-74a4261d-4293-4224-beda-c3eff2145fc9.png`。
- `.cache/companion/playful.png`：来源 `exec-a0e2efa8-19b3-4610-8678-ab7b33fd125b.png`。
- `.cache/companion/angry.png`：来源 `exec-afcb6221-f8f9-4512-bc19-773153dd9b2d.png`。
- 安慰状态复用 neutral 肖像，改变台词和语音参数。

最终提示词：

```
Use case: photorealistic-natural. Asset for a local AI voice companion demo. Create one photorealistic waist-up portrait of an original fictional adult East Asian woman, age 27, natural shoulder-length dark brown hair with soft bangs, warm expressive brown eyes, subtle natural makeup, wearing a modest cream knit cardigan over dusty rose top. Facing camera directly, head upright, shoulders relaxed, lips gently closed with very slight friendly smile. Both shoulders and upper torso visible, hands relaxed below frame. Cozy softly blurred warm apartment background with a plant and warm lamp, soft even daylight on face, realistic skin detail. Camera static frontal portrait, face clearly visible and large enough for face animation, head centered horizontally, generous space above head, composition from head to waist. Vertical image. No text, no watermark, no collage, no celebrity likeness. Suitable for talking-head animation.
```

```
Edit this exact fictional adult woman's portrait for the playful expression state of a talking companion. Preserve her exact identity, hairstyle, outfit, entire background, camera position and image dimensions. Only change facial expression and a very slight head tilt: a mischievous knowing smile with lips closed, one eyebrow slightly raised, eyes looking at viewer, head tilted just 4 degrees. No hand gestures, no text. Keep face position and scale nearly identical to reference, natural photorealistic subtle expression.
```

```
Edit this exact fictional adult woman's portrait for the mildly mock-annoyed expression state of a talking companion. Preserve her exact identity, hairstyle, outfit, entire background, camera position and image dimensions. Change facial expression ONLY: eyebrows slightly furrowed, lips gently pressed in a tiny pout, chin raised just a touch, eyes still looking straight at viewer. Clearly readable teasing annoyance but subtle and natural, not rage or distress. Keep head position and face scale identical for lip animation. No hand gestures, no text, photorealistic.
```

## 声音和动作

[edge-tts](https://github.com/rany2/edge-tts) 7.2.8 调用在线合成，声音 `zh-TW-HsiaoChenNeural`。四种语速/音高与台词记录于 `scripts/companion_media.py` 和各片段 metadata.json；不是 MiniMax 音频，不是专门的情绪 TTS，也没有克隆真人声音。

[MiniMax 官方同步 TTS](https://platform.minimax.io/docs/api-reference/speech-t2a-http) 适配器使用服务端 Bearer 密钥、十六进制音频输出和 emotion 参数。未配置账户，真实调用尚未验证。配置模板为 `.env.companion.example`；不把账户音色是否具有台湾口音当作已验证事实。

人物由现有 SadTalker 环境生成，`--preprocess full --still --enhancer gfpgan --size 256 --batch_size 1`，不同 pose_style。原始肖像在模型输入阶段缩至 512×768，生成人脸贴回，增强后编码为 512×768。衣服、手臂和背景静态，不能声称全身动作生成。

## 对话能力边界

点击情景会选取固定台词与视频，不执行语义理解或 LLM。自定义台词会实际调用 TTS 并离线运行人物模型，并非实时聊天；只把指定台词读出。真正实时对话仍需 LLM、ASR、流式语音与低延迟人物驱动集成。
