from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from html import escape

OUT=Path(__file__).resolve().parent
W,H=1600,1200
im=Image.new('RGB',(W,H),'#f3f6f8'); d=ImageDraw.Draw(im)
svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc"><title id="title">Effective HTML：从场景生成到能力沉淀</title><desc id="desc">场景与资料输入技能规则，模型生成代码，浏览器运行检查，交付 HTML 成果；我们提取场景、输入、生成规则和验收标准，复用到架构图、流程图与 UML 等任务。</desc><rect width="1600" height="1200" fill="#f3f6f8"/>']
INK='#183747'; MUTED='#506977'; LINE='#c4d3dc'; TEAL='#126777'
def box(x,y,w,h,fill='#ffffff',stroke=LINE,r=14):
    d.rounded_rectangle((x,y,x+w,y+h),radius=r,fill=fill,outline=stroke,width=2)
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
def text(x,y,s,size=24,fill=INK,bold=False):
    font=ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc' if bold else 'C:/Windows/Fonts/msyh.ttc',size)
    d.text((x,y),s,font=font,fill=fill,anchor='lt')
    svg.append(f'<text x="{x}" y="{y+size*.9}" font-family="Microsoft YaHei, Noto Sans CJK SC, sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{fill}">{escape(s)}</text>')
def arrow(x1,y1,x2,y2,color=TEAL):
    d.line((x1,y1,x2,y2),fill=color,width=3)
    if y1==y2: pts=[(x2,y2),(x2-10,y2-6),(x2-10,y2+6)]
    else: pts=[(x2,y2),(x2-6,y2-10),(x2+6,y2-10)]
    d.polygon(pts,fill=color)
    svg.append(f'<path d="M{x1} {y1}L{x2} {y2}" fill="none" stroke="{color}" stroke-width="3"/><polygon points="'+ ' '.join(f'{x},{y}' for x,y in pts)+f'" fill="{color}"/>')

text(60,40,'Effective HTML',48,bold=True)
text(60,105,'把特定场景下的 HTML 制作方法，整理成 AI 可复用的技能。',28)
text(60,154,'宏观理解  /  技能提供方法 · 模型完成生成 · 浏览器承载成果',21,MUTED)

box(60,230,270,290)
text(85,255,'场景与输入',28,bold=True)
for i,s in enumerate(['谁使用、要解决什么','原始内容与权威来源','已有设计与业务约束','需要审阅的关键问题']):text(85,315+i*43,s,21)
arrow(332,375,367,375)

box(370,215,750,340,'#e6f0f3','#9bbbc6')
text(397,240,'Effective HTML · 六个技能入口',28,bold=True)
box(397,291,333,83)
text(414,303,'html · 综合与分流',23,bold=True)
text(414,337,'先选适合问题的成果形式',19,MUTED)
box(748,291,344,83)
text(765,303,'design-artifact · 设计方法',22,bold=True)
text(765,337,'配色、字体、布局服从主题',19,MUTED)
for x,title,sub in [(397,'线框','结构与导航'),(574,'原型','流程与状态'),(751,'计划','承诺与依赖'),(928,'图解','关系与时序')]:
    box(x,397,163,83)
    text(x+18,409,title,25,bold=True);text(x+18,446,sub,20,MUTED)
text(397,509,'共同要求：内容忠实 · 表达清楚 · 范围明确 · 结果可检查',21)
arrow(1124,375,1158,375)

box(1160,230,380,290)
text(1185,255,'执行与检查',28,bold=True)
text(1185,309,'大模型',25,bold=True)
text(1185,346,'理解材料，生成 HTML / CSS / JS',19)
text(1185,401,'浏览器与评审',25,bold=True)
text(1185,438,'运行、检查布局与交互，反馈修改',19)
arrow(1350,523,1350,589)

box(60,595,1480,130,'#183e50','#183e50')
text(86,617,'HTML 成果',30,'#ffffff',True)
text(320,618,'报告与工具  /  视觉专题  /  线框与原型  /  计划  /  架构与流程图',27,'#ffffff')
text(86,671,'单文件交付为默认目标；具体布局按任务设计。规则不等于自动质量保证，效果仍依赖模型、资料与验证。',21,'#d0e1e9')

text(60,771,'对我们的意义：复用制作方法，沉淀自己的场景能力。',31,bold=True)
box(60,834,700,206)
text(85,858,'值得提取',27,bold=True)
text(85,906,'场景与目标  →  输入要求  →  生成规则  →  验收标准',23)
text(85,954,'把反复纠正的问题写成明确要求，',23,MUTED)
text(85,991,'在真实任务中验证后，再纳入可复用能力。',23,MUTED)
box(792,834,748,206)
text(817,858,'参考与扩展方向',27,bold=True)
text(817,906,'架构图：职责、边界、连接、依据',23)
text(817,947,'流程图：起止、判断、异常、回路',23)
text(817,988,'UML：图种与符号语义；严格校验需另行补充',23)

text(60,1074,'采用判断：按需参考、去重适配、实测后沉淀。输出可选 HTML，也可按维护需求选 Mermaid / PlantUML / SVG。',22,bold=True)
text(60,1127,'本研究原创概念图，非官方架构或效果排名。上游版本 d95debbaef15 · 2026-09-07',19,MUTED)
svg.append('</svg>')
(OUT/'effective-html-overview.svg').write_text('\n'.join(svg),encoding='utf8')
im.save(OUT/'effective-html-overview.png')
print('Saved macro overview PNG and SVG.')
