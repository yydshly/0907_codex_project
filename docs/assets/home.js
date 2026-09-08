const search=document.querySelector('#search');
const cards=[...document.querySelectorAll('.project')];
const buttons=[...document.querySelectorAll('[data-filter]')];
let active='all';
function filterProjects(){
 const query=search.value.trim().toLocaleLowerCase();let count=0;
 for(const card of cards){const match=(active==='all'||(active==='web'?card.dataset.web==='true':card.dataset.category===active))&&(!query||`${card.textContent} ${card.dataset.keywords}`.toLocaleLowerCase().includes(query));card.hidden=!match;if(match)count++;}
 document.querySelector('#count').textContent=`显示 ${count} / ${cards.length} 个项目`;
 document.querySelector('#empty').hidden=count!==0;
 for(const button of buttons)button.setAttribute('aria-pressed',String(button.dataset.filter===active));
}
for(const item of document.querySelectorAll('.progressive'))item.hidden=false;
search.addEventListener('input',filterProjects);
for(const button of buttons)button.addEventListener('click',()=>{active=button.dataset.filter;filterProjects();});
document.querySelector('#reset').addEventListener('click',()=>{active='all';search.value='';filterProjects();search.focus();});
filterProjects();
