const products={chat:'Claude 对话',cowork:'Cowork',code:'Claude Code',api:'API / Platform',chrome:'Chrome',design:'Design',excel:'Excel',powerpoint:'PowerPoint',security:'Security',tag:'Claude Tag'};
const kinds={all:'全部',course:'课程',tutorial:'教程','use-case':'使用案例'};
const routes=[
 {name:'刚开始接触 AI',title:'建立基础，再做一个真实任务',desc:'适合初学者。先熟悉对话，再练习协作方法，最后理解 AI 的能力边界。',practice:'练习：让 AI 帮你整理一份资料，自己核查三个关键事实，并修改最终版本。',steps:['claude-101','ai-fluency-framework-foundations','ai-capabilities-and-limitations']},
 {name:'提高日常工作效率',title:'从对话，走向可复用的工作流',desc:'适合需要处理资料、文档和多步骤任务的人。学会提供上下文，再将重复做法沉淀为技能。',practice:'练习：把每周资料整理流程写成“输入 → 处理步骤 → 验收要求”，用一次真实任务检验。',steps:['claude-101','introduction-to-claude-cowork','introduction-to-agent-skills']},
 {name:'用 AI 编程',title:'让编程协作更有章法',desc:'适合有编程基础的人。先掌握核心工作流，再学习长任务的引导、自动化和任务拆分。',practice:'练习：选择一个小功能，先说明验收标准，再完成实现、测试与人工检查。',steps:['claude-code-101','claude-code-in-action','introduction-to-agent-skills','introduction-to-subagents']},
 {name:'开发 AI 应用',title:'从平台基础，到工具连接',desc:'适合开发者。建立平台概念，学习 API 应用模式，再探索 MCP 的连接能力。',practice:'练习：做一个能检索资料并给出来源的问答原型，用固定问题检查结果。',steps:['claude-platform-101','building-with-the-claude-api','introduction-to-model-context-protocol','model-context-protocol-advanced-topics']},
 {name:'教学与学习',title:'把 AI 协作带入学习过程',desc:'适合教师和教育设计者。用共同框架讨论 AI 的使用方式，再设计教学活动。学生可在资源库搜索“学生”。',practice:'练习：设计一项允许 AI 辅助的作业，明确学生必须独立完成的部分与引用要求。',steps:['ai-fluency-framework-foundations','ai-fluency-for-educators','teaching-ai-fluency']}
];
const $=s=>document.querySelector(s),key='claude-academy-014-done-v1';let completed=new Set(),kind='all',limit=24;
try{const saved=JSON.parse(localStorage.getItem(key)||'[]');if(Array.isArray(saved))completed=new Set(saved.filter(id=>RESOURCES.some(r=>r.id===id)));}catch{ $('#storage-note').textContent='当前浏览器无法读取本地记录；仍可浏览资源并在本次打开期间标记完成。'; }
function el(tag,text,cls){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;}
function link(text,url){const a=el('a',text);a.href=url;a.target='_blank';a.rel='noopener noreferrer';return a;}
function updateProgress(){ $('#progress-text').textContent=`已完成 ${completed.size} / ${RESOURCES.length}`;$('#progress').value=completed.size; }
function setRoute(i){const r=routes[i];$('#route-title').textContent=r.title;$('#route-desc').textContent=r.desc;$('#route-practice').textContent=r.practice;$('#route-steps').replaceChildren(...r.steps.map(id=>{const resource=RESOURCES.find(x=>x.id===id),li=el('li');li.append(link(resource.title,resource.url),el('span','↗'));return li;}));[...$('#route-tabs').children].forEach((b,j)=>b.setAttribute('aria-pressed',String(i===j)));}
routes.forEach((r,i)=>{const b=el('button',r.name);b.type='button';b.onclick=()=>setRoute(i);$('#route-tabs').append(b);});setRoute(0);
Object.entries(products).forEach(([value,label])=>{const option=el('option',label);option.value=value;$('#product').append(option);});
Object.entries(kinds).forEach(([value,label])=>{const b=el('button',`${label} ${value==='all'?RESOURCES.length:RESOURCES.filter(r=>r.kind===value).length}`);b.type='button';b.dataset.kind=value;b.onclick=()=>{kind=value;limit=24;render();};$('#kind-tabs').append(b);});
function render(){
 const query=$('#search').value.trim().toLocaleLowerCase(),product=$('#product').value,status=$('#status').value;
 const rows=RESOURCES.filter(r=>(kind==='all'||r.kind===kind)&&(product==='all'||r.products.includes(product))&&(status==='all'||completed.has(r.id)===(status==='done'))&&(!query||[r.title,r.enTitle,r.summary,...r.tags,...r.products.map(p=>products[p])].join(' ').toLocaleLowerCase().includes(query)));
 $('#result-count').textContent=`找到 ${rows.length} 项 · 已显示 ${Math.min(limit,rows.length)} 项`;
 [...$('#kind-tabs').children].forEach(b=>b.setAttribute('aria-pressed',String(kind===b.dataset.kind)));
 $('#cards').replaceChildren(...rows.slice(0,limit).map(r=>{
  const card=el('article',undefined,'card'),top=el('div',undefined,'card-top');top.append(el('span',kinds[r.kind],'card-kind'),el('span',r.products.map(p=>products[p]||p).join(' · ')));
  const title=el('h3');title.append(link(r.title,r.url));card.append(top,title,el('p',r.summary));
  if(r.editorialTranslation)card.append(el('span','本站译名 · 官方英文资源','translated'));
  const bottom=el('div',undefined,'card-bottom'),button=el('button',completed.has(r.id)?'✓ 已完成':'○ 标记完成','done');button.type='button';button.setAttribute('aria-pressed',String(completed.has(r.id)));button.setAttribute('aria-label',`${r.title}：${completed.has(r.id)?'取消完成':'标记完成'}`);
  button.onclick=()=>{const oldScroll=window.scrollY;completed.has(r.id)?completed.delete(r.id):completed.add(r.id);try{localStorage.setItem(key,JSON.stringify([...completed]));}catch{$('#storage-note').textContent='当前浏览器无法保存记录，完成标记仅在本次打开期间有效。';}render();const next=[...document.querySelectorAll('.done')].find(b=>b.dataset.id===r.id);if(next)next.focus({preventScroll:true});window.scrollTo({top:oldScroll,behavior:'instant'});};button.dataset.id=r.id;
  bottom.append(link('前往学习 ↗',r.url),button);card.append(bottom);return card;
 }));$('#empty').hidden=rows.length>0;$('#more').hidden=rows.length<=limit;updateProgress();
}
$('#search').addEventListener('input',()=>{limit=24;render();});for(const id of ['#product','#status'])$(id).addEventListener('change',()=>{limit=24;render();});
$('#reset').onclick=()=>{$('#search').value='';$('#product').value='all';$('#status').value='all';kind='all';limit=24;render();$('#search').focus();};
$('#more').onclick=()=>{limit+=24;render();};render();
