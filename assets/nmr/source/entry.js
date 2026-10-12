import OCLE from 'openchemlib-extended';
import query from 'nmr-predictor/lib/queryByHose';
import proton from './h1.json';
import carbon from './nmrshiftdb2-13c.json';
export function predict(molfile,nucleus){
 const mol=OCLE.Molecule.fromMolfile(molfile),label=nucleus==='1H'?'H':'C';
 if(label==='H')mol.addImplicitHydrogens();
 const neighbors={};for(let b=0;b<mol.getAllBonds();b++){const a=mol.getBondAtom(0,b),c=mol.getBondAtom(1,b);(neighbors[a]??=[]).push(c);(neighbors[c]??=[]).push(a)}
 const options={atomLabel:label,ignoreLabile:false,use:'median',levels:[5,4,3,2]};
 const model={diaId:mol.getGroupedDiastereotopicAtomIDs()};
 for(const group of model.diaId)group.hose=OCLE.Util.getHoseCodesFromDiastereotopicID(group.oclID,{maxSphereSize:5,type:0});
 const result=(query.default||query)(model,label==='H'?proton:carbon,options),groups=new Map();
 for(const row of result){const key=row.diaIDs[0];if(!groups.has(key))groups.set(key,{delta:Number.isFinite(row.delta)?row.delta:null,count:0,atoms:[],attachedAtoms:[],matches:row.ncs||0,level:row.level||0,std:row.std,min:row.min,max:row.max});const group=groups.get(key);group.count++;for(const i of row.atomIDs){group.atoms.push(i);if(label==='H'){for(const neighbor of neighbors[i]||[]){if(!group.attachedAtoms.includes(neighbor))group.attachedAtoms.push(neighbor)}}else group.attachedAtoms.push(i)}}
 return [...groups.values()].sort((a,b)=>(b.delta??-999)-(a.delta??-999));
}
