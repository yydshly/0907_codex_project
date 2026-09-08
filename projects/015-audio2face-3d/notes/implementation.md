# 实现与证据

日期：2026-09-08。具体 commit 见项目 README。

## 从官方代码核对的接口

- SDK：`audio2face-sdk/source/samples/sample-a2f-low-level-api-fullface/main.cpp`：Mark 真实输入、隐式情绪数据库、PCA 资源、音频窗口和全脸输出。
- SDK：`audio2face-sdk/source/audio2face-core/model_regression.cpp`：表情向量先 16 维隐式表情，再 10 维显式表情。
- 训练框架：`audio2face/audio/audio_track.py`：按音频时间取中心窗口、边界补零。
- 训练框架：`audio2face/networks/conv_w2v_autocorr.py`：输出依次为皮肤、舌头、下颌/眼球。
- 训练框架：`audio2face/layers.py` 的 PCA：`coeffs @ shapes_matrix + shapes_mean`。
- 发布模型 `network_info.json`：8320 样本窗口、4160 偏移、16kHz、皮肤 272 维、舌头 10 维、下颌 15 维、眼球 4 维，合计 301。
- 注意：论文中的部分通用维度示例与该发布模型并不相同；本实现读取/核对发布文件，使用 Mark v2.3 的 272 维皮肤系数。

## 适配器

`scripts/inference.py` 使用官方 ONNX 模型，30 FPS、16 帧 batch，波形限制在 [-1,1]，以正确时间居中切片。隐式表情使用官方 model_config 指定的 `g2a_neutral` 第 33 帧；显式 neutral 为全零，joy / anger 指定对应维度为 1。

得到的 301 维原始结果保留在每段 `.coeffs.npy`。网页只使用皮肤通道；PCA 重建后的形变采用每段 SVD 24 维压缩以减小静态资源体积，int16 基底逐分量保存缩放值，浏览器按音频 currentTime 选帧回放。不使用音量张嘴、随机表情或预设口型替代真实模型输出。

`scripts/extract_geometry.py` 只解析官方 `mark_geom_v2_topo1.ma` 的数字顶点/边/面属性，不执行 Maya 场景脚本。Maya 有向边按正负符号恢复 polygon，再作扇形三角化；检查 61520 顶点、123036 三角形以及索引覆盖。眼球部件为静态资产；材质、灯光和浏览器 UI 为本项目提供。

## 运行层差异

本机未安装 TensorRT 开发包/完整 CUDA Toolkit，也未编译 C++ SDK。为降低首次查看门槛，采用 ONNX Runtime CUDA，所需 CUDA/cuDNN/cuFFT 动态库安装在独立虚拟环境。模型权重和人物数据都是官方文件；播放器是自编适配，不应标为“官方 SDK 全功能复现”。

CPU 初次验证：9.37 秒音频推理约 6.99 秒。随后配置 GPU；GPU 六组计时见 inference-results.json。显卡执行提供程序为 CUDAExecutionProvider，保留 CPUExecutionProvider 用于不支持的节点。

## 后续扩展

1. 接入舌头、牙齿、眼球变换及完整 SDK 后处理，提高口腔与眼部表现。
2. 对比 v2.3 与 v3，测量完整生成耗时、音画偏差、中文闭唇和圆唇质量。
3. 将完整输出通过 Blendshape 映射到自己的角色，再接语音助手。
4. 用户需要实时交互时，再设计流式缓冲、打断、倾听状态与并发调度。

## 官方资料

- https://github.com/NVIDIA/Audio2Face-3D
- https://github.com/NVIDIA/Audio2Face-3D-SDK
- https://github.com/NVIDIA/Audio2Face-3D-training-framework
- https://github.com/NVIDIA/Maya-ACE
- https://huggingface.co/nvidia/Audio2Face-3D-v2.3-Mark
- https://arxiv.org/abs/2508.16401
