const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const ctx={doc:{atoms:[],bonds:[]},ChemCore:{atom:(d,id)=>d.atoms.find(a=>a.id===id),connected(d,id){const ids=new Set([id]);let size;do{size=ids.size;for(const b of d.bonds)if(ids.has(b.a)||ids.has(b.b)){ids.add(b.a);ids.add(b.b)}}while(ids.size!==size);return ids}}};
vm.createContext(ctx);vm.runInContext(fs.readFileSync('assets/charges.js','utf8'),ctx);
const atom=(id,label,extra={})=>({id,label,charge:0,...extra});
const bond=(a,b,style='normal')=>({id:a+'-'+b,a,b,order:1,style});
const update=()=>vm.runInContext('updateBondCharges()',ctx);
function amides(style='normal'){
 ctx.doc={atoms:[],bonds:[]};
 for(let i=0;i<3;i++){ctx.doc.atoms.push(atom('n'+i,'N'),atom('s'+i,'Si'),atom('t'+i,'Si'));ctx.doc.bonds.push(bond('n'+i,'s'+i),bond('n'+i,'t'+i))}
 update();assert(ctx.doc.atoms.every(a=>a.charge===0));
 ctx.doc.atoms.push(atom('m','C'));
 for(let i=0;i<3;i++)ctx.doc.bonds.push(bond('n'+i,'m',style));
 update();const metal=ctx.doc.atoms.at(-1);metal.label='La';update();
 assert.equal(metal.charge,3,'La added after drawing three HMDS donors');
 assert.equal(ctx.doc.atoms.filter(a=>a.label==='N').reduce((s,a)=>s+a.charge,0),-3);
 assert.equal(ctx.doc.atoms.reduce((s,a)=>s+a.charge,0),0);
 update();assert.equal(metal.charge,3,'Stable on subsequent updates');
 return metal;
}
for(const style of ['normal','coord']){
 let metal=amides(style);metal.complexCharge=1;update();assert.equal(metal.charge,4);
 metal.charge=2;metal.chargeMode='manual';update();assert.equal(metal.charge,2);
 metal=amides(style);ctx.doc.bonds=ctx.doc.bonds.filter(b=>b.id!=='n2-m');update();assert.equal(metal.charge,2);
 ctx.doc.bonds=ctx.doc.bonds.filter(b=>b.a!=='m'&&b.b!=='m');update();assert.equal(metal.charge,0);
}
// An explicit N-H keeps a secondary amine neutral. A tertiary donor is neutral.
for(const label of ['H','C']){ctx.doc={atoms:[atom('m','La'),atom('n','N'),atom('a','C'),atom('b','C'),atom('h',label)],bonds:[bond('n','m','coord'),bond('n','a'),bond('n','b'),bond('n','h')]};update();assert.equal(ctx.doc.atoms[1].charge,0);assert.equal(ctx.doc.atoms[0].charge,0)}
ctx.doc={atoms:[atom('m','La'),atom('n','N',{explicitHs:1}),atom('a','C'),atom('b','C')],bonds:[bond('n','m','coord'),bond('n','a'),bond('n','b')]};update();assert.equal(ctx.doc.atoms[0].charge,0);
// Preserve a manual neutral donor and explicit ligand/metal charges.
let metal=amides();ctx.doc.atoms[0].charge=0;ctx.doc.atoms[0].chargeMode='manual';update();assert.equal(metal.charge,2);
// Alkoxide versus neutral ether.
for(const count of [1,2]){ctx.doc={atoms:[atom('m','La'),atom('o','O'),atom('a','C'),atom('b','C')],bonds:[bond('o','m','coord'),bond('o','a'),...(count===2?[bond('o','b')]:[])]};update();assert.equal(ctx.doc.atoms[0].charge,count===1?1:0)}
// Shared anionic ligands do not assign the whole charge to both metals.
amides();ctx.doc.atoms.push(atom('m2','La'));ctx.doc.bonds.push(bond('n0','m2'));update();assert.equal(ctx.doc.atoms.find(a=>a.id==='m').charge,0);
console.log('PASS: draw ligands before metal; covalent/coordination attachments; La(HMDS)3 charge +3; neutral amines/ethers; explicit hydrogens; manual overrides; complex charge; ligand removal; multimetal ambiguity.');
