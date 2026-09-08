"""Render the review map from its single Markdown source (requires markdown)."""
from pathlib import Path
import re
import markdown

ROOT=Path(__file__).resolve().parents[1]
REPO='https://github.com/yydshly/0907_codex_project/blob/main/projects/015-audio2face-3d/'

def build(document='REVIEW-MAP.md', output='review.html'):
 source=(ROOT/'notes'/document).read_text(encoding='utf-8')
 source=source.replace('http://127.0.0.1:8022','127.0.0.1:8022')
 source=re.sub(r'\]\(\.\./([^)]*)\)',lambda m:']('+REPO+m[1]+')',source)
 source=re.sub(r'\]\(([^):]+\.md(?:#[^)]*)?|revisit-inventory\.json)\)',lambda m:']('+REPO+'notes/'+m[1]+')',source)
 # Native HTML flow remains readable offline; no diagram CDN is required.
 flow='''<div class="flow" aria-label="首次准备与每轮对话流程"><article><h3>首次准备 · 可复用</h3><p>上传照片，选择动作来源</p><b>↓</b><p>LivePortrait 本地面部<br>或 Hailuo 远端半身（视频额度）</p><b>↓</b><p>本地检测框、蒙版、VAE 缓存</p><b>↓</b><p>保存人物动作包 → 供多轮口型生成复用</p></article><article><h3>每轮对话 · 按新音频生成</h3><p>用户输入消息</p><b>↓</b><p>MiniMax 对话 → TTS（远端额度）</p><b>↓</b><p>已有动作包 + 新音频 → 本地 MuseTalk</p><b>↓</b><p>稳定、句尾处理、编码 → 分段播放</p></article></div>'''
 source=re.sub(r'```mermaid.*?```',flow,source,flags=re.S)
 body=markdown.markdown(source,extensions=['tables','fenced_code'])
 toc=[]
 def heading(m):
  key='section-'+str(len(toc)+1);toc.append((key,m[1]));return f'<h2 id="{key}">{m[1]}</h2>'
 body=re.sub(r'<h2>(.*?)</h2>',heading,body)
 body=body.replace('<table>','<div class="table-scroll" tabindex="0" role="region" aria-label="可横向滚动的索引表"><table>').replace('</table>','</table></div>')
 nav=''.join(f'<a href="#{key}">{title}</a>' for key,title in toc)
 html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>后续分析与复现 · 数字人物实验室</title><link rel="icon" href="data:,"><link rel="stylesheet" href="effects.css"><style>
 .review{max-width:1150px;line-height:1.85}.review h1{font-size:clamp(27px,4vw,44px)}.review h2{margin-top:55px;scroll-margin-top:24px}.review a{text-decoration:underline}.review code{overflow-wrap:anywhere;font-size:.9em}.review li{margin:10px 0}.table-scroll{overflow:auto;border:1px solid #ccd5ca;border-radius:12px;margin:20px 0}table{width:100%;border-collapse:collapse;min-width:680px}td,th{text-align:left;padding:14px;vertical-align:top;border-bottom:1px solid #ccd5ca}th{background:#e6eddf}.flow{display:grid;grid-template-columns:1fr 1fr;gap:18px}.flow article{border:1px solid #a7bba2;border-radius:16px;text-align:center;padding:20px;background:#edf2e8}.flow p{background:white;border-radius:8px;padding:12px}.review-nav{display:flex;flex-wrap:wrap;gap:12px;padding:20px;background:#e6eddf;border-radius:12px}.review-nav a{padding:6px}header{height:auto;min-height:76px;gap:15px;flex-wrap:wrap}header nav{flex-wrap:wrap}@media(max-width:640px){.flow{grid-template-columns:1fr}.review{padding:0 16px}td,th{padding:10px}}
 </style></head><body><header><a class="brand" href="effects.html">数字人物实验室</a><nav><a href="effects.html">效果首页</a><a href="implementation-guide.html">完整架构与实施</a></nav></header><main class="review"><p class="eyebrow">REVISIT / RESTORE / VERIFY</p><nav class="review-nav" aria-label="本文目录">'''+nav+'</nav>'+body+'<p>本文从 <a href="'+REPO+'notes/REVIEW-MAP.md">版本化原文</a> 自动构建，修改原文后重新发布，避免网页与文档脱节。</p></main></body></html>'
 html=html.replace('notes/REVIEW-MAP.md">版本化原文','notes/'+document+'">版本化原文')
 html=html.replace('<a href="implementation-guide.html">','<a href="directories.html">目录与重新下载</a><a href="review.html">后续分析</a><a href="implementation-guide.html">',1)
 if output=='directories.html':html=html.replace('<title>后续分析与复现','<title>目录与重新下载指南')
 (ROOT/'demo'/output).write_text(html,encoding='utf-8',newline='\n')
 return html

if __name__=='__main__':build()
