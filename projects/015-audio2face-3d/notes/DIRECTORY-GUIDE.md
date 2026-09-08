# 项目目录与重新下载指南

本地项目位置：`F:\codex_project\0907_codex_project\projects\015-audio2face-3d`。记录日期：2026-09-08。

**GitHub 保存代码、说明和精选演示，并未保存完整的本地模型与运行环境。** 换电脑或删除本地依赖后，需要重新获取上游库、权重并安装环境；自己生成的人物素材则要从备份恢复，不能靠下载原库恢复。

## 1. 根目录分别存什么

| 目录 / 文件 | 内容 | Git 是否保存 | 重新使用时怎么办 |
|---|---|---|---|
| `scripts/` | 下载、推理、人物准备、服务、后处理与发布脚本 | 是，源码 | 按选择的链路执行；不要把所有历史脚本依次运行 |
| `demo/` | 页面模板、播放器、本地及公开交互代码 | 页面源码是；大部分生成资产不是 | 页面可恢复；本地素材要下载、重建或从备份恢复 |
| `assets/` | 项目说明用图片 | 当前已跟踪的文件是 | 随 Git 获取 |
| `config/` | 模型版本 / 散列清单与时序参数 | 是 | 作为下载和验证依据 |
| `notes/` | 原理、决策、恢复、效果与清理说明 | Markdown 等已跟踪文件是；多数运行 JSON 不公开 | 先看 REVIEW-MAP 与 START-HERE，勿把历史状态当作当前状态 |
| `vendor/` | 上游代码、模型权重、三维角色资产 | **否** | 根据下一表重新获取固定版本 |
| `.venv/` | Audio2Face 的 Python / ONNX / CUDA 依赖 | **否** | 重新创建环境、安装 `requirements.txt` |
| `.cache/` | 视频运行环境、人物、生成任务、中间缓存与基线 | **否** | 区分可重建依赖和不可直接恢复的个人素材，见第 3 节 |
| `.env.companion` | 本机服务配置或共享配置引用 | **否** | 由 `.env.companion.example` 创建，重新配置 MiniMax；不提交真实密钥 |
| `start*.ps1` | 各版本服务启动入口 | 是 | 仅启动已准备环境，不能自动补齐所有模型 |
| `requirements.txt` | 3D 路线依赖版本 | 是 | 视频路线另看 `scripts/*requirements.txt` |

仓库外层 `docs/demos/015-audio2face-3d/` 保存精选静态页面与演示素材，是公开回放包；它不能替代 `vendor/`、人物缓存和后端环境。

## 2. vendor：哪些库与模型需要重新下载

| 本地目标目录 | 用途 | 获取入口 / 版本依据 |
|---|---|---|
| `vendor/Audio2Face-3D` | NVIDIA 原库入口 | [setup.ps1](../scripts/setup.ps1) 内固定提交 |
| `vendor/Audio2Face-3D-SDK`、`Audio2Face-3D-training-framework` | SDK、训练参考资料；当前不运行训练 | 同上，按脚本固定版本 |
| `vendor/Maya-ACE` | Mark 几何来源 | 同上；需要 Git LFS 获取指定几何文件 |
| `vendor/models/mark-v2.3` | Audio2Face 推理权重与数据 | [download_model.py](../scripts/download_model.py)，由 setup.ps1 调用 |
| `vendor/Camila` | 写实三维角色，仅本地评估 | [setup_camila.py](../scripts/setup_camila.py)，先读其来源与许可 |
| `vendor/MuseTalk` | 视频口型算法代码 | 从 `https://github.com/TMElyralab/MuseTalk` 获取；实际 checkout 提交见 [版本索引](revisit-inventory.json) |
| `vendor/musetalk-models` | U-Net、VAE、Whisper 权重 | [download_musetalk.py](../scripts/download_musetalk.py)，脚本内固定 Hugging Face revisions |
| `vendor/LivePortrait` | 本地表情与头部动作代码 | 从 `https://github.com/KwaiVGI/LivePortrait` 获取；实际提交见版本索引 |
| `vendor/LivePortrait/pretrained_weights` | LivePortrait 权重 | [download_liveportrait.py](../scripts/download_liveportrait.py) 与 [模型清单](../config/liveportrait-models.json)，校验 SHA-256 |
| `vendor/photo-models` | 共享人脸检测、对齐、分割；另有旧 SadTalker 权重 | [download_photo_models.py](../scripts/download_photo_models.py)；当前脚本同时下载新旧路线所需文件，不是最小下载器 |
| `vendor/SadTalker` | 旧版 8017/8018 照片说话实验 | [setup_photo.py](../scripts/setup_photo.py) 获取旧路线代码及环境；当前主口型链路是 MuseTalk |

版本索引记录的是当时本机 checkout 和清单，不保证上游链接永久有效。下载脚本存在不代表已验证空白机器一键安装。恢复时应核对代码提交、依赖和权重完整性。

MiniMax 对话、TTS、Hailuo 使用远端 API，本项目不下载它们的模型权重。LTX-Video 是早期远端生成动作素材的来源，也不应预期在本地找到完整 LTX 权重。

## 3. cache：哪些能重建，哪些应备份

| 子目录 | 内容与恢复方式 |
|---|---|
| `.cache/sadtalker-venv/` | **当前视频运行环境**，名称遗留；不要按名称认定已废弃。需要重新安装 Python/PyTorch 与视频依赖，不能用下载单个库替代 |
| `.cache/avatars/` | 用户人物、动作、状态、口型缓存；应单独备份。丢失后重新准备可能需要再次调用 Hailuo 并消耗额度 |
| `.cache/performance/` | 内置小晴动作与缓存；公开构建和工作台会读取。备份或按历史准备流程重建 |
| `.cache/performance-jobs/`、`.cache/dialogue-sessions/` | 生成音频、视频、任务与会话；可能含私人内容，不公开上传，按需求私下备份 |
| `.cache/complete/`、`.cache/motion/` | 8020 完整效果与早期动作素材；保留原素材才能重新比较优化效果 |
| `.cache/releases/` | 阶段基线，不能当作完整环境镜像 |
| `.cache/camila/`、`demo/assets/` | 三维角色处理结果、几何、音频与动画数据；按相应脚本重建或备份；公开站只保留选定 Mark 样例 |
| `.cache/public-recording/` | 录屏、原始帧和发布所需素材；当前发布脚本直接读取，删除前应保留所需文件 |
| `demo/public-preview/` | 公开站的额外本地预览副本，可从 `docs/demos/015-audio2face-3d/` 重建 |

## 4. 以后恢复的最短路径

1. **只回顾效果**：直接打开公开站，无须重新下载模型。也可回放 Git 内的精选素材。
2. **恢复 3D 推理**：准备 Python 3.10、Git / Git LFS，在项目目录执行 `./scripts/setup.ps1`，检查权重和几何后执行 `./start.ps1`。Camila 属于额外步骤。
3. **恢复视频与对话**：获取 MuseTalk / LivePortrait 对应代码及权重、共享辅助模型，恢复视频 Python 环境和 FFmpeg，再恢复人物动作包、配置 MiniMax，最后执行 `./start-performance.ps1`。历史 `setup_photo.py` 仅是旧环境基础步骤，不能单独完成当前全链路安装；依赖参考 `scripts/photo-requirements.txt`、`scripts/musetalk-requirements.txt` 等和 [START-HERE](START-HERE.md)。
4. **先验证回放再生成**：确认人物选择、动作视频和模型就绪，再做短台词测试，最后测试完整聊天。云端调用只在需要新结果时进行。
5. **重新发布静态站**：需要保留本地精选素材，执行 `python scripts/publish_static.py`；网页文档构建还需要 Python `markdown` 包。仅 clone 后缺少这些素材时，不能直接重建全部公开包，但已提交的公开包可以回放。

## 5. 当前清理状态与占用

F 盘项目曾测得约 **18.18 GiB**（硬链接去重后的逻辑大小），主要为环境、权重和生成素材。**本项目 F 盘目录尚未清理。** 已执行的只是 C 盘 19 个匹配 pip 下载缓存及配套元数据，约 7.20 GiB；它们不是项目运行环境，删除后当前环境仍保留，以后重装需要重新下载包。

详细占用与已执行范围见 [本地存储记录](LOCAL-STORAGE.md)。该记录是时间点快照，不是未来删除授权。后续清理模型 / 人物 / 环境应先确认具体目录及影响。

继续分析见 [能力与复现索引](REVIEW-MAP.md)。原库许可、模型许可与人物素材许可分别查看 [第三方说明](../demo/THIRD_PARTY_NOTICES.md)。
