/* Categorized, press-hold-slide-release template picker shared by Mac and web. */
window.ErezTemplatePicker=function(button,load,choose){
 let root=null,groups=[],active=0,opening=0,loading=false,previousFocus=null;
 const make=(tag,attrs={})=>{const e=document.createElement(tag);for(const [key,value]of Object.entries(attrs))e.setAttribute(key,value);return e};
 function close(){opening++;loading=false;if(!root)return;root.remove();root=null;button.setAttribute('aria-expanded','false');previousFocus?.focus();}
 function select(item){close();choose(item);button.title='Templates — '+item.name;}
 function showGroup(index){
  if(!root)return;active=index;const grid=root.querySelector('.template-icons');grid.replaceChildren();
  root.querySelectorAll('.template-category').forEach((e,i)=>e.setAttribute('aria-expanded',String(i===index)));
  for(const item of groups[index].items){const b=make('button',{type:'button',class:'template-icon',title:item.name,'aria-label':item.name});b.innerHTML=item.svg;const text=make('span');text.textContent=item.name;b.append(text);b.addEventListener('pointerup',e=>{if(e.button!==0)return;e.preventDefault();e.stopPropagation();select(item)});b.addEventListener('click',e=>{e.preventDefault();if(root)select(item)});grid.append(b);}
 }
 async function open(){
  if(root)return;const request=++opening;previousFocus=document.activeElement;loading=true;let data;try{data=await load()}catch(error){if(request===opening)loading=false;throw error}if(request!==opening)return;loading=false;groups=data.templates;
  root=make('div',{class:'template-cascade',role:'dialog','aria-label':'Templates'});const cats=make('div',{class:'template-categories',role:'menu','aria-label':'Template categories'}),grid=make('div',{class:'template-icons',role:'group','aria-label':'Template icons'});root.append(cats,grid);
  groups.forEach((group,i)=>{const b=make('button',{type:'button',class:'template-category',role:'menuitem','aria-haspopup':'true'});b.textContent=group.name+' ▸';b.addEventListener('pointerenter',()=>showGroup(i));b.addEventListener('click',()=>showGroup(i));b.addEventListener('keydown',e=>{if(e.key==='ArrowRight'){e.preventDefault();showGroup(i);grid.querySelector('button')?.focus()}else if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();cats.children[(i+(e.key==='ArrowDown'?1:groups.length-1))%groups.length].focus()}});cats.append(b)});
  document.body.append(root);button.setAttribute('aria-expanded','true');const rect=button.getBoundingClientRect();root.style.left=Math.max(4,Math.min(rect.right+4,innerWidth-root.offsetWidth-4))+'px';root.style.top=Math.max(4,Math.min(rect.top,innerHeight-root.offsetHeight-4))+'px';showGroup(Math.min(active,groups.length-1));
  root.addEventListener('keydown',e=>{e.stopPropagation();if(e.key==='Escape'){e.preventDefault();close()}else if(e.key==='ArrowLeft'){e.preventDefault();cats.children[active].focus()}});
 }
 button.setAttribute('aria-haspopup','dialog');button.setAttribute('aria-expanded','false');
 button.addEventListener('pointerdown',e=>{if(e.button!==0)return;e.preventDefault();e.stopPropagation();open().catch(error=>notify(error.message))});
 button.addEventListener('click',e=>{e.preventDefault();open().catch(error=>notify(error.message))});
 button.addEventListener('keydown',e=>{if(['ArrowDown','Enter',' '].includes(e.key)){e.preventDefault();e.stopPropagation();open().then(()=>root?.querySelector('.template-category')?.focus())}});
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&(root||loading)){close();e.preventDefault();e.stopImmediatePropagation()}},true);
 document.addEventListener('pointerdown',e=>{if(root&&!root.contains(e.target)&&!button.contains(e.target)){const onCanvas=e.target===canvas||canvas.contains(e.target);close();if(onCanvas){e.preventDefault();e.stopImmediatePropagation()}}},true);
 // Cache the catalog before a quick press-drag-release; failure is reported on open.
 load().catch(()=>{});
 return {open,close};
};
