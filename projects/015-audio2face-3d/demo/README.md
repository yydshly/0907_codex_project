# 浏览器演示

这是官方 Mark 模型真实输出的独立浏览器播放器。运行方式与实测边界见 [项目说明](../README.md)。

- `index.html` / `style.css` / `app.js`：界面和三维播放。
- `assets/*.bin`：真实面部动画的压缩数据，以及官方人物拓扑/静态眼球。
- `assets/*.json`：实际推理配置与计时。
- `assets/*.wav`：本地生成的中文语音。
- `assets/*.coeffs.npy`：原始输出，用于数值验证，不复制到静态展示。
- `scripts/serve.py`：位于项目上一级的本机推理服务。

`python scripts/publish_static.py` 可准备静态站点文件，不进行外部发布。静态版仅回放，上传生成必须通过本机服务。
