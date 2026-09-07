'use strict';
const sampleBase='https://github.com/plugin87/ux-ui-agent-skills/blob/2ffb677aa02b225c8a3da1b7f31d9ebb7c38f1dd/examples/';
const examples=[
{name:'完整管理页面',path:'sample-app/preview.html',purpose:'把主题、统计卡片、表格、表单、开关和确认弹窗放进同一页面。',steps:['点击右上角 Dark，观察整页进入深色主题。','点击通知开关，查看 On / Off 状态变化。','点击 Export，观察短暂禁用和反馈文字。','点击 Delete account，输入 DELETE；试试 Cancel 或 Escape 返回。'],ability:'同一套 Token 驱动整页；危险操作使用对应视觉语义，确认弹窗管理焦点和输入状态。',limit:'统计与表格数据是静态样例。Export 仅模拟状态，不下载文件或发送邮件；Delete account 仅关闭弹窗，不删除任何真实数据。'},
{name:'品牌与主题',path:'brandkit-demo/index.html',purpose:'用一个小界面观察颜色、按钮和输入框如何保持统一。',steps:['点击 Toggle theme 切换明暗主题。','输入 Account name，观察输入框焦点。','对比 Primary、Secondary 和 Delete 的视觉区别。'],ability:'语义 Token 统一背景、文本和操作角色。切换主题改变共享映射，而非逐个改组件。',limit:'三个操作按钮是视觉示意，不执行业务动作。主题演示不意味着任意自定义品牌配色已经通过检查。'},
{name:'按钮状态',path:'component-states/button.html',purpose:'把同一个按钮的不同变体和状态并排呈现，直观看清组件规范的产物。',steps:['对比普通、禁用和 Saving 加载状态。','鼠标悬停在 Save changes；用 Tab 查看焦点。','对比主要、次要和危险操作的样式。'],ability:'设计组件时覆盖适用状态，而不只画一个默认按钮；加载态明确显示忙碌并阻止重复操作。',limit:'这是状态样板。Bold 的选中与未选中是固定展示，不会点击切换；Saving 不会完成保存。'},
{name:'表单控件',path:'component-states/form-controls.html',purpose:'体验复选框、半选、单选和开关的真实原生行为。',steps:['勾选或取消 Email / SMS notifications。','观察 Partial selection 的初始半选效果。','选择 Daily digest 或 Weekly，观察单选互斥。','点击开关；用 Tab 和空格重复操作。'],ability:'复选、半选、禁用和互斥状态有明确表达；使用原生输入行为兼顾键盘操作。',limit:'开关只改变自己的状态。Dark mode (on) 文案是原始静态标签，不会切换整页主题，也不会随点击更新文字。'},
{name:'可操作数据表',path:'component-states/data-table.html',purpose:'检查一个看起来可排序、可选择的表格，是否真的兑现交互。',steps:['点击 Name，观察三行数据顺序反转。','点击 Role，按角色重新排序。','点击表头复选框，全选或取消所有行。','仅选择一行，观察表头恢复半选状态。'],ability:'排序不仅改变箭头，也改变数据行顺序；全选与半选状态联动，体现可验证的组件行为。',limit:'只有三行本地示例数据。没有服务端分页、筛选请求或批量业务操作；排序正确不代表完整数据产品已完成。'},
{name:'确认弹窗',path:'component-states/modal.html',purpose:'把焦点约束、取消和恢复焦点这些不易从截图看出的能力展示出来。',steps:['点击 Delete account 打开弹窗。','连续按 Tab，观察焦点停留在弹窗按钮中。','按 Escape 关闭，焦点回到原按钮。','再次打开，点击 Cancel 关闭。'],ability:'明确的危险操作、弹窗语义、焦点约束、Escape 与关闭后恢复焦点构成完整交互模式。',limit:'这个简化示例不要求输入确认词；确认按钮只关闭弹窗。带输入确认的版本见“完整管理页面”。'}
];
let active=0;
const mappings=[
[['design-tokens','统一主题'],['design-component','组件与适用状态'],['design-code','页面实现'],['a11y-audit','确认与焦点行为']],
[['brandkit','品牌基础'],['design-tokens','语义映射'],['token-build','已有主题样式产物']],
[['design-component','按钮变体与状态'],['design-code','样式实现']],
[['design-component','选择与禁用状态'],['a11y-audit','原生语义与键盘操作']],
[['design-component','表格选择与排序规范'],['design-code','行顺序实际变化'],['design-qa','可检查的行为']],
[['design-component','弹窗交互规范'],['design-code','弹窗实现'],['a11y-audit','焦点约束与恢复']]
];
function renderMapping(index){const el=document.querySelector('#skill-mapping');el.innerHTML='<h3>当前案例 → 对应 Skill 要求 → 可观察效果</h3><p>'+mappings[index].map(([id,meaning])=>`<a href="${sampleBase.replace('examples/','')}.claude/skills/${id}/SKILL.md">${id}</a>：${meaning}`).join('； ')+'</p><p class="caption">对应规则的效果展示，不是现场运行上述 Skill；也没有证明不用 Skill 就做不到。</p>';}
const frame=document.querySelector('#demo-frame');
const buttons=document.querySelector('#examples');
function show(index){active=index;const s=examples[index];document.querySelector('#sample-number').textContent=`EXAMPLE 0${index+1} / 06`;document.querySelector('#sample-title').textContent=s.name;document.querySelector('#sample-purpose').textContent=s.purpose;document.querySelector('#sample-ability').textContent=s.ability;document.querySelector('#sample-boundary').textContent=s.limit;const steps=document.querySelector('#sample-steps');steps.replaceChildren();for(const text of s.steps){const li=document.createElement('li');li.textContent=text;steps.append(li);}document.querySelector('#source-example').href=sampleBase+s.path;document.querySelector('#open-sample').href='samples/'+s.path;frame.title='上游原始示例：'+s.name;frame.src='samples/'+s.path;[...buttons.children].forEach((b,i)=>b.setAttribute('aria-pressed',String(i===index)));}
examples.forEach((sample,index)=>{const b=document.createElement('button');b.type='button';b.innerHTML=`<span>0${index+1}</span>${sample.name}`;b.addEventListener('click',()=>{show(index);renderMapping(index);});buttons.append(b);});
document.querySelector('#phone').addEventListener('click',event=>{const enabled=event.currentTarget.getAttribute('aria-pressed')!=='true';event.currentTarget.setAttribute('aria-pressed',String(enabled));event.currentTarget.textContent=enabled?'恢复自适应':'窄屏预览';document.querySelector('.frame-stage').classList.toggle('phone',enabled);});
document.querySelector('#reload').addEventListener('click',()=>show(active));
const requested=Number(new URLSearchParams(location.search).get('sample')||0);
const initial=Number.isInteger(requested)&&requested>=0&&requested<examples.length?requested:0;
show(initial);renderMapping(initial);
