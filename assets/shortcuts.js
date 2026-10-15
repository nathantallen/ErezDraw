/* ChemDraw 17 manual, chapter 5, pp. 51–61. Shared engine shortcuts. */
const ErezShortcuts = {
  resolve(e) {
    const key=e.key.length===1?e.key.toLowerCase():e.key;
    const mod=e.ctrlKey||e.metaKey;
    const prefix=(mod?'Ctrl+':'')+(e.altKey?'Alt+':'')+(e.shiftKey?'Shift+':'');
    return this.commands[prefix+key] || null;
  },
  commands: {
    'Ctrl+n':'new','Ctrl+o':'open','Ctrl+s':'save','Ctrl+Shift+s':'saveas',
    'Ctrl+p':'print','Ctrl+Shift+p':'pageSetup','Ctrl+w':'close',
    'Ctrl+z':'undo','Ctrl+Shift+z':'redo','Ctrl+y':'repeat',
    'Ctrl+x':'cut','Ctrl+c':'copy','Ctrl+v':'paste','Ctrl+a':'selectAll',
    'F5':'actual','F6':'fitWindow','F7':'zoomIn','F8':'zoomOut','F11':'rulers',
    'Ctrl+l':'fixedLengths','Ctrl+e':'fixedAngles','Ctrl+g':'group','Ctrl+Shift+g':'ungroup',
    'Ctrl+r':'rotateDialog','Ctrl+k':'scaleObjects','Ctrl+Shift+h':'flip','Ctrl+Shift+v':'flipVertical',
    'Ctrl+Alt+Shift+l':'align_left','Ctrl+Alt+Shift+c':'align_horizontal','Ctrl+Alt+Shift+r':'align_right',
    'Ctrl+Alt+Shift+t':'align_top','Ctrl+Alt+Shift+m':'align_vertical','Ctrl+Alt+Shift+b':'align_bottom',
    'Ctrl+Shift+k':'cleanup','Ctrl+Shift+n':'nameToStructure','Ctrl+Alt+n':'structureToName',
    'Ctrl+Shift+l':'textLeft','Ctrl+Shift+c':'textCenter','Ctrl+Shift+r':'textRight','Ctrl+Shift+j':'textJustify',
    'Ctrl+t':'plain','Ctrl+b':'bold','Ctrl+i':'italic','Ctrl+u':'underline','Ctrl+f':'formula',
    'F9':'subscript','F10':'superscript','Ctrl+Alt+Tab':'lassoToggle'
  },
  labels:{f:'F',p:'P',P:'Ph',A:'Ac',h:'H',b:'Br',B:'B',i:'I',r:'R',k:'K',s:'S',S:'Si',m:'Me',n:'N',w:'N',N:'Na',c:'C',C:'Cl',l:'Cl',x:'X',o:'O',q:'O',d:'D',e:'Et',E:'COOCH3'},
  tools:{' ':'select',x:'single',X:'chain',t:'text',T:'bracket',e:'arrow',E:'chargeUp',j:'benzene',J:'cyclopentadiene',u:'ring6',U:'ring5',G:'orbital_p_phase',l:'pen',L:'elements',k:'fragment'},
};
let keyboardRepeat=null,keyboardPreviousTool='single';
function keyboardCommand(name) {
  const host=window.ErezWeb?.keyboardCommand;
  if(host&&host(name))return true;
  const alignment={textLeft:'left',textCenter:'center',textRight:'right',textJustify:'justify'};
  if(alignment[name]){paragraphStyle({alignment:alignment[name]});return true}
  if(name.startsWith('align_')){objectAlign(name.slice(6));return true}
  if(['bold','italic','underline'].includes(name)){setTextStyle({[name]:!activeTextStyle()[name]});return true}
  if(name==='plain'){setTextStyle({plain:true});return true}
  if(name==='formula'){formatFormula();return true}
  if(name==='subscript'||name==='superscript'){setTextStyle({script:name==='subscript'?'sub':'super'});return true}
  if(name==='fixedLengths'||name==='fixedAngles'){if(name==='fixedLengths')fixedLengths=!fixedLengths;else fixedAngles=!fixedAngles;render();return true}
  if(name==='rulers'){showRulers=!showRulers;render();return true}
  if(name==='group'){groupSelection();return true}if(name==='ungroup'){ungroupSelection();return true}
  if(name==='flipVertical'){flipSelection(true);keyboardRepeat=()=>flipSelection(true);return true}
  if(name==='flip'){flipSelection();keyboardRepeat=()=>flipSelection();return true}
  if(name==='repeat'){if(keyboardRepeat)keyboardRepeat();else notify('No repeatable keyboard command yet.');return true}
  if(name==='rotateDialog'){nativeRotateRequest=true;return true}if(name==='scaleObjects'){nativeScaleRequest=true;return true}
  if(name==='lassoToggle'){const next=tool==='lasso'?keyboardPreviousTool:'lasso';if(tool!=='lasso')keyboardPreviousTool=tool;setTool(next);return true}
  if(['new','open','save','print','undo','redo','cut','copy','paste','selectAll','actual','zoomIn','zoomOut'].includes(name)){action(name);return true}
  if(name==='fitWindow'){const p=doc.pageSettings||{width:816,height:1056,margin:48};center={x:p.width/2-p.margin,y:p.height/2-p.margin};zoomTo(Math.min(canvas.clientWidth/p.width,canvas.clientHeight/p.height)*.95);return true}
  notify('Use the '+name+' menu command in the desktop app.');return true;
}
function chemicalHotkey(e) {
  if(e.ctrlKey||e.metaKey||e.altKey||e.isComposing||gesture)return false;
  const h=pointerOnCanvas?hit(lastPointer):null,key=e.key;
  if(h?.kind==='atom'){
    const a=h.item;
    if(key==='Enter'){edit(a,'atom');return true}
    if(key==='Delete'||key==='Backspace'||key===' '){const before=snapshot();a.label='C';delete a.textRuns;commit(before);return true}
    if(ErezShortcuts.labels[key]){const before=snapshot();a.label=ErezShortcuts.labels[key];delete a.textRuns;commit(before);return true}
    if(key==='+'||key==='-'){const before=snapshot();a.chargeMode='manual';a.charge=Math.max(-20,Math.min(20,(a.charge||0)+(key==='+'?1:-1)));commit(before);return true}
    if(['0','1','4','5','8','9','z'].includes(key)){
      const before=snapshot(),end=endpoint(a,a,true),b=addAtom(end);addBond(a,b,key==='8'?2:key==='z'?3:1,key==='4'?'wedge':key==='5'?'hash':'normal');
      if(key==='9'){const c=addAtom(endpoint(a,a,true));addBond(a,c)}selection=new Set([b.id]);annSelection.clear();commit(before);return true;
    }
    if(['3','a','6','7'].includes(key)){placeRing(a,key==='7'?5:6,key==='3'||key==='a');return true}
    return false;
  }
  if(h?.kind==='bond'){
    const b=h.item,styles={'1':[1,'normal'],'2':[2,'normal'],'3':[3,'normal'],d:[1,'dashed'],b:[1,'boldBond'],B:[2,'boldBond'],y:[1,'wavy'],w:[1,'wedge'],h:[1,'hash'],H:[1,'hashed']};
    if(styles[key]){const before=snapshot();[b.order,b.style]=styles[key];commit(before);return true}
    if(['l','c','r'].includes(key)){const before=snapshot();b.order=2;b.doublePosition={l:'left',c:'center',r:'right'}[key];commit(before);return true}
    if(['a','v','4','5','6','7','8'].includes(key)){placeRing(lastPointer,key==='v'?3:key==='a'?6:Number(key),key==='a');return true}
    return false;
  }
  if(key==='k'){window.ErezWeb?.massSpectrum?window.ErezWeb.massSpectrum():notify('Use Structure > Mass Spectrometry Fragmentation.');return true}
  if(ErezShortcuts.tools[key]){setTool(ErezShortcuts.tools[key]);return true}
  return false;
}
function handleChemDrawKey(e) {
  if(e.isComposing||document.querySelector('dialog[open]'))return false;
  const input=e.target?.isContentEditable||['INPUT','TEXTAREA','SELECT'].includes(e.target?.tagName);
  const command=ErezShortcuts.resolve(e);
  const textCommands=['bold','italic','underline','plain','formula','subscript','superscript','textLeft','textCenter','textRight','textJustify'];
  if(input&&!(editing&&textCommands.includes(command)))return false;
  if(command){keyboardCommand(command);return true}
  return !input&&chemicalHotkey(e);
}
window.ErezShortcuts=ErezShortcuts;
