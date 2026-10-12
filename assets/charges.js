/* Conservative drawing charge rules, with explicit manual overrides. */
const drawingMetals=new Set('Li Be Na Mg Al K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv'.split(' '));
function updateBondCharges(){
 const neighbors=a=>doc.bonds.filter(b=>b.a===a.id||b.b===a.id).map(b=>({b,a:ChemCore.atom(doc,b.a===a.id?b.b:b.a)}));
 for(const a of doc.atoms){if(a.nodeType==='centroid'||drawingMetals.has(a.label)||a.chargeMode==='manual'||a.charge&&a.chargeMode!=='auto')continue;
  const ns=neighbors(a),organic=ns.filter(n=>!drawingMetals.has(n.a.label)&&n.b.style!=='coord'),v=organic.reduce((s,n)=>s+(n.b.order===4?1.5:n.b.order),0)+(a.explicitHs||0),metal=ns.some(n=>drawingMetals.has(n.a.label));let charge=null;
  if(a.label==='N'&&v===4)charge=1;else if(a.label==='O'&&v===3)charge=1;else if(a.label==='B'&&v===4)charge=-1;else if(a.label==='P'&&v===4&&organic.every(n=>n.b.order===1))charge=1;
  // Ionic ligand representation: bare two-coordinate N is amido, not a
  // neutral amine with an invented implicit H. Explicit N-H bonds / H counts
  // keep amines neutral; three-coordinate donors are also neutral.
  else if(metal&&a.label==='N'&&v===2&&!a.radical&&organic.every(n=>n.b.order===1))charge=-1;
  else if(metal&&['O','S'].includes(a.label)&&v===1&&!a.radical&&organic.every(n=>n.b.order===1))charge=-1;
  else if(metal&&['F','Cl','Br','I','H'].includes(a.label)&&organic.length===0)charge=-1;
  else if(a.chargeMode==='auto')charge=0;
  if(charge!==null){a.charge=charge;a.chargeMode='auto'}
 }
 // Only a single metal with recognized ionic ligand charges can be balanced.
 const visited=new Set();for(const metal of doc.atoms.filter(a=>drawingMetals.has(a.label))){if(visited.has(metal.id))continue;const ids=ChemCore.connected(doc,metal.id),atoms=doc.atoms.filter(a=>ids.has(a.id));for(const id of ids)visited.add(id);const metals=atoms.filter(a=>drawingMetals.has(a.label));if(metals.length!==1){for(const m of metals)if(m.chargeMode==='auto')m.charge=0;continue}if(metal.chargeMode==='manual'||metal.charge&&metal.chargeMode!=='auto')continue;
  const attached=neighbors(metal);if(!attached.length){if(metal.chargeMode==='auto')metal.charge=0;continue}
  const charge=atoms.filter(a=>!drawingMetals.has(a.label)&&a.nodeType!=='centroid').reduce((s,a)=>s+a.charge,0);
  if(attached.some(n=>n.a.nodeType==='centroid')||charge!==0||metal.chargeMode==='auto'){metal.charge=(metal.complexCharge||0)-charge;metal.chargeMode='auto'}
 }
}
