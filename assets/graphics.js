/* Original ErezDraw pen, orbital and table drawing objects. */
function isGraphic(a){return ['pen','orbital','table'].includes(a.type)}
function validateGraphic(a,finite){
 if(!finite(a.x)||!finite(a.y)||!finite(a.angle||0))throw Error('Invalid graphic position.');
 if(a.type==='pen'){
  if(!Array.isArray(a.points)||a.points.length<1||a.points.length>2000||a.points.some(p=>!finite(p.x)||!finite(p.y)||!finite(p.hx||0)||!finite(p.hy||0)))throw Error('Invalid curve points.');
  if(typeof a.closed!=='boolean'||!['none','gray','black'].includes(a.fill)||!['none','start','end','both'].includes(a.heads)||!finite(a.lineWidth)||a.lineWidth<=0||a.lineWidth>20)throw Error('Invalid curve style.');
 }else{
  if(!finite(a.width)||!finite(a.height)||a.width<=0||a.height<=0||a.width>10000||a.height>10000)throw Error('Invalid graphic size.');
  if(a.type==='orbital'&&(!['s','p','dxy','dz2','hybrid'].includes(a.kind)||!['outline','gray','phase'].includes(a.fill)))throw Error('Invalid orbital.');
  if(a.type==='table'){
   if(!Number.isInteger(a.rows)||!Number.isInteger(a.cols)||a.rows<1||a.cols<1||a.rows>30||a.cols>20||!Array.isArray(a.cells)||a.cells.length!==a.rows*a.cols||a.cells.some(c=>typeof c!=='string'||c.length>500))throw Error('Invalid table.');if(a.cellObjects!==undefined){if(!Array.isArray(a.cellObjects)||a.cellObjects.length!==a.rows*a.cols)throw Error('Invalid table drawings.');for(const f of a.cellObjects)if(f){if(f.atoms.length>300||f.annotations.some(a=>a.type==='table'))throw Error('Nested tables or oversized cell drawings are not supported.');ChemCore.validate({format:'chemsketch-classic',version:1,name:'Cell',...f});}}
  }
 }
 return JSON.parse(JSON.stringify(a));
}
function graphicPoint(a,p){const t=(a.angle||0)*Math.PI/180;return {x:a.x+p.x*Math.cos(t)-p.y*Math.sin(t),y:a.y+p.x*Math.sin(t)+p.y*Math.cos(t)}}
function graphicLocal(a,p){const t=-(a.angle||0)*Math.PI/180,x=p.x-a.x,y=p.y-a.y;return {x:x*Math.cos(t)-y*Math.sin(t),y:x*Math.sin(t)+y*Math.cos(t)}}
function penSamples(a){const out=[];if(!a.points.length)return out;out.push(a.points[0]);const count=a.closed?a.points.length:a.points.length-1;for(let i=0;i<count;i++){const p=a.points[i],q=a.points[(i+1)%a.points.length],c1={x:p.x+(p.hx||0),y:p.y+(p.hy||0)},c2={x:q.x-(q.hx||0),y:q.y-(q.hy||0)};for(let k=1;k<=24;k++){const t=k/24,u=1-t;out.push({x:u*u*u*p.x+3*u*u*t*c1.x+3*u*t*t*c2.x+t*t*t*q.x,y:u*u*u*p.y+3*u*u*t*c1.y+3*u*t*t*c2.y+t*t*t*q.y})}}return out}
function graphicBounds(a){const pts=a.type==='pen'?penSamples(a).map(p=>graphicPoint(a,p)):[{x:0,y:0},{x:a.width,y:0},{x:a.width,y:a.height},{x:0,y:a.height}].map(p=>graphicPoint(a,p));return ErezGeometry.bounds(pts,5)}
function graphicHit(a,p){if(a.type==='pen'){const pts=penSamples(a).map(q=>graphicPoint(a,q));return pts.length===1?ChemCore.dist(p,pts[0])<8/zoom:pts.slice(1).some((q,i)=>ChemCore.segmentDistance(p,pts[i],q)<8/zoom)}const q=graphicLocal(a,p);return q.x>=-5/zoom&&q.y>=-5/zoom&&q.x<=a.width+5/zoom&&q.y<=a.height+5/zoom}
function penPath(a){let d=`M${a.points[0].x} ${a.points[0].y}`;const count=a.closed?a.points.length:a.points.length-1;for(let i=0;i<count;i++){const p=a.points[i],q=a.points[(i+1)%a.points.length];d+=` C${p.x+(p.hx||0)} ${p.y+(p.hy||0)} ${q.x-(q.hx||0)} ${q.y-(q.hy||0)} ${q.x} ${q.y}`}return d+(a.closed?' Z':'')}
function drawGraphic(parent,a){const g=sv('g',{transform:`translate(${a.x} ${a.y}) rotate(${a.angle||0})`});parent.append(g);
 if(a.type==='pen'){
  g.append(sv('path',{d:penPath(a),fill:a.fill==='none'?'none':a.fill==='gray'?'#aaa':'#151b20',stroke:'#151b20','stroke-width':a.lineWidth,'stroke-dasharray':a.dashed?'5 4':'none','stroke-linejoin':'round'}));
  const pts=penSamples(a);const head=(p,q)=>{const t=Math.atan2(p.y-q.y,p.x-q.x);for(const v of [-.42,.42])line(g,p.x,p.y,p.x-10*Math.cos(t+v),p.y-10*Math.sin(t+v),{'stroke-width':a.lineWidth})};
  if(!a.closed&&pts.length>1){if(['start','both'].includes(a.heads))head(pts[0],pts[1]);if(['end','both'].includes(a.heads))head(pts.at(-1),pts.at(-2))}
 }else if(a.type==='orbital'){
  const w=a.width,h=a.height,cx=w/2,cy=h/2;
  const lobe=(angle,phase,length=w*.48,breadth=h*.29)=>{const lg=sv('g',{transform:`translate(${cx} ${cy}) rotate(${angle})`});lg.append(sv('path',{d:`M0 0 C${length*.45} ${-breadth} ${length} ${-breadth} ${length} 0 C${length} ${breadth} ${length*.45} ${breadth} 0 0Z`,fill:a.fill==='phase'?(phase?'#151b20':'white'):a.fill==='gray'?'#aaa':'white',stroke:'#151b20','stroke-width':1.5}));g.append(lg)};
  if(a.kind==='s')g.append(sv('ellipse',{cx,cy,rx:w/2,ry:h/2,fill:a.fill==='phase'?'#151b20':a.fill==='gray'?'#aaa':'white',stroke:'#151b20','stroke-width':1.5}));
  else if(a.kind==='p'){lobe(0,true);lobe(180,false)}
  else if(a.kind==='hybrid'){lobe(0,true);lobe(180,false,w*.19,h*.17)}
  else if(a.kind==='dxy'){for(let i=0;i<4;i++)lobe(45+i*90,i%2===0,Math.min(w,h)*.45,Math.min(w,h)*.18)}
  else{lobe(90,true,h*.47,w*.2);lobe(270,true,h*.47,w*.2);g.append(sv('ellipse',{cx,cy,rx:w*.43,ry:h*.12,fill:a.fill==='gray'?'#aaa':'white',stroke:'#151b20','stroke-width':1.5}))}
 }else{
  const cw=a.width/a.cols,ch=a.height/a.rows;
  for(let r=0;r<=a.rows;r++)line(g,0,r*ch,a.width,r*ch);
  for(let c=0;c<=a.cols;c++)line(g,c*cw,0,c*cw,a.height);
  for(let r=0;r<a.rows;r++)for(let c=0;c<a.cols;c++){const fragment=a.cellObjects?.[r*a.cols+c];if(fragment){const saved=doc;try{doc={...ChemCore.blank(),...fragment};const bounds=drawingBounds();if(bounds){const scale=Math.min((cw-10)/(bounds.x2-bounds.x),(ch-10)/(bounds.y2-bounds.y)),content=sv('g',{transform:`translate(${c*cw+5} ${r*ch+5}) scale(${scale}) translate(${-bounds.x} ${-bounds.y})`});content.append(drawingGroup(false));g.append(content)}}finally{doc=saved}continue}const text=a.cells[r*a.cols+c],size=Math.min(a.textStyle?.size||14,ch*.65);const node=sv('text',{x:c*cw+5,y:r*ch+size+4,'font-size':size,'font-family':a.textStyle?.font||'Arial',fill:a.textStyle?.color||'#151b20'});for(const [i,line] of text.split('\n').entries())node.append(sv('tspan',{x:c*cw+5,...(i?{dy:size*1.2}:{})},line));g.append(node)}
 }
}
let penActive=null,penNodeIndex=0,curveStyle={closed:false,fill:'none',heads:'none',lineWidth:1.7,dashed:false},nativeGraphicRequest=null;
function makeGraphic(g){const p=g.p,q=g.end;
 if(g.graphicTool==='pen'){let a=penActive&&doc.annotations.find(a=>a.id===penActive);if(!a){a={id:id('curve'),type:'pen',x:p.x,y:p.y,angle:0,points:[],...curveStyle};doc.annotations.push(a);penActive=a.id}const local=graphicLocal(a,p),handle=graphicLocal(a,q);a.points.push({...local,hx:handle.x-local.x,hy:handle.y-local.y});penNodeIndex=a.points.length-1;return a}
 const orbital=g.graphicTool.startsWith('orbital'),kind=g.graphicTool.split('_')[1]||'p',w=orbital?Math.max(30,ChemCore.dist(p,q)*2):Math.max(120,Math.abs(q.x-p.x)),h=orbital?w:Math.max(70,Math.abs(q.y-p.y));
 const a=orbital?{id:id('orb'),type:'orbital',x:p.x-w/2,y:p.y-h/2,width:w,height:h,angle:Math.atan2(q.y-p.y,q.x-p.x)*180/Math.PI,kind,fill:g.graphicTool.split('_')[2]||'phase'}:{id:id('table'),type:'table',x:Math.min(p.x,q.x),y:Math.min(p.y,q.y),width:w,height:h,angle:0,rows:3,cols:3,cells:Array(9).fill(''),textStyle:{...textStyle}};
 // Rotate orbital about its node rather than its upper-left corner.
 if(orbital){const t=a.angle*Math.PI/180;a.x=p.x-w/2*Math.cos(t)+h/2*Math.sin(t);a.y=p.y-w/2*Math.sin(t)-h/2*Math.cos(t)}doc.annotations.push(a);return a;
}
function curveCommand(change){const before=snapshot();const curves=doc.annotations.filter(a=>annSelection.has(a.id)&&a.type==='pen');curveStyle={...curveStyle,...change};for(const a of curves)Object.assign(a,change);commit(before);render()}
function curvePointCommand(remove=false){const a=doc.annotations.find(a=>annSelection.has(a.id)&&a.type==='pen');if(!a)return;const before=snapshot();if(remove){if(a.points.length<=2)return;a.points.splice(Math.min(penNodeIndex,a.points.length-1),1)}else{const i=Math.min(penNodeIndex,a.points.length-2),p=a.points[i],q=a.points[i+1];a.points.splice(i+1,0,{x:(p.x+q.x)/2,y:(p.y+q.y)/2,hx:0,hy:0});penNodeIndex=i+1}commit(before)}
function curveHandles(){const g=sv('g',{'data-editing-guides':true});if(tool!=='pen')return g;for(const a of doc.annotations.filter(a=>annSelection.has(a.id)&&a.type==='pen'))for(let i=0;i<a.points.length;i++){const p=a.points[i];for(const sign of [-1,1]){const q=graphicPoint(a,{x:p.x+sign*(p.hx||0),y:p.y+sign*(p.hy||0)}),o=graphicPoint(a,p);line(g,o.x,o.y,q.x,q.y,{stroke:'#777','stroke-width':1/zoom});g.append(sv('circle',{cx:q.x,cy:q.y,r:3/zoom,fill:'white',stroke:'#555'}))}const o=graphicPoint(a,p);g.append(sv('rect',{x:o.x-3/zoom,y:o.y-3/zoom,width:6/zoom,height:6/zoom,fill:'white',stroke:'black'}))}return g}
function curveHandleHit(p){for(const a of doc.annotations.filter(a=>annSelection.has(a.id)&&a.type==='pen'))for(let i=0;i<a.points.length;i++){const q=a.points[i];for(const sign of [1,-1])if(Math.hypot(q.hx||0,q.hy||0)>3/zoom&&ChemCore.dist(p,graphicPoint(a,{x:q.x+sign*(q.hx||0),y:q.y+sign*(q.hy||0)}))<6/zoom)return {a,index:i,sign};if(ChemCore.dist(p,graphicPoint(a,q))<6/zoom)return {a,index:i,sign:0}}return null}
