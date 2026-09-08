# 本地内容盘点与待确认清理方案

盘点日期：2026-09-08。状态：**仅盘点，尚未获清理确认，未删除文件或停止服务。**

范围仅限 `projects/015-audio2face-3d/`。没有扫描或计划删除其他子项目、系统共享 pip / Hugging Face 缓存、仓库 `.git`，也不包含仓库外的共享 MiniMax 配置。只读取文件元数据与相关代码，未读取密钥内容或会话正文。

## 实际占用如何理解

文件路径大小合计约 **18.86 GiB**；按文件标识去除硬链接重复计数后约 **18.18 GiB**。这是逻辑字节估算，不是文件系统分配簇的精确占用；压缩、稀疏文件等会影响实际释放空间。

`vendor/SadTalker/gfpgan/weights` 中四个文件与 `vendor/photo-models` 使用硬链接，合计约 0.69 GiB，不能重复计入释放量。不能看到两个同名文件就按两份下载处理。

## 大目录与影响

| 目录 | 路径大小 GiB（可能含硬链接） | 用途与清理影响 |
|---|---:|---|
| `.cache/sadtalker-venv` | 5.098 | 当前 MuseTalk / 视频运行环境；名称历史遗留。进程仍在使用，不能当作旧 SadTalker 环境删除。 |
| `vendor/musetalk-models` | 3.619 | 当前口型权重；删除后无法生成新口型，须重新下载。 |
| `.venv` | 2.822 | Audio2Face / ONNX / CUDA 环境；3D 服务进程仍在使用。 |
| `vendor/photo-models` | 1.652 | 旧 SadTalker 权重与当前共用人脸检测、关键点、分割权重混放；不得整目录删除。 |
| `.cache/complete` | 1.079 | 8020 已接受效果、原动作、优化对照与中间产物；保留，公开构建仍读取。 |
| `.cache/avatars` | 1.028 | 人物、动作与缓存；保留，重建可能再次消耗远端视频额度。 |
| `vendor/SadTalker` | 0.822 | 早期 8017 / 8018 路线；可作为退役候选，但其删除会使旧版新生成不可用。 |
| `.cache/performance-jobs` | 0.645 | 音频、成片与任务记录，部分被公开构建引用；不要整目录删除。 |
| `vendor/LivePortrait` | 0.560 | 本地面部动作模型与上游；保留当前人物准备能力。 |
| `.cache/performance` | 0.474 | 内置小晴动作与口型缓存；当前工作台及公开构建依赖。 |
| `vendor/models` | 0.298 | Audio2Face Mark 权重；保留 3D 推理。 |
| `vendor/Maya-ACE` | 0.149 | Mark 三维几何来源；保留。 |
| `vendor/Camila` | 0.132 | 本地写实 3D 角色；保留本地展示。 |
| `demo/public-preview` | 0.073 | 已发布静态文件的额外本地副本；可重建，删除只影响 /public-preview/。 |
| `.cache/public-recording` | 0.038 | 录屏原始帧、视频和校验记录；当前发布脚本依赖其中素材，暂不删。 |
| `.cache/releases` | 0.035 | 阶段基线备份；后续分析需要，保留。 |

## 等待用户确认的具体选项

### A. 只清理重复预览（最保守）

仅删除 `demo/public-preview/`，预计释放约 **74.3 MiB**。当前本地工作台、人物对话、8020 和远端站点不依赖该副本；本地 `/public-preview/` 将失效。需要时重新构建公开站并复制即可恢复。

### B. A + 退役旧 SadTalker 实验

额外删除以下精确目标：

- `vendor/SadTalker/`
- `vendor/photo-models/SadTalker_V0.0.2_256.safetensors`
- `vendor/photo-models/mapping_00109-model.pth.tar`
- `vendor/photo-models/mapping_00229-model.pth.tar`

这四项扣除仍被保留的硬链接后预计释放 **1.10 GiB**，与 A 合计约 **1.17 GiB**。影响：8017 / 8018 的旧 SadTalker 新生成不能继续使用；已有成片和源代码仍保留。恢复需重新获取旧库与对应权重，可参考 `scripts/setup_photo.py`、`scripts/download_photo_models.py`；历史安装环境仍需实际检查。

**必须保留** `.cache/sadtalker-venv/` 以及 `vendor/photo-models/` 下的 `alignment_WFLW_4HG.pth`、`detection_Resnet50_Final.pth`、`parsing_parsenet.pth`、`GFPGANv1.4.pth`。其中检测、对齐、分割仍被当前代码引用。本次方案不修改共享权重路径或运行环境。

### C. 暂不清理

保留全部运行与历史能力，只保留这份盘点，后续决定。

若想释放更大空间，需要另行决定是否放弃本地视频生成或 3D 推理，再制定环境 / 权重清理清单；不能将本次确认扩大为删除全部 `.cache` 或 `vendor`。

## 执行前后的检查（尚未执行）

1. 用户明确选择方案；执行前重新计算目标大小与链接，避免把本次数字当作实时状态。
2. 解析每个目标的绝对路径，确认严格位于项目内；检查相关进程，不删除仍使用中的模型环境。
3. 使用 PowerShell 原生文件操作，仅处理获批清单；不做自动扩大范围的递归清理。
4. 核对保留的共享权重、人物素材和本地页面；补记实际释放空间、删除清单与验证结果。

完整目录计数在本地 `.cache/storage-inventory.json`；硬链接感知的候选清单在 `.cache/storage-cleanup-proposal.json`。这些本地清单没有密钥或会话正文。后续删除行为必须有新的用户确认。

## C 盘补充盘点（仅检查常见缓存位置）

同日检查。C 盘总已用约 278.43 GiB、剩余约 27.58 GiB（采样时）。下表是路径下逻辑文件大小，未对跨目录硬链接去重，不等于全部可释放空间。多个项目共享，不能归因于本项目；未删除任何内容。

| 路径 | GiB |
|---|---:|
| `C:\Users\yun68\.cache` | 1.91 |
| `C:\Users\yun68\AppData\Local\pip` | 12.55 |
| `C:\Users\yun68\AppData\Local\ms-playwright` | 2.75 |
| `C:\Users\yun68\AppData\Local\Temp` | 14.77 |
| `C:\Users\yun68\AppData\Local\uv` | 5.22 |
| `C:\Users\yun68\AppData\Local\npm-cache` | 16.13 |

项目安装到 F 盘时，pip/npm/uv 的下载与安装缓存仍可能默认落在 C 盘，形成项目环境与下载缓存两份存储。Temp 包含其他研究和工具任务目录；Playwright 包含多个 Chromium 版本。以上不能整体自动删除，需单独确认清单，检查活动任务与重建成本。原始元数据记录 `.cache/c-drive-storage.json`。

## C 盘与本项目依赖精确匹配的候选

核对 pip 缓存中大于等于 20 MiB 的 wheel 包元数据，与项目两套环境的 dist-info 名称及版本精确匹配：共 19 个缓存文件，去重文件标识后约 7.20 GiB。主要为 torch 2.1.2+cu121（两份约 4.61 GiB）、cuDNN 9.25.1.1、cuBLAS 12.9.2.10（两份）、ONNX Runtime GPU 1.23.2 与其他已安装依赖。

这证明缓存内容对应本项目依赖，不证明由本项目独占产生；可能被其他项目共享。它们是 C 盘 pip 下载缓存，不是 F 盘已安装环境。可以作为单独待确认清理项：删除精确匹配清单及其缓存条目元数据，不卸载环境，不清空全部 pip 缓存。预期不影响已安装项目运行，但以后重新安装相关版本需再次下载。尚未删除，也未获得本项清理确认。

精确路径清单在 `.cache/c-project-cache-matches.json`（只处理 matches_project_installed=true 的条目）。C 盘 npm、uv、Temp 未建立本项目专属归因，本次不列入清理；Codex 和 Playwright 运行环境是共享工具依赖，保留。

## 已执行：获批的 C 盘 pip 缓存清理

用户在 2026-09-08 确认清理上述 19 个匹配条目。已删除 19 个包缓存文件及 10 个配套 HTTP 元数据文件，共约 **7.196 GiB**，失败 0 项。清理后采样 C 盘可用约 **34.79 GiB**。已核对目标消失，项目两套 Python 入口、MuseTalk 主权重、人物目录和人脸检测权重仍存在；未重新调用模型生成。

仅此 C 盘清单已执行；前述 F 盘 A/B 方案未执行。其他 pip 包、npm、uv、Temp、浏览器及 F 盘文件未清理。逐项结果保存在 `.cache/pip-cleanup-result.json`，执行前清单在 `.cache/approved-pip-cleanup.json`。以后重装被清缓存的包需要重新下载。
