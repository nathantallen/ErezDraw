const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync('assets/editor.html','utf8');
const code=html.slice(html.indexOf('function hoverGraphic(){'),html.indexOf('function render(){'));
const atom={id:'n',x:10,y:20},other={id:'c',x:40,y:50};let target={kind:'atom',item:atom};
const ctx={pointerOnCanvas:true,gesture:null,editing:null,lastPointer:{x:10,y:20},zoom:2,doc:{atoms:[atom,other]},ChemCore:{atom:(d,id)=>d.atoms.find(a=>a.id===id)},hit:()=>target,objectBounds:a=>({x:a.x-5,y:a.y-5,x2:a.x+5,y2:a.y+5}),sv:(tag,attrs)=>({tag,attrs,children:[],append(x){this.children.push(x)},setAttribute(k,v){this.attrs[k]=v}})};
vm.createContext(ctx);vm.runInContext(code,ctx);const draw=()=>vm.runInContext('hoverGraphic()',ctx);
let g=draw();assert.equal(g.attrs['data-hover-kind'],'atom');assert.equal(g.children[0].tag,'rect');assert.equal(g.attrs['pointer-events'],'none');
target={kind:'bond',item:{id:'b',a:'n',b:'c'}};g=draw();assert.equal(g.children[0].tag,'line');assert.equal(g.children[0].attrs['stroke-width'],4);
target={kind:'annotation',item:atom};assert.equal(draw().attrs['data-hover-kind'],'annotation');
for(const key of ['gesture','editing']){ctx[key]={};assert.equal(draw().children.length,0);ctx[key]=null}
ctx.pointerOnCanvas=false;assert.equal(draw().children.length,0);ctx.pointerOnCanvas=true;target=null;assert.equal(draw().children.length,0);
assert(html.includes('canvas.append(drawingGroup(true),hoverGraphic())'));
assert(!html.slice(html.indexOf('function exportSVG('),html.indexOf('function exportSVG(')+3000).includes('hoverGraphic()'));
console.log('PASS: hover outlines atoms/annotations, highlights bonds, ignores pointer events, hides during editing/drag/outside canvas, and stays out of exports.');
