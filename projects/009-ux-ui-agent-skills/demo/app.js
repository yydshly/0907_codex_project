'use strict';
const base = 'https://github.com/plugin87/ux-ui-agent-skills/blob/2ffb677aa02b225c8a3da1b7f31d9ebb7c38f1dd/';
const skills = [
  ['brandkit','品牌基础','品牌与主题','从品牌简报建立统一的视觉基础。','分层 Token、明暗主题与共享 CSS。','需要品牌目标；主题仍需对实际页面验证。'],
  ['design-tokens','设计 Token','品牌与主题','统一颜色、字体、间距、圆角和动效。','可维护的原始、语义与组件 Token。','引用正确不代表所有实际颜色配对合格。'],
  ['apply-aesthetic','应用视觉风格','品牌与主题','按参考风格调整界面的设计语言。','配色、排版、层次与布局方向。','138 份参考不是官方组件库；审美规则需按场景选择。'],
  ['design-component','组件设计','组件与实现','明确组件结构、变体和适用状态。','结构、状态表、Token 映射与无障碍要求。','8 类状态按适用性选择；组件规范需转为具体实现。'],
  ['design-code','界面代码生成','组件与实现','根据框架协议，将设计要求转成代码。','目标框架组件、样式与主题映射。','依赖模型、框架版本和项目约定，不是通用编译器。'],
  ['image-to-code','截图转代码','组件与实现','从截图提炼布局、配色和排版规则。','推导的主题与重建界面。','不保证像素级还原，也不自带新的视觉模型。'],
  ['token-build','Token 构建','组件与实现','把统一设计数据映射到平台样式。','CSS 等产物，以及多平台构建指导。','应按具体脚本与输出目标核对实际支持范围。'],
  ['redesign','已有界面改版','研究与改进','先审查问题，再按优先级调整界面。','改造方案、修改实现与复查。','需要已有页面和业务行为依据，避免改坏原流程。'],
  ['prototype','原型与流程','研究与改进','选择保真度，组织流程和测试计划。','原型、用户路径与可用性测试计划。','计划不等于已经完成用户测试。'],
  ['ux-writing','界面文案','研究与改进','完善按钮、错误、提示与空状态文字。','明确、一致的界面文案和语气规范。','需要补充中文表达、业务词汇与本地化规则。'],
  ['design-review','设计评审','质量与治理','按维度检查设计并整理问题优先级。','评审意见、问题依据与修复建议。','模型评分不能替代业务效果和客观测量。'],
  ['a11y-audit','无障碍审查','质量与治理','检查颜色、语义、焦点和操作方式。','无障碍问题清单与具体修复建议。','自动检查覆盖有限，无法独立证明全面合规。'],
  ['design-qa','质量保障','质量与治理','为持续迭代组织自动检查与回归流程。','CI 方案、检查入口和回归指导。','必须绑定产品实际页面，不能只跑上游示例。'],
  ['performance','性能改进','质量与治理','围绕加载、布局偏移和动画成本改进。','性能检查与优化指导。','指标需真实测量，文档本身不提供效果保证。'],
  ['governance','设计系统治理','质量与治理','规定系统如何贡献、升级和弃用。','版本策略与团队维护流程。','需要团队采用和持续执行。'],
  ['migrate-design-system','设计系统迁移','系统协作','将源系统的语义映射到目标系统。','角色对照、Token 映射与迁移指导。','映射完整性和业务兼容仍需逐项验证。'],
  ['figma-integration','Figma 协作','系统协作','组织 Variables、Token 与代码组件对应。','同步方向、变量映射与组件一致性流程。','依赖外部工具和连接，不是内置完整同步服务。']
];
const categories = ['全部','品牌与主题','组件与实现','研究与改进','质量与治理','系统协作'];
let category = '全部';
const grid = document.querySelector('#skills');
const search = document.querySelector('#search');
const filterBox = document.querySelector('#filters');
for (const name of categories) {
  const button = document.createElement('button');
  button.type = 'button'; button.textContent = name; button.setAttribute('aria-pressed', String(name === category));
  button.addEventListener('click', () => {category = name; for (const b of filterBox.children) b.setAttribute('aria-pressed', String(b === button)); renderSkills();});
  filterBox.append(button);
}
function renderSkills() {
  const query = search.value.trim().toLocaleLowerCase();
  const matches = skills.filter(s => (category === '全部' || s[2] === category) && s.join(' ').toLocaleLowerCase().includes(query));
  grid.replaceChildren();
  for (const [id,title,group,description,output,limit] of matches) {
    const card = document.createElement('details');card.className = 'skill';
    // All inserted fields are the static research catalogue, never search input.
    card.innerHTML = `<summary><span class="category">${group}</span><h3>${title}</h3><code>${id}</code><span class="expand" aria-hidden="true">＋</span><p>${description}</p></summary><div class="skill-body"><p><b>预期产物</b>${output}</p><p><b>使用边界</b>${limit}</p><a href="${base}.claude/skills/${id}/SKILL.md">查看固定版本技能定义 ↗</a></div>`;
    grid.append(card);
  }
  document.querySelector('#result-count').textContent = `显示 ${matches.length} / 17 项技能 · ${category}`;
  document.querySelector('#empty').hidden = matches.length !== 0;
}
search.addEventListener('input', renderSkills);
document.querySelector('#reset').addEventListener('click', () => {search.value = ''; category = '全部'; for(const b of filterBox.children) b.setAttribute('aria-pressed', String(b.textContent === '全部'));renderSkills();});
renderSkills();
const themes = {light:'#17624e', dark:'#a4d4b6', clay:'#984529'};
document.querySelectorAll('[data-theme]').forEach(button => {
  button.addEventListener('click', () => {
    document.querySelector('#token-preview').dataset.theme = button.dataset.theme;
    document.querySelector('#raw-value').textContent = themes[button.dataset.theme];
    document.querySelectorAll('.theme-controls button').forEach(b => b.setAttribute('aria-pressed',String(b === button)));
  });
});
let checklist = false;
document.querySelector('#sample-button').addEventListener('click', event => {
  checklist = !checklist;
  event.currentTarget.textContent = checklist ? '收起交付清单' : '查看交付清单';
  event.currentTarget.setAttribute('aria-expanded', String(checklist));
  document.querySelector('#sample-feedback').textContent = checklist ? '检查项：主题一致、交互可用、实际页面验证。此处仅展示清单，未运行检查。' : '点击按钮，查看此示例的检查项。';
});
document.querySelector('#sample-button').setAttribute('aria-expanded','false');
document.querySelector('#sample-button').setAttribute('aria-controls','sample-feedback');
const scenarios = [
  ['新产品原型','先建立基础，再生成页面。','适合需要快速探索产品形态、同时保持页面一致性的任务。',['品牌简报','brandkit','design-component','design-code','实际页面检查'],'统一主题、组件及对应页面。','真实内容、业务优先级、交互验收标准。'],
  ['后台与 SaaS','把状态完整性带进复杂界面。','适合表格、筛选、表单、弹窗和多状态管理页面。',['组件规范','design-code','ux-writing','a11y-audit'],'组件变体、适用状态、错误与空状态表达。','权限、排序、批量操作、数据保存和失败恢复。'],
  ['已有页面改版','从问题出发，控制改造范围。','适合保留已有业务流程，同时改善视觉与体验。',['redesign','design-review','主题与组件调整','回归检查'],'按优先级组织的问题清单和界面修改。','原有行为依据、兼容要求和关键路径测试。'],
  ['多品牌与主题','共享组件，集中调整语义映射。','适合多品牌、明暗模式和长期维护的产品。',['design-tokens','语义映射','token-build','全状态验证'],'可维护的主题数据和平台样式映射。','各品牌约束，以及每种主题下的真实页面检查。'],
  ['设计协作','给设计与代码建立对应关系。','适合设计系统交接、组件治理与迁移任务。',['figma-integration','migrate-design-system','governance'],'Variables 与代码映射、迁移和维护约定。','外部工具连接、唯一数据源和同步实现。']
];
const scenarioBox = document.querySelector('#scenario-buttons');
function showScenario(index) {
  const [label,title,description,flow,output,need] = scenarios[index];
  document.querySelector('#scenario-detail').innerHTML = `<span class="overline">${label} / 场景建议</span><h3>${title}</h3><p>${description}</p><div class="flow">${flow.map(x=>`<span>${x}</span>`).join('<span aria-hidden="true">→</span>')}</div><p><b>可以得到：</b>${output}</p><p class="need"><b>我们还需补充：</b>${need}</p>`;
  [...scenarioBox.children].forEach((b,i)=>b.setAttribute('aria-pressed',String(i===index)));
}
scenarios.forEach((scenario,index)=>{const b=document.createElement('button');b.type='button';b.innerHTML=`${scenario[0]} <span aria-hidden="true">↗</span>`;b.addEventListener('click',()=>showScenario(index));scenarioBox.append(b);});
showScenario(0);
const sources = [['入口与路由','CLAUDE.md'],['框架适配协议','frameworks/adapter-protocol.md'],['总检查目标','scripts/accuracy_report.mjs'],['浏览器检查','scripts/measure_render.mjs'],['作者评测记录','evals/RESULTS.md'],['Figma 流程','workflows/figma-integration.md'],['版本与许可声明','package.json'],['项目说明','README.md']];
for(const [label,path] of sources){const a=document.createElement('a');a.href=base+path;a.textContent=label+' ↗';document.querySelector('#source-links').append(a);}
const navLinks=[...document.querySelectorAll('.sidebar nav a')];
const sections=[...document.querySelectorAll('main section[id]')];
let navFramePending=false;
function updateNavigation(){
  const boundary=innerWidth<=700?165:150;
  let current=sections[0];
  for(const section of sections){if(section.getBoundingClientRect().top<=boundary)current=section;}
  navLinks.forEach(a=>{if(a.hash==='#'+current.id)a.setAttribute('aria-current','location');else a.removeAttribute('aria-current');});
  navFramePending=false;
}
function scheduleNavigation(){if(!navFramePending){navFramePending=true;requestAnimationFrame(updateNavigation);}}
window.addEventListener('scroll',scheduleNavigation,{passive:true});
window.addEventListener('resize',scheduleNavigation);
updateNavigation();
