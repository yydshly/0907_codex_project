"""Preserve the full local effect/architecture guide in the static publication."""
import json,re

def build(root,target,copy,repo):
 def write(name,text):
  (target/name).write_text(text,encoding='utf-8',newline='\n')
 mappings={
  'http://127.0.0.1:8022/jobs/9359a6b01a5f40279be3e015779147ac/result.mp4':'media/ruoan-body.mp4',
  'http://127.0.0.1:8022/jobs/e7a06c64995745aea2848f08a98a841f/result.mp4':'media/ruoan-face.mp4',
  'http://127.0.0.1:8022/avatars-media/371ea1eac99f4bdfa994b7f8796d5e69/assets/comfort/poster.jpg':'media/ruoan-body.jpg',
  'http://127.0.0.1:8022/avatars-media/8b119506a6dc48b5b4c74bf38204e940/assets/comfort/poster.jpg':'media/ruoan-face.jpg',
  'http://127.0.0.1:8020/complete/welcome/timing-v5/result.mp4':'media/welcome-result.mp4',
  'http://127.0.0.1:8020/source.png':'media/portrait.jpg',
  'http://127.0.0.1:8022/body-comparison.html':'body-comparison.html',
  'http://127.0.0.1:8022/characters':'characters.html',
  'http://127.0.0.1:8022/chat-classic':'chat.html',
  'http://127.0.0.1:8022/chat?avatar=371ea1eac99f4bdfa994b7f8796d5e69':'chat.html?avatar=ruoan',
  'http://127.0.0.1:8022/chat':'chat.html',
  'http://127.0.0.1:8022/?avatar=8b119506a6dc48b5b4c74bf38204e940':'experience.html',
  'http://127.0.0.1:8022/implementation-guide.html':'implementation-guide.html',
  'http://127.0.0.1:8022/':'experience.html',
  'http://127.0.0.1:8020/':'complete.html',
 }
 def portable(text):
  for old,new in mappings.items():text=text.replace(old,new)
  text=re.sub(r'http://127\.0\.0\.1:\d+[^"\s<]*','implementation-guide.html#reproduce',text)
  return text
 for name,folder in [('body','371ea1eac99f4bdfa994b7f8796d5e69'),('face','8b119506a6dc48b5b4c74bf38204e940')]:
  copy(root/'.cache/avatars'/folder/'assets/comfort/poster.jpg',f'media/ruoan-{name}.jpg')
 for name,key in [('body','9359a6b01a5f40279be3e015779147ac'),('face','e7a06c64995745aea2848f08a98a841f')]:
  copy(root/'.cache/performance-jobs'/key/'result.mp4',f'media/ruoan-{name}.mp4')
 # Full 8020 player: preserve all four comparison modes and matching idle clips.
 data=json.loads((root/'.cache/complete/active-release.json').read_text(encoding='utf-8'))
 for clip in data['clips']:
  for field,label in [('video','result'),('before_video','before'),('idle_video','idle'),('source_video','source')]:
   src=clip[field];relative=f'media/{clip["id"]}-{label}.mp4'
   copy(root/'.cache'/src.lstrip('/'),relative);clip[field]=relative
 data.update(idle='media/welcome-source.mp4',montage='media/performance-clips.mp4',baseline_url='complete.html')
 write('complete-data.json',json.dumps(data,ensure_ascii=False,indent=2))
 complete=(root/'demo/complete.html').read_text(encoding='utf-8')
 complete=re.sub(r'<nav>.*?</nav>','<nav><a href="./">效果与架构总览</a><a href="implementation-guide.html">完整实施指引</a><a href="body-comparison.html">人物效果对照</a></nav>',complete,count=1)
 complete=complete.replace('href="/"','href="./"').replace('/source.png','media/portrait.jpg').replace('/motion/listen-v2/result.mp4','media/welcome-source.mp4')
 write('complete.html',complete)
 write('complete-v5.js',(root/'demo/complete-v5.js').read_text(encoding='utf-8').replace("fetch('/api/complete')","fetch('complete-data.json')"))
 copy(root/'demo/complete.css','complete.css')
 compare=(root/'demo/body-comparison.html').read_text(encoding='utf-8')
 compare=re.sub(r'<header>.*?</header>','<header><a href="./">效果与架构总览</a><a href="implementation-guide.html">完整实施指引</a></header>',compare,count=1)
 compare=portable(compare).replace('href="/characters"','href="implementation-guide.html#reproduce"').replace('使用自然半身人物对话 ↗','本地对话使用说明 ↗')
 write('body-comparison.html',compare)
 js=(root/'demo/body-comparison.js').read_text(encoding='utf-8')
 js=js.replace("'/chat?avatar='+item.avatar_id","'implementation-guide.html#reproduce'").replace("fetch('/body-comparison.json')","fetch('body-comparison.json')").replace('或进入新人物对话','或阅读本地对话说明')
 write('body-comparison.js',js)
 comparison=json.loads((root/'demo/body-comparison.json').read_text(encoding='utf-8'))
 comparison['cases'][0].update(before='media/ruoan-face.mp4',after='media/ruoan-body.mp4')
 write('body-comparison.json',json.dumps(comparison,ensure_ascii=False,indent=2));copy(root/'demo/characters.css','characters.css')
 # Restore original effect tabs and the unabridged architecture/ownership content.
 full=(root/'demo/effects.html').read_text(encoding='utf-8')
 full=re.sub(r'<nav>.*?</nav>','<nav><a href="characters.html">人物选择页</a><a href="chat.html">人物对话页</a><a href="experience.html">六种动作回放</a><a href="#showcase">按效果浏览</a><a href="#architecture">完整架构</a><a href="implementation-guide.html">从零实施</a><a href="#recording-demo">网页录像</a></nav>',full,count=1)
 full=full.replace('href="effects.html"','href="./"')
 full=portable(full)
 full=full.replace('人物库 / 上传 / 选择 ↗','打开人物选择页 ↗').replace('进入人物对话 ↗','打开人物对话页（静态预览） ↗').replace('进入 8022 工作台 ↗','六种动作工作台回放 ↗')
 full=full.replace('历史页面需要对应本地服务运行；不代表每个旧版本都已达到当前质量。','公开版提供可播放样例；上传、新台词和自由对话需本地服务。历史版本链接提供实施说明，不代表该版本在线运行。')
 full=full.replace('href="implementation-guide.html#reproduce">查看动作与新台词工作台','href="experience.html">查看动作与新台词工作台')
 full=full.replace('href="implementation-guide.html#reproduce">用若安开始对话','href="experience.html">用若安开始对话')
 full=full.replace('<section id="showcase">','<section class="notice"><h2>人物对话与 8022 工作台</h2><p>补充两个人物的已保存回应与十二段动作，可切换人物、播放声音、选择动作和停止。完整上传与自由对话在本地运行。</p><a class="action" href="experience.html">进入六种动作与片段回放 ↗</a></section><section id="showcase">',1)
 full=full.replace('上传人物 ↗','本地上传说明 ↗').replace('管理 / 上传人物 ↗','本地人物管理说明 ↗').replace('用若安开始对话 ↗','本地对话说明 ↗').replace('查看动作与新台词工作台 ↗','动作与新台词使用说明 ↗')
 full=full.replace('<button data-view="camila" aria-pressed="true">Camila 写实角色</button>','<button data-view="camila" aria-pressed="false" disabled>Camila · 仅本地评估</button>')
 full=full.replace('<button data-view="mark" aria-pressed="false">','<button data-view="mark" aria-pressed="true">')
 full=full.replace('href="implementation-guide.html#reproduce" target="_blank" rel="noopener">独立打开 3D 体验','href="mark.html#lab" target="_blank" rel="noopener">独立打开 3D 体验')
 full=full.replace('在预览中点击播放并拖动旋转。','公开预览提供 Mark；Camila 说明保留，受资产许可限制仅在本地评估，不发布其模型或画面。在预览中点击播放并拖动旋转。')
 old=(root/'demo/public-index.html').read_text(encoding='utf-8')
 recording='<section id="demo">'+old.split('<section id="demo">',1)[1].split('</section>',1)[0]+'</section>'
 recording=recording.replace('id="demo"','id="recording-demo"')
 full=full.replace('<section id="showcase">',recording+'<section id="showcase">',1)
 full=full.replace('</head>','<style>.recording{background:#19251e;padding:10px;border-radius:14px}.recording video{display:block;width:100%;max-height:70vh}.record-actions{display:flex;gap:22px;flex-wrap:wrap}.source-note{color:var(--muted);font-size:12px;margin:15px 0 35px}</style></head>')
 full=full.replace('</main>','<section class="notice"><strong>静态与本地能力的区别：</strong>公开页保留效果预览、同音频对照、8020 全部回放模式、Mark 交互和完整原理。上传人物与新回复生成需要本地服务。<a href="'+repo+'notes/REVIEW-MAP.md">后续分析与复现索引 ↗</a> · <a href="'+repo+'notes/START-HERE.md">重读与维护手册 ↗</a> · <a href="THIRD_PARTY_NOTICES.md">来源说明 ↗</a></section></main>')
 write('index.html',full)
 js=(root/'demo/effects.js').read_text(encoding='utf-8')
 js=re.sub(r'const views=.*?;',"const views={mark:'mark.html#lab'};",js,count=1)
 js=js.replace("let currentView='camila'","let currentView='mark'")
 write('effects.js',js)
