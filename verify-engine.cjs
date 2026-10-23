const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const html=fs.readFileSync(__dirname+'/assets/editor.html','utf8');
const script=fs.readFileSync(__dirname+'/assets/shortcuts.js','utf8')+'\n'+fs.readFileSync(__dirname+'/assets/charges.js','utf8')+'\n'+fs.readFileSync(__dirname+'/assets/text.js','utf8')+'\n'+fs.readFileSync(__dirname+'/assets/graphics.js','utf8')+'\n'+fs.readFileSync(__dirname+'/assets/chemgeometry.js','utf8')+'\n'+html.match(/<script>([\s\S]*?)<\/script>/)[1];
new vm.Script(script);
// Model checks run without a browser or chemical toolkit.
const ctx={window:{}};vm.createContext(ctx);vm.runInContext(script.slice(0,script.indexOf('const $=id=>')),ctx);const core=ctx.window.ChemCore;
let d=core.blank();d.name='Metal / aromatic / alias roundtrip';d.atoms=[{id:'a',x:40,y:80,label:'Y',charge:3},{id:'b',x:80,y:80,label:'N',charge:-1},{id:'c',x:120,y:80,label:'HMDS',charge:0},{id:'d',x:100,y:120,label:'C',charge:0}];d.bonds=[{id:'1',a:'a',b:'b',order:1,style:'coord'},{id:'2',a:'b',b:'c',order:2,style:'normal'},{id:'3',a:'c',b:'d',order:1,style:'wedge'},{id:'4',a:'d',b:'a',order:4,style:'normal'}];d.annotations=[{id:'t',type:'text',x:10,y:10,text:'La(HMDS)3'}];
let v=core.validate(d);assert.equal(v.atoms.length,4);assert.equal(core.connected(d,'a').size,4);assert.equal(core.nearAtom(d,{x:42,y:82}).id,'a');assert.equal(core.segmentDistance({x:5,y:5},{x:0,y:0},{x:10,y:0}),5);
const mol=core.toMol(d),back=core.fromMol(mol);assert.equal(back.atoms[0].label,'Y');assert.equal(back.atoms[0].charge,3);assert.equal(back.atoms[1].charge,-1);assert.equal(back.atoms[2].label,'HMDS');assert.equal(back.atoms[0].y,80);assert.equal(back.bonds[0].style,'normal');assert.equal(back.bonds[2].style,'wedge');assert.equal(back.bonds[3].order,4);assert.equal(back.annotations.length,0);
const invalid=core.clone(d);invalid.bonds[0].a='missing';assert.throws(()=>core.validate(invalid));const dupe=core.clone(d);dupe.atoms[1].id='a';assert.throws(()=>core.validate(dupe));assert.throws(()=>core.fromMol(mol.replace('V2000','V3000')));assert.throws(()=>core.validate({format:'something-else'}));assert.equal(core.fromMol(mol+'$$$$\n'+mol).atoms.length,4);
// Execute UI logic with a minimal DOM harness. No browser layout / rendering claim.
class Element{constructor(tag='div'){this.tagName=tag.toUpperCase();this.children=[];this.attrs={};this.handlers={};this.style={};this.dataset={};this.value='';this.clientWidth=1000;this.clientHeight=650;this.options=[];this.classList={add(){},remove(){},toggle(){},contains(){return false}};}setAttribute(k,v){this.attrs[k]=String(v)}append(...v){this.children.push(...v)}replaceChildren(...v){this.children=v}addEventListener(n,f){this.handlers[n]=f}getScreenCTM(){return {inverse(){return {}}}}getBoundingClientRect(){return {x:0,y:0,left:0,top:0,width:1000,height:650}}setPointerCapture(){}focus(){}select(){}click(){}add(o){this.options.push(o)}showModal(){} }
const els=new Map();const get=id=>{if(!els.has(id))els.set(id,new Element(id==='canvas'?'svg':'div'));return els.get(id)};get('bondLength').value='40';get('zoom').options=[{value:'1'}];get('elementInput').value='C';
const documentHandlers={};
const dom={getElementById:get,querySelectorAll:()=>[],querySelector:()=>null,createElement:t=>new Element(t),createElementNS:(_,t)=>new Element(t),addEventListener(name,handler){(documentHandlers[name]??=[]).push(handler)}};
const testctx={document:dom,window:{},console,localStorage:{getItem(){return null},setItem(){}},DOMPoint:class{constructor(x,y){this.x=x;this.y=y}matrixTransform(){return this}},ResizeObserver:class{observe(){}},setTimeout:()=>0,clearTimeout(){},Option:class{constructor(text,value){this.text=text;this.value=value}},confirm:()=>true,Blob,URL,XMLSerializer:class{serializeToString(){return '<svg/>'}}};vm.createContext(testctx);vm.runInContext(script,testctx);const evaluate=s=>vm.runInContext(s,testctx),state=()=>JSON.parse(evaluate('JSON.stringify(doc)'));
// New documents use the ACS Document 1996 fixed bond length (19.2 px). These interaction checks use 40 px geometry, so the harness pins that document setting.
evaluate("{const acsBlank=ChemCore.blank;ChemCore.blank=()=>{const d=acsBlank();d.drawingSettings.bondLength=40;return d};doc=ChemCore.blank()}");
function event(x,y,extra={}){return {clientX:x,clientY:y,button:0,pointerId:1,preventDefault(){},...extra}}
function click(x,y){get('canvas').handlers.pointerdown(event(x,y));get('canvas').handlers.pointerup(event(x,y))}
function drag(x,y,x2,y2){get('canvas').handlers.pointerdown(event(x,y));get('canvas').handlers.pointermove(event(x2,y2));get('canvas').handlers.pointerup(event(x2,y2))}
click(200,200);assert.equal(state().atoms.length,2);assert.equal(state().bonds.length,1);let atom=state().atoms[1];click(atom.x,atom.y);assert.equal(state().atoms.length,3);assert.equal(state().bonds.length,2);
evaluate("action('undo')");assert.equal(state().atoms.length,2);evaluate("action('redo')");assert.equal(state().atoms.length,3);
evaluate("action('new');setTool('benzene')");click(250,200);assert.equal(state().atoms.length,6);assert.equal(state().bonds.filter(b=>b.order===2).length,3);
evaluate("action('selectAll');action('copy');action('paste')");assert.equal(state().atoms.length,12);assert.equal(state().bonds.length,12);evaluate("action('delete')");assert.equal(state().atoms.length,6);evaluate("action('undo')");assert.equal(state().atoms.length,12);
evaluate("action('new');setTool('single')");drag(100,100,140,100);evaluate("setTool('double')");click(120,100);assert.equal(state().bonds[0].order,2);assert.equal(state().atoms.length,2);
evaluate("setTool('select')");drag(75,75,165,125);assert.equal(evaluate('selection.size'),2);drag(100,100,120,130);assert.equal(state().atoms[0].x,120);assert.equal(state().atoms[0].y,130);evaluate("action('undo')");assert.equal(state().atoms[0].x,100);
evaluate("setTool('coord')");click(120,100);assert.equal(state().bonds[0].style,'coord');evaluate("setTool('arrow')");drag(200,200,350,200);assert.equal(state().annotations[0].x2,350);
evaluate("setTool('atom');element='La'");click(400,300);assert.equal(state().atoms[2].label,'La');evaluate("action('chargeUp')");assert.equal(state().atoms[2].charge,1);evaluate("setTool('erase')");click(400,300);assert.equal(state().atoms.length,3);assert.equal(state().atoms[2].label,'C');click(400,300);assert.equal(state().atoms.length,2);
evaluate("action('new');setTool('single')");drag(100,100,140,100);click(100,100);click(100,100);get('canvas').handlers.dblclick(event(100,100));assert.equal(state().atoms.length,2);assert.equal(state().bonds.length,1);assert.equal(evaluate('editing.type'),'atom');get('textEditor').value='Y';evaluate('finishEditing()');assert.equal(state().atoms[0].label,'Y');evaluate("action('undo')");assert.equal(state().atoms[0].label,'C');
evaluate("demo()");assert.equal(state().atoms.length,14);assert.equal(state().annotations.length,4);evaluate("ChemCore.validate(doc)");
console.log('PASS: JavaScript syntax; graph validation; MOL V2000 charge, alias, coordinate and bond-style roundtrips; unsupported format rejection; draw/extend/change bonds; undo/redo; benzene; selection/move; copy/paste/delete; coordination; reaction arrow; metal labels/charges; eraser; example reaction.');
// Manual-alignment checks derived from the inspected ChemDraw 8 drawing chapters.
evaluate("action('new');setTool('single')");drag(100,100,140,110);let d2=state();let angle=Math.atan2(d2.atoms[1].y-100,d2.atoms[1].x-100)*180/Math.PI;assert.ok(Math.abs(angle-15)<0.001);assert.ok(Math.abs(Math.hypot(d2.atoms[1].x-100,d2.atoms[1].y-100)-40)<0.001);
evaluate("action('new');setTool('single')");get('canvas').handlers.pointerdown(event(100,100,{altKey:true}));get('canvas').handlers.pointermove(event(220,135,{altKey:true}));get('canvas').handlers.pointerup(event(220,135,{altKey:true}));assert.ok(Math.abs(state().atoms[1].x-220)<0.001);assert.ok(Math.abs(state().atoms[1].y-135)<0.001);
evaluate("setTool('triple')");click(160,117.5);assert.equal(state().bonds[0].order,3);evaluate("setTool('erase')");click(160,117.5);assert.equal(state().bonds[0].order,2);click(160,117.5);assert.equal(state().bonds[0].order,1);
evaluate("setTool('wedge')");click(160,117.5);const start=state().bonds[0].a;click(160,117.5);assert.notEqual(state().bonds[0].a,start);
evaluate("action('new');setTool('ring6')");click(250,250);let r=state();assert.ok(Math.abs(r.atoms.reduce((s,a)=>s+a.x,0)/6-250)<0.001);assert.ok(Math.abs(r.atoms.reduce((s,a)=>s+a.y,0)/6-250)<0.001);const bond=r.bonds[0],a=r.atoms.find(a=>a.id===bond.a),b=r.atoms.find(a=>a.id===bond.b);click((a.x+b.x)/2,(a.y+b.y)/2);assert.equal(state().atoms.length,10);assert.equal(state().bonds.length,11);
evaluate("setTool('select')");get('canvas').handlers.dblclick(event(state().atoms[0].x,state().atoms[0].y));assert.equal(evaluate('selection.size'),10);
evaluate("action('new');setTool('arrow')");drag(100,100,250,100);evaluate("setTool('select')");drag(80,80,150,120);assert.equal(evaluate('annSelection.size'),0);
evaluate("action('new');setTool('single')");drag(100,100,140,100);evaluate("setTool('text')");click(100,100);get('textEditor').value='Cl';evaluate('finishEditing()');assert.equal(state().atoms[0].label,'Cl');assert.equal(state().annotations.length,0);evaluate("setTool('erase')");click(100,100);assert.equal(state().atoms[0].label,'C');assert.equal(state().bonds.length,1);
evaluate("setTool('lasso')");get('canvas').handlers.pointerdown(event(80,80));for(const [x,y]of [[160,80],[160,120],[80,120],[80,80]])get('canvas').handlers.pointermove(event(x,y));get('canvas').handlers.pointerup(event(80,80));assert.equal(evaluate('selection.size'),2);
console.log('PASS: manual alignment — 15-degree snapping, Alt unconstrained lengths/angles, reducing bond order with eraser, reversing wedge orientation, centered and fused rings, connected-structure selection, complete arrow enclosure, Text-tool atom editing, preserving bonds while erasing labels, lasso selection.');
// Rotation regression: handle dragging, exact angles, partial-structure pivot, mixed selections.
evaluate("action('new');setTool('single')");drag(100,100,140,100);evaluate("action('selectAll')");const original=state();let box=evaluate('selectionBounds()'),pivot=evaluate('rotationCenter(selectionBounds())');let hx=box.x2,hy=box.y,tx=pivot.x-(hy-pivot.y),ty=pivot.y+(hx-pivot.x);drag(hx,hy,tx,ty);assert.ok(Math.abs(state().atoms[0].x-120)<1e-6);assert.ok(Math.abs(state().atoms[0].y-80)<1e-6);assert.equal(state().bonds[0].id,original.bonds[0].id);evaluate("action('undo')");assert.deepEqual(state(),original);evaluate("action('redo')");assert.ok(Math.abs(state().atoms[1].y-120)<1e-6);
evaluate("action('undo');action('selectAll');rotateSelection(-90)");assert.ok(Math.abs(state().atoms[0].y-120)<1e-6);
evaluate("action('undo');selection=new Set([doc.atoms[1].id]);rotateSelection(90)");assert.ok(Math.abs(state().atoms[0].x-100)<1e-6);assert.ok(Math.abs(state().atoms[1].x-100)<1e-6);assert.ok(Math.abs(state().atoms[1].y-140)<1e-6);
evaluate("action('new');setTool('arrow')");drag(100,100,200,100);evaluate("action('selectAll');rotateSelection(90)");assert.ok(Math.abs(state().annotations[0].x-150)<1e-6);assert.ok(Math.abs(state().annotations[0].y-50)<1e-6);assert.ok(Math.abs(state().annotations[0].y2-150)<1e-6);
evaluate("action('new');setTool('single')");drag(100,100,140,100);evaluate("action('selectAll')");box=evaluate('selectionBounds()');get('canvas').handlers.dblclick(event(box.x2,box.y));assert.equal(evaluate('nativeRotateRequest'),true);
console.log('PASS: draggable upper-right rotation handle; exact CW/CCW rotation; fixed unselected atom pivot; arrow rotation; Undo/Redo; exact-angle dialog request.');
// Object commands preserve connected structures and support undo.
evaluate("action('new');doc.atoms=[{id:'a',x:100,y:100,label:'C',charge:0},{id:'b',x:140,y:100,label:'C',charge:0},{id:'c',x:220,y:150,label:'N',charge:0}];doc.bonds=[{id:'ab',a:'a',b:'b',order:1,style:'normal'}];selection=new Set(['a','c']);objectAlign('top')");assert.equal(state().atoms[2].y,100);assert.equal(state().atoms[1].x-state().atoms[0].x,40);evaluate("action('undo');action('selectAll');flipSelection(true)");evaluate('flipSelection(true)');assert.equal(state().atoms[0].y,100);evaluate("action('undo');action('undo');action('selectAll');scaleSelection(200)");assert.equal(state().atoms[1].x-state().atoms[0].x,80);
evaluate("action('new');doc.annotations=[{id:'t1',type:'text',x:0,y:50,text:'aa'},{id:'t2',type:'text',x:40,y:50,text:'aaaa'},{id:'t3',type:'text',x:200,y:50,text:'aa'}];action('selectAll');objectDistribute('x')");assert.equal(state().annotations[1].x,90);assert.equal(state().annotations[2].x,200);assert.equal(evaluate('ChemCore.validate(doc).annotations.length'),3);
console.log('PASS: alignment, whole-molecule movement, equal edge-gap distribution, vertical flip, geometry scaling and undo.');
// UI controls must modify persisted document fields, including label rotation.
evaluate("action('new');doc.atoms=[{id:'a',x:100,y:100,label:'N',charge:0},{id:'b',x:140,y:100,label:'O',charge:0}];doc.bonds=[{id:'ab',a:'a',b:'b',order:1,style:'normal'}];action('selectAll');setTextStyle({font:'Arial',bold:true,color:'#0033cc'});rotateSelection(90,true)");assert.equal(state().atoms[0].labelAngle,90);assert.equal(state().atoms[0].textStyle.bold,true);let checked=evaluate('ChemCore.validate(doc)');assert.equal(checked.atoms[0].labelAngle,90);assert.equal(checked.atoms[0].textStyle.color,'#0033cc');evaluate('scaleSelection(200,true)');const labelSize=evaluate('ChemCore.blank().textSettings.labelSize');assert.equal(state().atoms[0].textStyle.size,labelSize*2);assert.ok(Math.abs(evaluate('medianSelectedBond()')-80)<1e-6);evaluate("action('undo')");assert.equal(state().atoms[0].textStyle.size,labelSize);evaluate("action('selectAll');setTextStyle({plain:true})");assert.equal(state().atoms[0].textStyle.bold,false);
console.log('PASS: persisted font styling, label rotation, label scaling, median bond length and Undo.');
evaluate("action('new');doc.atoms=[{id:'a',x:100,y:100,label:'N',charge:0},{id:'b',x:140,y:100,label:'O',charge:0}];doc.bonds=[{id:'ab',a:'a',b:'b',order:1,style:'normal'}];doc.annotations=[{id:'t',type:'text',x:80,y:200,text:'Caption'}];selection=new Set(['a']);annSelection=new Set(['t']);groupSelection()");assert.equal(state().groups[0].atoms.length,2);assert.equal(evaluate('ChemCore.validate(doc).groups.length'),1);assert.equal(evaluate('selectedUnits().length'),1);evaluate('integralSelection()');assert.equal(state().groups[0].integral,true);evaluate("copy();paste()");assert.equal(state().groups.length,2);assert.equal(evaluate('ChemCore.validate(doc).groups.length'),2);evaluate('ungroupSelection()');assert.equal(state().groups.length,1);evaluate("action('undo');selection=new Set(doc.groups[1].atoms);annSelection=new Set(doc.groups[1].annotations);deleteSelection()");assert.equal(state().groups.length,1);assert.equal(evaluate('ChemCore.validate(doc).groups.length'),1);
console.log('PASS: persisted Group/Ungroup, integral groups, whole-molecule grouping, grouped alignment units, clipboard duplication and deletion cleanup.');
// Ring doubles must preserve every outer edge; second lines must face inward.
evaluate("action('new');setTool('benzene')");click(250,250);for(const b of state().bonds){const segments=evaluate('bondSegments(doc.bonds.find(b=>b.id==='+JSON.stringify(b.id)+'))');const a=state().atoms.find(a=>a.id===b.a),z=state().atoms.find(a=>a.id===b.b);assert.equal(segments[0].x1,a.x);assert.equal(segments[0].y1,a.y);assert.equal(segments[0].x2,z.x);assert.equal(segments[0].y2,z.y);if(b.order===2){assert.equal(segments.length,2);const mid=p=>({x:(p.x1+p.x2)/2,y:(p.y1+p.y2)/2});assert.ok(Math.hypot(mid(segments[1]).x-250,mid(segments[1]).y-250)<Math.hypot(mid(segments[0]).x-250,mid(segments[0]).y-250));assert.ok(Math.hypot(segments[1].x2-segments[1].x1,segments[1].y2-segments[1].y1)<40)}}
for(const style of ['dashed','hashed','boldBond','hollowWedge','wavy','crossBond']){evaluate("action('new');setTool("+JSON.stringify(style)+")");drag(100,100,140,100);assert.equal(state().bonds[0].style,style);assert.equal(evaluate('ChemCore.validate(doc).bonds[0].style'),style);evaluate('render()');evaluate("action('undo')");assert.equal(state().bonds.length,0)}
evaluate("action('new');setTool('chain')");drag(100,100,250,100);assert.ok(state().bonds.length>=4);for(const b of state().bonds){const a=state().atoms.find(a=>a.id===b.a),z=state().atoms.find(a=>a.id===b.b);assert.ok(Math.abs(Math.hypot(z.x-a.x,z.y-a.y)-40)<1e-6)}
for(const kind of ['chair','chair2','cyclopentadiene']){evaluate("action('new');setTool("+JSON.stringify(kind)+")");click(250,250);assert.equal(state().atoms.length,kind==='cyclopentadiene'?5:6);assert.equal(state().bonds.length,state().atoms.length);assert.equal(state().bonds.filter(b=>b.order===2).length,kind==='cyclopentadiene'?2:0)}
for(const kind of ['equilibrium','curvedArrow','fishhook','elements','ellipse','bracket']){evaluate("action('new');setTool("+JSON.stringify(kind)+")");drag(100,100,240,180);assert.equal(state().annotations[0].variant,kind);assert.equal(evaluate('ChemCore.validate(doc).annotations[0].variant'),kind);evaluate('render();action("selectAll");rotateSelection(30);copy();paste();');assert.equal(state().annotations.length,2)}
console.log('PASS: complete ring perimeter with shortened internal doubles, six added bond styles, zigzag chains, chair/Cp templates, arrow variants, drawing elements, validation and Undo.');
evaluate("action('new');doc.atoms=[{id:'n',x:100,y:100,label:'N',charge:0}];setTool('chargeUp')");click(100,100);assert.equal(state().atoms[0].charge,1);evaluate("setTool('chargeDown')");click(100,100);assert.equal(state().atoms[0].charge,0);evaluate("setTool('radical')");click(100,100);assert.equal(state().atoms[0].radical,1);evaluate("setTool('lonePair')");click(100,100);assert.equal(state().atoms[0].lonePairs,1);assert.equal(evaluate('ChemCore.validate(doc).atoms[0].lonePairs'),1);assert.equal(evaluate('ChemCore.validate(doc).atoms[0].radical'),1);evaluate("action('undo')");assert.equal(state().atoms[0].lonePairs,undefined);click(220,100);assert.equal(state().annotations[0].text,':');assert.equal(state().bonds.length,0);
console.log('PASS: click-to-place charge/radical/unshared-pair tools, persisted electron symbols, standalone symbols and Undo.');
// Geometry adapters: measured-box clipping, open-angle marks and double alignment.
let clipped=evaluate("ErezGeometry.clippedSegment({x:0,y:0},{x:100,y:0},null,{x:80,y:-10,x2:120,y2:10},2)");assert.equal(clipped.x2,78);assert.equal(evaluate("ErezGeometry.clippedSegment({x:0,y:0},{x:10,y:0},{x:-20,y:-20,x2:20,y2:20},{x:-10,y:-10,x2:30,y2:10})"),null);
evaluate("action('new');doc.atoms=[{id:'a',x:0,y:0,label:'C',charge:0},{id:'b',x:40,y:0,label:'C',charge:0}];doc.bonds=[{id:'ab',a:'a',b:'b',order:2,style:'normal'}];cycleDoubleAlignment('ab')");assert.equal(state().bonds[0].doublePosition,'left');evaluate("cycleDoubleAlignment('ab')");assert.equal(state().bonds[0].doublePosition,'right');evaluate("cycleDoubleAlignment('ab')");assert.equal(state().bonds[0].doublePosition,'center');evaluate("action('undo')");assert.equal(state().bonds[0].doublePosition,'right');
// Cp anion: five chemical atoms, true geometric centroid and a haptic attachment.
evaluate("action('new');setTool('cpAnion')");click(250,250);let cp=state().ligands[0],centroid=state().atoms.find(a=>a.id===cp.centroidId);assert.equal(state().atoms.length,6);assert.equal(state().atoms.filter(a=>a.nodeType!=='centroid').length,5);assert.equal(state().atoms.reduce((sum,a)=>sum+a.charge,0),-1);assert.equal(state().bonds.length,5);assert.equal(centroid.x,250);assert.equal(centroid.y,250);assert.equal(evaluate('ChemCore.validate(doc).ligands.length'),1);
evaluate("setTool('atom');element='Y'");click(400,250);evaluate("setTool('coord')");drag(250,250,400,250);let attachment=state().bonds.find(b=>b.a===cp.centroidId||b.b===cp.centroidId);assert.ok(attachment);assert.equal(attachment.style,'coord');assert.equal(evaluate('ChemCore.connected(doc,doc.ligands[0].centroidId).size'),7);
evaluate("selection=new Set([...doc.ligands[0].atomIds,doc.ligands[0].centroidId]);annSelection.clear();rotateSelection(90);updateCentroids()");cp=state().ligands[0];centroid=state().atoms.find(a=>a.id===cp.centroidId);let members=state().atoms.filter(a=>cp.atomIds.includes(a.id));assert.ok(Math.abs(centroid.x-members.reduce((sum,a)=>sum+a.x,0)/5)<1e-6);assert.ok(Math.abs(centroid.y-members.reduce((sum,a)=>sum+a.y,0)/5)<1e-6);assert.equal(evaluate('ChemCore.fromMol(ChemCore.toMol(doc)).atoms.length'),6);evaluate('copy();paste();');assert.equal(state().ligands.length,2);assert.equal(evaluate('ChemCore.validate(doc).ligands.length'),2);evaluate('deleteSelection()');assert.equal(state().ligands.length,1);evaluate("action('undo')");assert.equal(state().ligands.length,2);
console.log('PASS: measured box clipping, double-side cycling, Cp anion creation, centroid bonding to Y, tied centroid transforms, serialization, clipboard, chemical MOL filtering and Undo.');
evaluate("action('new');placeCpAnion({x:250,y:250});copy();paste();paste();");assert.equal(state().ligands.length,3);assert.equal(evaluate('ChemCore.validate(doc).ligands.length'),3);for(const l of state().ligands){const anchor=state().atoms.find(a=>a.id===l.centroidId);assert.ok(anchor.members.every(id=>l.atomIds.includes(id)))}
console.log('PASS: repeated Cp paste preserves every independent centroid and ligand identity.');

for(const t of ['arrow','equilibrium','curvedArrow','fishhook','elements','ellipse','bracket','single','benzene','chain','cpAnion','chair','atom','chargeUp','radical','lonePair']){
 evaluate(`doc=ChemCore.blank();selection.clear();annSelection.clear();undoStack=[];setTool('${t}')`);
 const before=JSON.stringify(state());get('canvas').handlers.pointerdown(event(200,200));
 assert.equal(JSON.stringify(state()),before,t+' must not finalize on mouse down');assert.equal(evaluate('undoStack.length'),0);
 assert.ok(get('canvas').children.some(n=>n.attrs?.['data-preview']==='true'),t+' mouse-down preview');
 get('canvas').handlers.pointermove(event(320,240));assert.equal(JSON.stringify(state()),before);
 get('canvas').handlers.pointercancel(event(320,240));assert.equal(JSON.stringify(state()),before);assert.equal(evaluate('undoStack.length'),0);
 drag(200,200,320,240);assert.ok(state().atoms.length||state().annotations.length);assert.equal(evaluate('undoStack.length'),1,t+' single commit');
 evaluate("action('undo')");assert.equal(JSON.stringify(state()),before);
}
evaluate("setTool('arrow');setTool(false);setTool('invalid')");assert.equal(evaluate('tool'),'arrow');
console.log('PASS: mouse-down object previews, drag without document mutation, cancel, mouse-up single commit and Undo; invalid tool rejection.');
// Perspective Cp rings preserve the graph and centroid while projecting all decoration.
for(const tilt of [30,60,75]){
 evaluate(`doc=ChemCore.blank();selection.clear();annSelection.clear();undoStack=[];setTool('cpTilt${tilt}')`);
 get('canvas').handlers.pointerdown(event(250,250));assert.equal(state().atoms.length,0);
 get('canvas').handlers.pointermove(event(350,250));assert.equal(state().atoms.length,0);
 get('canvas').handlers.pointerup(event(350,250));
 const cp=state();assert.equal(cp.ligands[0].perspectiveTilt,tilt);assert.equal(cp.atoms.length,6);assert.equal(cp.bonds.length,5);assert.equal(evaluate('undoStack.length'),1);
 const r=40/(2*Math.sin(Math.PI/5));assert.ok(Math.abs(cp.atoms[0].y-(250-r*Math.cos(tilt*Math.PI/180)))<1e-8);
 assert.ok(Math.abs(cp.atoms[5].x-250)<1e-8);assert.ok(Math.abs(cp.atoms[5].y-250)<1e-8);
 const deco=JSON.parse(evaluate('JSON.stringify(cpDecoration(doc.ligands[0]))'));
 assert.ok(Math.abs(Math.max(...deco.innerPoints.map(p=>p.y))-250-.48*r*Math.cos(tilt*Math.PI/180))<1e-8);
 evaluate("doc=ChemCore.validate(doc);action('selectAll');rotateSelection(90);action('copy');action('paste');doc=ChemCore.validate(doc)");
 assert.equal(state().ligands[1].perspectiveTilt,tilt);assert.equal(state().ligands.length,2);
 evaluate("action('undo');action('undo')");assert.equal(state().ligands.length,1);
}
evaluate("doc=ChemCore.blank();selection.clear();annSelection.clear();undoStack=[];setTool('cpTilt60')");drag(250,250,250,350);
assert.ok(Math.abs(state().atoms[0].x-(250+40/(2*Math.sin(Math.PI/5))*.5))<1e-8);
evaluate("setTool('single')");drag(250,250,250,170);assert.ok(state().bonds.some(b=>b.a===state().ligands[0].centroidId));
console.log('PASS: three Cp perspective tilts; projected aromatic ellipse; drag orientation; centroid attachment; save validation, rotation, copy/paste and Undo.');
for(const t of ['arrow','solidArrow','hollowArrow','boldArrow','dashedArrow','resonance','equilibrium','equilibriumRight','equilibriumLeft','twoWay','retrosynthetic','noGo','straightFishhook','curvedArrow','fishhook','arcArrow90','arcArrow120','arcArrow180','arcArrow270']){
 evaluate(`doc=ChemCore.blank();selection.clear();annSelection.clear();undoStack=[];setTool('${t}')`);
 get('canvas').handlers.pointerdown(event(200,200));get('canvas').handlers.pointermove(event(320,200,{altKey:true}));assert.equal(state().annotations.length,0);
 get('canvas').handlers.pointerup(event(320,200,{altKey:true}));assert.equal(state().annotations.length,1);assert.equal(state().annotations[0].reversed,true,t);
 evaluate("doc=ChemCore.validate(doc);action('selectAll');action('copy');action('paste');doc=ChemCore.validate(doc)");assert.equal(state().annotations[1].reversed,true);
 if(t.startsWith('arcArrow')){const pts=JSON.parse(evaluate('JSON.stringify(arrowCurve(doc.annotations[0]))'));assert.ok(Math.hypot(pts.at(-1).x-320,pts.at(-1).y-200)<1e-7);assert.ok(evaluate('annotationHit(doc.annotations[0],arrowCurve(doc.annotations[0])[30])'));const b=JSON.parse(evaluate('JSON.stringify(objectBounds(doc.annotations[0]))'));assert.ok(pts.every(p=>p.x>=b.x&&p.x<=b.x2&&p.y>=b.y&&p.y<=b.y2));}
}
for(const t of ['chair','chair2']){
 evaluate(`doc=ChemCore.blank();selection.clear();annSelection.clear();undoStack=[];setTool('${t}')`);click(250,250);const d=state();assert.equal(d.atoms.length,6);assert.equal(d.bonds.length,6);assert.equal(evaluate('undoStack.length'),1);
 const vectors=d.atoms.map((a,i)=>({x:d.atoms[(i+1)%6].x-a.x,y:d.atoms[(i+1)%6].y-a.y}));for(let i=0;i<3;i++){assert.ok(Math.abs(vectors[i].x+vectors[i+3].x)<1e-8);assert.ok(Math.abs(vectors[i].y+vectors[i+3].y)<1e-8)}
 assert.ok(d.atoms[0].y===250+(t==='chair'?-18:18));evaluate("action('undo')");assert.equal(state().atoms.length,0);
}
console.log('PASS: expanded arrow styles, Alt reversal, persistence, curved/arc hit testing and export bounds; both chair projections with three opposite parallel bond pairs.');
evaluate("doc=ChemCore.blank();selection.clear();annSelection.clear();undoStack=[];setTool('arrow')");drag(200,200,320,200);
get('canvas').handlers.pointerdown(event(260,200,{altKey:true}));assert.equal(state().annotations[0].reversed,undefined);get('canvas').handlers.pointerup(event(260,200,{altKey:true}));assert.equal(state().annotations.length,1);assert.equal(state().annotations[0].reversed,true);evaluate("action('undo')");assert.equal(state().annotations[0].reversed,undefined);
console.log('PASS: Alt-click reverses an existing arrow on release and is undoable.');
// Structure perspective: true accumulated depth, chemical-only selection and transactions.
evaluate("doc=ChemCore.blank();doc.atoms=[{id:'a',x:100,y:100,label:'C',charge:0},{id:'b',x:180,y:100,label:'N',charge:0},{id:'c',x:140,y:160,label:'O',charge:0}];doc.bonds=[{id:'ab',a:'a',b:'b',order:1,style:'wedge'},{id:'bc',a:'b',b:'c',order:1,style:'coord'}];doc.annotations=[{id:'txt',type:'text',x:120,y:120,text:'unchanged'}];selection.clear();annSelection.clear();undoStack=[];redoStack=[];setTool('trackball')");
drag(80,80,200,180);assert.equal(evaluate('selection.size'),3);assert.equal(evaluate('annSelection.size'),0);
const flat=state(),beforePerspectiveUndo=evaluate('undoStack.length');
get('canvas').handlers.pointerdown(event(140,130));get('canvas').handlers.pointermove(event(195,150));assert.ok(state().atoms.some(a=>Math.abs(a.z)>1));assert.equal(evaluate('undoStack.length'),beforePerspectiveUndo);get('canvas').handlers.pointercancel();assert.deepEqual(state(),flat);
get('canvas').handlers.pointerdown(event(140,130));get('canvas').handlers.pointermove(event(195,150));get('canvas').handlers.pointerup(event(195,150));let tilted=state();assert.equal(evaluate('undoStack.length'),beforePerspectiveUndo+1);assert.deepEqual(tilted.annotations,flat.annotations);assert.deepEqual(tilted.bonds,flat.bonds);
const distance3=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y,(a.z||0)-(b.z||0));assert.ok(Math.abs(distance3(tilted.atoms[0],tilted.atoms[1])-80)<1e-6);
assert.deepEqual(JSON.parse(evaluate('JSON.stringify(ChemCore.validate(doc))')),tilted);
const molTilt=evaluate('ChemCore.fromMol(ChemCore.toMol(doc))');assert.ok(Math.abs(molTilt.atoms[0].z-tilted.atoms[0].z)<.003);
evaluate('copy();paste()');assert.ok(state().atoms.slice(3).every((a,i)=>a.z===tilted.atoms[i].z));evaluate("action('undo');selection=new Set(doc.atoms.map(a=>a.id));action('flatten')");assert.ok(state().atoms.every(a=>a.z===undefined));assert.ok(state().atoms.every((a,i)=>a.x===tilted.atoms[i].x&&a.y===tilted.atoms[i].y));evaluate("action('undo')");assert.deepEqual(state(),tilted);
// Inverse rotations recover the starting coordinates instead of repeated 2D squashing.
evaluate('selection=new Set(doc.atoms.map(a=>a.id));const ps=perspectiveState();applyPerspective(ps,.3,.4);const ps2={...perspectiveState(),center:ps.center};applyPerspective(ps2,0,-.4);const ps3={...perspectiveState(),center:ps.center};applyPerspective(ps3,-.3,0)');for(let i=0;i<3;i++)assert.ok(distance3(state().atoms[i],tilted.atoms[i])<1e-6);
// Shift chooses only one axis; a partial selection pivots about one fixed neighbor.
evaluate("doc=ChemCore.clone("+JSON.stringify(flat)+");selection=new Set(doc.atoms.map(a=>a.id));setTool('trackball')");get('canvas').handlers.pointerdown(event(140,130));get('canvas').handlers.pointermove(event(190,140,{shiftKey:true}));assert.ok(Math.abs(evaluate('gesture.rx'))<1e-12);get('canvas').handlers.pointerup(event(190,140,{shiftKey:true}));assert.ok(state().atoms.every((a,i)=>a.y===flat.atoms[i].y));
evaluate("doc=ChemCore.blank();doc.atoms=[{id:'p',x:100,y:100,label:'C',charge:0},{id:'q',x:180,y:100,label:'C',charge:0}];doc.bonds=[{id:'pq',a:'p',b:'q',order:1,style:'normal'}];selection=new Set(['q']);annSelection.clear();applyPerspective(perspectiveState(),0,Math.PI/3)");assert.equal(state().atoms[0].x,100);assert.ok(Math.abs(state().atoms[1].x-140)<1e-6);assert.ok(Math.abs(distance3(state().atoms[0],state().atoms[1])-80)<1e-6);
assert.throws(()=>evaluate("ChemCore.validate({...doc,atoms:doc.atoms.map(a=>({...a,z:Infinity}))})"));
console.log('PASS: structure trackball chemical-only marquee, preview/cancel/one Undo, 3D distance preservation, inverse rotations, Shift axis constraint, fixed-neighbor pivot, upright annotations, preserved bond styles, depth validation, JSON/MOL/clipboard roundtrips and Flatten.');
// Pen is an anchor/tangent Bézier tool, not a chemical bond tool.
evaluate("doc=ChemCore.blank();selection.clear();annSelection.clear();undoStack=[];redoStack=[];setTool('pen')");click(100,100);assert.equal(state().annotations[0].type,'pen');drag(180,130,190,90);assert.equal(state().annotations[0].points.length,2);assert.equal(state().annotations[0].points[1].hy,-40);assert.equal(state().atoms.length,0);evaluate("curveCommand({heads:'end'});ChemCore.validate(doc)");assert.ok(evaluate("penPath(doc.annotations[0]).includes('C')"));const penSaved=state();evaluate('copy();paste();ChemCore.validate(doc)');assert.equal(state().annotations.length,2);evaluate("action('undo');action('selectAll');rotateSelection(45)");assert.equal(state().annotations[0].angle,45);evaluate("action('undo')");assert.deepEqual(state(),penSaved);
evaluate("doc=ChemCore.blank();selection.clear();annSelection.clear();undoStack=[];setTool('orbital_dxy_phase')");get('canvas').handlers.pointerdown(event(250,250));assert.equal(state().annotations.length,0);get('canvas').handlers.pointermove(event(300,275));assert.equal(state().annotations.length,0);get('canvas').handlers.pointerup(event(300,275));assert.equal(state().annotations[0].type,'orbital');assert.equal(state().annotations[0].kind,'dxy');evaluate('ChemCore.validate(doc);copy();paste();ChemCore.validate(doc)');assert.equal(state().annotations.length,2);evaluate("action('undo');action('selectAll');scaleSelection(150)");assert.ok(state().annotations[0].width>160);
evaluate("doc=ChemCore.blank();selection.clear();annSelection.clear();undoStack=[];setTool('table')");drag(100,200,340,320);assert.equal(state().annotations[0].type,'table');assert.equal(state().annotations[0].rows,3);evaluate("doc.annotations[0].cells[0]='Catalyst';ChemCore.validate(doc);copy();paste();ChemCore.validate(doc)");assert.equal(state().annotations[1].cells[0],'Catalyst');
// Rich runs survive validation and clipboard and do not change atom identity.
evaluate("doc=ChemCore.blank();doc.annotations=[{id:'t',type:'text',x:100,y:100,text:'MeCp3Y',textRuns:[{text:'MeCp',bold:true},{text:'3',script:'sub'},{text:'Y',italic:true}],alignment:'right',lineSpacing:1.5}];selection.clear();annSelection=new Set(['t']);ChemCore.validate(doc);copy();paste();ChemCore.validate(doc)");assert.equal(state().annotations[1].textRuns[1].script,'sub');assert.equal(state().annotations[1].alignment,'right');evaluate("setTextStyle({plain:true})");assert.equal(state().annotations[1].textRuns[1].script,'normal');
// Dynamic charge is conservative, reversible and honors manual overrides.
evaluate("doc=ChemCore.blank();doc.atoms=[{id:'n',x:0,y:0,label:'N',charge:0},...Array.from({length:4},(_,i)=>({id:'c'+i,x:i*40,y:40,label:'C',charge:0}))];doc.bonds=doc.atoms.slice(1).map(a=>({id:'b'+a.id,a:'n',b:a.id,style:'normal',order:1}));updateBondCharges()");assert.equal(state().atoms[0].charge,1);evaluate('doc.bonds.pop();updateBondCharges()');assert.equal(state().atoms[0].charge,0);evaluate("doc.atoms[0].charge=-1;doc.atoms[0].chargeMode='manual';updateBondCharges()");assert.equal(state().atoms[0].charge,-1);
evaluate("doc=ChemCore.blank();selection.clear();annSelection.clear();const cp=placeCpAnion({x:250,y:250});const y=addAtom({x:300,y:300},'Y');addBond(ChemCore.atom(doc,cp.centroidId),y,1,'coord');updateBondCharges()");assert.equal(state().atoms.at(-1).charge,1);assert.equal(evaluate("labelElement(doc.atoms.at(-1),true).children.at(-1).attrs['data-metal-charge']"),'true');evaluate('doc.bonds=doc.bonds.filter(b=>b.style!==\'coord\');updateBondCharges()');assert.equal(state().atoms.at(-1).charge,0);
console.log('PASS: Bézier anchors/tangents, curve styles, orbital/table preview and transforms, rich-run persistence/formatting, clipboard roundtrips and dynamic/manual charges.');

// Keyboard event regression tests: exact modifiers and hotspot precedence.
evaluate("doc=ChemCore.blank();selection.clear();annSelection.clear();gesture=null;pointerOnCanvas=true;lastPointer={x:100,y:100};addAtom(lastPointer);setTool('select')");
function keyEvent(key,mods={}){return {key,target:{tagName:'SVG'},preventDefault(){},stopImmediatePropagation(){},ctrlKey:false,metaKey:false,shiftKey:false,altKey:false,...mods}}
testctx.keyEvent=keyEvent;
assert.equal(evaluate("handleChemDrawKey(keyEvent('b'))"),true);assert.equal(state().atoms[0].label,'Br');
evaluate("handleChemDrawKey(keyEvent('B',{shiftKey:true}))");assert.equal(state().atoms[0].label,'B');
evaluate("handleChemDrawKey(keyEvent(' '))");assert.equal(state().atoms[0].label,'C');
evaluate("handleChemDrawKey(keyEvent('1'))");assert.equal(state().bonds.length,1);assert.equal(state().bonds[0].order,1);
evaluate("lastPointer={x:(doc.atoms[0].x+doc.atoms[1].x)/2,y:(doc.atoms[0].y+doc.atoms[1].y)/2};handleChemDrawKey(keyEvent('2'));handleChemDrawKey(keyEvent('l'))");assert.equal(state().bonds[0].order,2);assert.equal(state().bonds[0].doublePosition,'left');
evaluate("handleChemDrawKey(keyEvent('b'))");assert.equal(state().bonds[0].style,'boldBond');
assert.equal(evaluate("ErezShortcuts.resolve(keyEvent('v',{ctrlKey:true,shiftKey:true}))"),'flipVertical');
assert.equal(evaluate("ErezShortcuts.resolve(keyEvent('c',{ctrlKey:true,shiftKey:true,altKey:true}))"),'align_horizontal');
assert.equal(evaluate("ErezShortcuts.resolve(keyEvent('c',{metaKey:true,shiftKey:true}))"),'textCenter');
assert.equal(evaluate("ErezShortcuts.resolve(keyEvent('c',{ctrlKey:true,altKey:true}))"),null);
assert.equal(evaluate("handleChemDrawKey({key:'b',target:{tagName:'INPUT'},ctrlKey:true})"),false);
evaluate("pointerOnCanvas=false;handleChemDrawKey(keyEvent('e'))");assert.equal(evaluate('tool'),'arrow');
evaluate("handleChemDrawKey(keyEvent('X',{shiftKey:true}))");assert.equal(evaluate('tool'),'chain');
assert.equal(evaluate("handleChemDrawKey(keyEvent('F6'))"),true);
console.log('PASS: shortcut modifier resolution, macOS Command, focus guards, atom and bond hotspot edits, generic tool switching, function-key view commands.');
// Ctrl-drag duplicates the selection without moving originals or replacing the clipboard.
evaluate("doc=ChemCore.blank();const a=addAtom({x:100,y:100}),b=addAtom({x:140,y:100});addBond(a,b);selection=new Set([a.id,b.id]);annSelection.clear();tool='select';clipboard={sentinel:true};undoStack=[];redoStack=[];zoom=1;showCrosshair=false;showRulers=false;");
const originalDrag=state();
get('canvas').handlers.pointerdown(event(100,100,{ctrlKey:true}));
get('canvas').handlers.pointermove(event(102,101,{ctrlKey:true}));assert.deepEqual(state(),originalDrag);
get('canvas').handlers.pointermove(event(200,180,{ctrlKey:true}));
assert.equal(state().atoms.length,4);assert.deepEqual(state().atoms.slice(0,2),originalDrag.atoms);assert.equal(evaluate('undoStack.length'),0);
get('canvas').handlers.pointerup(event(200,180,{ctrlKey:true}));
assert.equal(evaluate('undoStack.length'),1);assert.equal(evaluate('clipboard.sentinel'),true);
assert.equal(state().atoms[2].x,200);assert.equal(state().atoms[2].y,180);
evaluate("action('undo')");assert.deepEqual(state(),originalDrag);
evaluate("selection=new Set(doc.atoms.map(a=>a.id));tool='lasso'");
get('canvas').handlers.pointerdown(event(100,100,{ctrlKey:true,shiftKey:true}));
get('canvas').handlers.pointermove(event(200,150,{ctrlKey:true,shiftKey:true}));
get('canvas').handlers.pointerup(event(200,150,{ctrlKey:true,shiftKey:true}));
assert.equal(state().atoms.length,4);assert.equal(state().atoms[2].y,100);assert.equal(evaluate('tool'),'lasso');
evaluate("action('undo');selection=new Set(doc.atoms.map(a=>a.id));tool='select'");
get('canvas').handlers.pointerdown(event(120,100,{ctrlKey:true}));get('canvas').handlers.pointermove(event(220,200,{ctrlKey:true}));
evaluate('cancelGesture();render()');assert.deepEqual(state(),originalDrag);assert.equal(evaluate('selection.size'),2);
// Captions, arrows and integral groups get independent IDs, metadata and one Undo.
evaluate("doc=ChemCore.blank();doc.annotations=[{id:'text1',type:'text',x:400,y:300,text:'Label',textRuns:[{text:'Label',bold:true}]},{id:'arr1',type:'arrow',x:450,y:300,x2:500,y2:300}];selection.clear();annSelection=new Set(['text1','arr1']);doc.groups=[{id:'group1',atoms:[],annotations:['text1','arr1'],integral:true}];tool='select';undoStack=[];");
const annotationsBefore=state();
get('canvas').handlers.pointerdown(event(450,300,{ctrlKey:true}));get('canvas').handlers.pointermove(event(500,400,{ctrlKey:true}));get('canvas').handlers.pointerup(event(500,400,{ctrlKey:true}));
assert.equal(state().annotations.length,4);assert.equal(state().groups.length,2);assert.equal(new Set(state().annotations.map(a=>a.id)).size,4);assert.deepEqual(state().annotations.slice(0,2),annotationsBefore.annotations);
assert.equal(state().annotations[3].x2,550);assert.equal(state().annotations[3].y2,400);
evaluate("action('undo')");assert.deepEqual(state(),annotationsBefore);
console.log('PASS: Ctrl-drag/Shift+Ctrl-drag duplication, threshold, original preservation, independent IDs/groups/annotations, unchanged clipboard, cancel and one Undo.');
// Copying a Cp centroid preserves independent ligand membership.
evaluate("doc=ChemCore.blank();selection.clear();annSelection.clear();placeCpAnion({x:300,y:300});selection=new Set(doc.atoms.map(a=>a.id));tool='select';zoom=1;undoStack=[];");
const cpOriginal=state();
get('canvas').handlers.pointerdown(event(300,300,{ctrlKey:true}));get('canvas').handlers.pointermove(event(450,350,{ctrlKey:true}));get('canvas').handlers.pointerup(event(450,350,{ctrlKey:true}));
assert.equal(state().ligands.length,2);assert.notEqual(state().ligands[0].centroidId,state().ligands[1].centroidId);assert.deepEqual(state().atoms.slice(0,cpOriginal.atoms.length),cpOriginal.atoms);assert.equal(new Set(state().ligands.flatMap(l=>l.atomIds)).size,10);
evaluate("action('undo')");assert.deepEqual(state(),cpOriginal);
console.log('PASS: Ctrl-drag Cp duplication retains independent ligand and centroid identities.');

// Native bridge owns copy; the canvas must not substitute its internal clipboard.
const dispatched=[];testctx.window.ErezDesktop={dispatch:name=>{dispatched.push(name);return name==='copy'}};
evaluate("clipboard={nativeSentinel:true};pointerOnCanvas=false;");
documentHandlers.keydown.at(-1)(keyEvent('c',{ctrlKey:true}));
assert.deepEqual(dispatched,['copy']);assert.equal(evaluate('clipboard.nativeSentinel'),true);
assert.equal(evaluate("handleChemDrawKey(keyEvent('Delete'))"),false);
delete testctx.window.ErezDesktop;
console.log('PASS: keyboard Copy dispatches once to the native host; selected-object Delete is not swallowed by atom-label hotkeys.');

// Switching tools mid-copy cancels the preview and restores actual selection IDs.
for (const annotations of [false,true]) {
 evaluate("gesture=null;doc=ChemCore.blank();selection.clear();annSelection.clear();undoStack=[];redoStack=[];tool='select';zoom=1;showCrosshair=false;showRulers=false;");
 if(annotations)evaluate("doc.annotations=[{id:'cancel-text',type:'text',x:100,y:100,text:'Label'}];annSelection=new Set(['cancel-text']);");
 else evaluate("const ca=addAtom({x:100,y:100}),cb=addAtom({x:140,y:100});addBond(ca,cb);selection=new Set([ca.id,cb.id]);");
 const before=state(), selected=evaluate('JSON.stringify([[...selection],[...annSelection]])');
 get('canvas').handlers.pointerdown(event(100,100,{ctrlKey:true}));
 get('canvas').handlers.pointermove(event(200,180,{ctrlKey:true}));
 assert.equal(evaluate('gesture.copied'),true);
 documentHandlers.keydown.at(-1)(keyEvent('1'));
 assert.equal(evaluate('tool'),'single');assert.equal(evaluate('gesture'),null);
 assert.deepEqual(state(),before);assert.equal(evaluate('JSON.stringify([[...selection],[...annSelection]])'),selected);
 get('canvas').handlers.pointerup(event(200,180));
 assert.deepEqual(state(),before);assert.equal(evaluate('undoStack.length'),0);
 evaluate("action('delete')");assert.equal(state().atoms.length+state().annotations.length,0);
 evaluate("action('undo')");assert.deepEqual(state(),before);
}
console.log('PASS: tool changes during duplicate drags restore molecule/caption selections, preserve undo history and cancel later release.');
