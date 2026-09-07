# 来源与许可

- 花园行者 `human-*.json/.glb` 为新增独立人形设计；头、身体、四肢与待机/行走/挥手参数在本研究中编写，经上游引擎编译。未复用官方人物或动作资产。

- 蓝金蝴蝶 `butterfly-*.json/.glb` 为新增独立设计，经 anyCreature 生成几何和振翅动画。花园几何、路线、暂停与进度控制为本研究新增展示代码；不属于上游库自动生成的场景。

- 苔灯蜗牛（`snail-0.json` / `snail-0.glb`）为本次会话从空白参数独立设计，经 anyCreature 通用引擎生成；未使用官方狼的参数、模型或动作。其他狼变体来源如下。

- anyCreature 1.2.0, commit `ab5b1ce5c13e632f00f7f7cbfdb7a746e315000d`，作者 Ariescar / Alsomind Tech Co., Ltd.：https://github.com/Ariescar/anyCreature
- 官方狼 JSON 和生成模型，以及本演示修改的体型、配色与弯角版本，基于该仓库的 MIT 授权内容。完整许可证见 [ANYCREATURE-LICENSE.txt](assets/ANYCREATURE-LICENSE.txt)。
- `assets/three-bundle.js` 来自上游的展示工具，包含 Three.js、GLTFLoader、OrbitControls；保留原文件内 MIT 许可。上游依赖说明见 [UPSTREAM-NOTICES.md](assets/UPSTREAM-NOTICES.md)。
- 本演示的中文界面、参数变体和构建脚本是研究项目新增内容；不是 anyCreature 官方界面，不代表官方视觉评审或生产认证。
- 页面不连接大模型，不上传模型。所有模型预先由原版引擎编译；Three.js 仅负责显示和播放。
