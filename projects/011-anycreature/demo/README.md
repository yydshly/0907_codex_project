# 生物制造实验室

无 CDN、无在线大模型调用，模型与展示依赖本地保存；通过 HTTP 静态服务器打开。

## 重新生成

在研究仓库根目录执行（已验证 Node.js v22.15.0 / Windows）：

```powershell
git clone https://github.com/Ariescar/anyCreature.git upstream/anyCreature
git -C upstream/anyCreature checkout ab5b1ce5c13e632f00f7f7cbfdb7a746e315000d
node projects/011-anycreature/demo/build.cjs upstream/anyCreature
```

脚本读取上游狼 JSON 生成九份变体，并调用独立蜗牛、蝴蝶和人形构建器各生成三档体型，共 18 份模型。原版 CLI 检查失败则停止；成功后同步到 `docs/demos/011-anycreature/`。完整上游源码独立保存。

只修改页面时，复制 `index.html`、`style.css`、`app.js` 到发布目录即可。

## 查看

使用静态服务器服务 `docs/`。例如已安装 Python 时：

```powershell
python -m http.server 5191 --bind 127.0.0.1 --directory docs
```

打开 [本地演示](http://127.0.0.1:5191/demos/011-anycreature/)。本次实际预览使用 Node.js 静态服务器。

## 结构

- `build.cjs`：参数变体、编译、统计和静态同步。
- `assets/*.json`：角色描述；`catalog.json` 为说明与统计。
- `assets/*.glb`：实际编译成果，内含蒙皮和动画。
- `app.js`：加载、动画、视角和显示模式。

新蜗牛是独立创作；另外三个外观是官方狼的衍生版本。页面没有即时文本生成能力。

独立生成蜗牛：`node projects/011-anycreature/demo/create-snail.cjs upstream/anyCreature 0`，末尾体型参数为 0、1 或 2。独立生成蝴蝶三档：`node projects/011-anycreature/demo/create-butterfly.cjs upstream/anyCreature`。完整构建会调用两者；它们均从空白对象定义关节、体积、部件与动画，不读取官方样例。

人形独立重建：`node projects/011-anycreature/demo/create-human.cjs upstream/anyCreature`。实际效果图渲染入口为 `capture.html`；截图保存在子项目 assets/，完整构建会复制到发布目录。
