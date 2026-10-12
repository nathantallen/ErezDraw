/* ErezDraw geometry adapters.
 * Portions adapted from ChemCanvas bond.py, atom.py and geometry.py,
 * copyright (C) 2022–2026 Arindam Chaudhuri; see THIRD-PARTY-NOTICES.md.
 * SPDX-License-Identifier: GPL-3.0-or-later
 */
'use strict';
const ErezGeometry=(()=>{
 const epsilon=1e-8;
 const distance=(a,b)=>Math.hypot(b.x-a.x,b.y-a.y);
 const cross=(a,b)=>a.x*b.y-a.y*b.x;
 const side=(a,b,p)=>Math.sign(cross({x:b.x-a.x,y:b.y-a.y},{x:p.x-a.x,y:p.y-a.y}));
 const rotate=(p,c,angle)=>({x:c.x+(p.x-c.x)*Math.cos(angle)-(p.y-c.y)*Math.sin(angle),y:c.y+(p.x-c.x)*Math.sin(angle)+(p.y-c.y)*Math.cos(angle)});
 function intersection(a,b,c,d){const r={x:b.x-a.x,y:b.y-a.y},s={x:d.x-c.x,y:d.y-c.y},den=cross(r,s);if(Math.abs(den)<epsilon)return null;const t=cross({x:c.x-a.x,y:c.y-a.y},s)/den;return {x:a.x+t*r.x,y:a.y+t*r.y,t}}
 function boxExit(a,b,box,padding=0){if(!box)return a;const rect={x:box.x-padding,y:box.y-padding,x2:box.x2+padding,y2:box.y2+padding};const dx=b.x-a.x,dy=b.y-a.y;let lo=0,hi=1;for(const [value,delta,min,max] of [[a.x,dx,rect.x,rect.x2],[a.y,dy,rect.y,rect.y2]]){if(Math.abs(delta)<epsilon){if(value<min||value>max)return a;continue}let t1=(min-value)/delta,t2=(max-value)/delta;if(t1>t2)[t1,t2]=[t2,t1];lo=Math.max(lo,t1);hi=Math.min(hi,t2);if(lo>hi)return a}return hi>=0&&hi<=1?{x:a.x+hi*dx,y:a.y+hi*dy}:a}
 function clippedSegment(a,b,boxA,boxB,padding=2){const start=boxExit(a,b,boxA,padding),end=boxExit(b,a,boxB,padding);const direction={x:b.x-a.x,y:b.y-a.y};if((end.x-start.x)*direction.x+(end.y-start.y)*direction.y<=epsilon)return null;return {x1:start.x,y1:start.y,x2:end.x,y2:end.y}}
 function offsetSegment(seg,offset){const len=Math.hypot(seg.x2-seg.x1,seg.y2-seg.y1)||1,nx=-(seg.y2-seg.y1)/len,ny=(seg.x2-seg.x1)/len;return {x1:seg.x1+nx*offset,y1:seg.y1+ny*offset,x2:seg.x2+nx*offset,y2:seg.y2+ny*offset}}
 function shortenAgainstNeighbors(seg,a,b,offset,neighborsA,neighborsB,ratio=.75){const out={...offsetSegment(seg,offset)},dx=out.x2-out.x1,dy=out.y2-out.y1,k=(1-ratio)/2;out.x1+=dx*k;out.y1+=dy*k;out.x2-=dx*k;out.y2-=dy*k;const sign=side(a,b,{x:out.x1,y:out.y1}),length=distance(a,b);for(const [atom,other,neighbors,start] of [[a,b,neighborsA,true],[b,a,neighborsB,false]])for(const n of neighbors){if(side(a,b,n)!==sign)continue;const neighborLine=offsetSegment({x1:atom.x,y1:atom.y,x2:n.x,y2:n.y},k*length*side(atom,n,other));const p=intersection({x:out.x1,y:out.y1},{x:out.x2,y:out.y2},{x:neighborLine.x1,y:neighborLine.y1},{x:neighborLine.x2,y:neighborLine.y2});if(p&&p.t>0&&p.t<1){if(start){out.x1=p.x;out.y1=p.y}else{out.x2=p.x;out.y2=p.y}}}return out}
 function bounds(points,padding=0){return {x:Math.min(...points.map(p=>p.x))-padding,y:Math.min(...points.map(p=>p.y))-padding,x2:Math.max(...points.map(p=>p.x))+padding,y2:Math.max(...points.map(p=>p.y))+padding}}
 function markAngles(occupied,count){const tau=Math.PI*2;let angles=occupied.map(v=>((v%tau)+tau)%tau).sort((a,b)=>a-b);const result=[];if(!angles.length&&count){result.push(-Math.PI/2);angles=[Math.PI*1.5];count--}const gaps=angles.map((a,i)=>({start:a,gap:((angles[(i+1)%angles.length]||0)+(i===angles.length-1?tau:0))-a,n:0}));while(count-->0){const gap=gaps.reduce((best,g)=>g.gap/(g.n+1)>best.gap/(best.n+1)?g:best);gap.n++}for(const gap of gaps)for(let i=1;i<=gap.n;i++)result.push(gap.start+i*gap.gap/(gap.n+1));return result.sort((a,b)=>Math.sin(a)-Math.sin(b))}
 function markPosition(center,box,angle,gap){const ray={x:center.x+Math.cos(angle)*10000,y:center.y+Math.sin(angle)*10000};const edge=box?boxExit(center,ray,box):center;const dist=distance(center,edge)+gap;return {x:center.x+Math.cos(angle)*dist,y:center.y+Math.sin(angle)*dist,angle}}
 return {distance,side,rotate,intersection,boxExit,clippedSegment,offsetSegment,shortenAgainstNeighbors,bounds,markAngles,markPosition};
})();
