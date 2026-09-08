# 用户自助人物接入 v1

入口：<http://127.0.0.1:8022/characters>。用户上传照片、填写名称，等待自动检查和准备，预览六种动作，点击“使用此人物对话”或“输入台词测试口型”。没有逐人物修改代码、手画遮罩或提供另一个人的表情参考图这一步。

## 能力边界

- 接近正面的单人近景或半身照片，静态 JPG/PNG/WebP，最大 12 MB、2000 万像素，短边至少 256 像素。
- 自动检查解码、尺寸、单人脸、人脸大小及俯仰/侧转角度。检测不是对遮挡、模糊、风格化照片的全面质量保证。
- 同一套 LivePortrait 控制生成倾听、思考、安慰、调皮、轻微不满、肯定；包括眼神、眨眼、表情和小幅头动。不会从一张照片生成新的手臂动作。
- 自助人物的“不满”使用自身照片的通用表情控制，强度可能低于原始角色专用愤怒照片的效果。绝不借用原始角色的脸。
- MiniMax 对话与语音继续复用。换照片只换视觉形象，保留当前 AI 伙伴性格和配置音色，不等于照片人物的真实身份、性格或声音，也没有新增音色选择界面。
- 每轮仍需等待视频生成，保留首句就绪播放、后句并行准备和打断；不是实时视频流。

## 稳定接口与资产

`avatar_registry.py` 是统一入口：`get / asset_root / asset_for`。历史无 avatar_id 的任务默认为 `xiaoqing`，继续使用 `.cache/performance`，原始素材没有重建或覆盖。

自助人物存储在 `.cache/avatars/<32位ID>/`：

| 内容 | 用途 |
|---|---|
| avatar.json | 人物名称、状态、版本、来源哈希、任务 ID、公开媒体前缀 |
| source.png | 去除 EXIF、等比缩放补边后的 512×768 RGB 照片 |
| assets/manifest.json | 六种表情动作及预览路径 |
| assets/<state>/ | motion.mp4、跟踪框、平滑遮罩、确定性 VAE 缓存、审计帧 |
| validation.json | 来源哈希、帧数、循环连续性与动作变化校验 |

每次上传创建独立且不覆盖旧人物的 ID。资产版本为 `portrait-pack-v1`，每个动作缓存绑定对应视频 SHA-256。人物状态经过 queued → preparing → ready；失败或取消不会进入可用人物列表中的“开始对话”入口。

| HTTP 接口 | 含义 |
|---|---|
| GET /api/avatars | 人物库与资源占用状态 |
| GET /api/avatars/:id | 单个人物状态 |
| POST /api/avatars?name=... | 原始图片 bytes，Content-Type application/octet-stream |
| GET /api/jobs/:id | 准备或对话进度 |
| POST /api/cancel/:id | 取消任务；保留失败/取消记录 |
| POST /api/dialogue/session | JSON `{ "avatar_id": "..." }` 创建绑定人物的会话 |
| POST /api/dialogue/turn | 按已有 session 驱动，无需重新传照片 |
| GET /api/workbench?avatar=... | 该人物的六种动作及生成历史 |
| POST /api/generate | JSON text、state、avatar_id；MiniMax TTS + MuseTalk |

会话固定人物 ID，主任务、分段子任务、GPU 请求都携带同一 ID。客户端不能给一个会话提交另一个人物 ID。切换人物创建新会话，旧会话和成片保留自己的身份。页面重新打开时从会话恢复人物；没有通过可变全局“当前人物”决定后台任务。

## GPU 与恢复

上传准备与对话共用 admission lock。准备任务进入现有持久队列，GPU worker 等待已提交的后处理结束，把 resident MuseTalk 模型卸载到 CPU，依次启动 motion/cache/validate 子进程，最后恢复 GPU 模型。三个阶段各自进程退出以释放显存。

取消时停止本次准备的 Windows 进程树，等待退出后恢复模型并释放锁，避免 venv 启动器退出而推理子进程仍占显存。每阶段有 20 分钟超时。服务重启会接管未结束的准备任务锁；已有 ready 人物无需重新准备。失败/取消可重新上传，生成新 ID，旧记录和日志保留。

## 保存与验证

改动前代码保存在 `.cache/releases/before-user-avatars-v1/`，包含 SHA-256 清单。之前接受的 8020/8021 基线保持不变。

验证记录：`user-avatars-browser.json` 保存真实浏览器播放观测；`user-avatars-verification.json` 保存端到端验收。`performance-verification.json` 对真实成片核对音视频同步、语音结束后原始动作帧恢复和口型变化。

测试用短发虚构成年人照片位于 `.cache/avatar-samples/auburn.png`，通过内置 image_gen 生成。提示词：photorealistic-natural；35-year-old fictional woman, short auburn bob, freckles, green eyes, dark teal crew-neck sweater, straight-on neutral closed lips, full head/shoulders/upper torso, even diffuse lighting, warm gray studio background, vertical 2:3, no text/occlusion/additional people。图片生成只用于测试素材；真实用户上传流程不依赖 image_gen。

进一步提高通用画质应优先加入多照片质量评测集、遮挡与清晰度评分、嘴部开合/牙齿稳定性检查、按检测质量缩小动作幅度。当前两张照片的验证不足以证明任意照片都达到相同画质。

## 本机实际验收结果

- 两张不同源照片通过相同上传 API 自动准备，分别耗时 240.0 秒、281.2 秒，没有人物专用修补。
- 两个自助人物的真实 MiniMax 分段对话都完成浏览器播放，首句开播 16.65 秒、15.17 秒；各播放两句。
- 两个人物共 12 组动作通过来源、缓存、帧数和循环连续性检查。
- 无脸图片经过真实检测拒绝；准备中取消至释放约 2.16 秒；Windows 准备子进程已退出。
- 取消后，短发人物再次通过工作台生成“你还好吗？今天辛苦了，慢慢来就好。”，全程 14.45 秒，输出 4.52 秒；证明模型恢复后仍可真实推理。
- 29 个 Python 测试通过；播放器状态机测试覆盖重复轮询、延迟播放、打断、部分重播、切换会话后的新人物待机路径。
- 已检查短发人物的实际说话帧；嘴部细节仍比原照片柔和。自动指标不能替代对自然度、牙齿细节和人物相似度的主观评审。

本版代码快照：`.cache/releases/user-avatars-v1-code/manifest.json`。该快照包含实现、页面与测试代码，不含密钥、模型权重或用户照片；运行依赖现有本地模型环境。
