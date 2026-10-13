/* Desktop command adapters. Document edits use the shared commit/undo pipeline. */
(() => {
  'use strict';
  const W = window.ErezWeb;
  const commands = new Map();
  let fieldId = 0;
  function el(tag, text=null, attrs={}) {
    const node=document.createElement(tag); if(text!==null) node.textContent=text;
    for(const [key,value] of Object.entries(attrs)) node.setAttribute(key,value);
    return node;
  }
  function modal(title, wide=false) {
    const d=el('dialog',null,{class:wide?'web-dialog web-wide':'web-dialog','aria-label':title});
    const head=el('header');head.append(el('h2',title));const close=el('button','Close',{type:'button'});head.append(close);d.append(head);
    const body=el('section');d.append(body);close.onclick=()=>d.close();d.addEventListener('close',()=>d.remove(),{once:true});document.body.append(d);
    return {dialog:d,body,open:()=>d.showModal()};
  }
  function fields(title, specs, submit='Apply', note='') {
    return new Promise(resolve=>{
      const m=modal(title), form=el('form',null);m.body.append(form);
      if(note) form.append(el('p',note));const controls={};
      for(const spec of specs){
        const label=el('label',spec.label,{class:'web-field'}),id='web-field-'+(++fieldId);label.htmlFor=id;
        const input=el(spec.type==='select'?'select':spec.type==='textarea'?'textarea':'input',null,{id});
        if(!['select','textarea'].includes(spec.type)) input.type=spec.type||'text';
        for(const key of ['min','max','step','maxLength','placeholder'])if(spec[key]!==undefined)input[key]=spec[key];
        if(spec.type==='select')for(const option of spec.options)input.add(new Option(Array.isArray(option)?option[1]:option,Array.isArray(option)?option[0]:option));
        if(spec.type==='checkbox')input.checked=Boolean(spec.value);else input.value=spec.value??(spec.type==='select'?input.options[0]?.value||'':'');
        if(spec.required)input.required=true;if(spec.readonly)input.readOnly=true;
        label.append(input);form.append(label);controls[spec.key]=input;
      }
      const footer=el('footer');const ok=el('button',submit,{type:'submit'}),cancel=el('button','Cancel',{type:'button'});footer.append(ok,cancel);form.append(footer);
      let answer=null;cancel.onclick=()=>m.dialog.close();
      form.onsubmit=event=>{event.preventDefault();answer={};for(const spec of specs){const input=controls[spec.key];answer[spec.key]=spec.type==='checkbox'?input.checked:spec.type==='number'?Number(input.value):input.value;}m.dialog.close();};
      m.dialog.addEventListener('close',()=>resolve(answer),{once:true});m.open();
    });
  }
  function ensureMenu(name){
    try{return W.menu(name);}catch{}
    const menu=el('div',null,{class:'menu'}),button=el('button',name),drop=el('div',null,{class:'dropdown'});menu.append(button,drop);
    document.querySelector('.menubar').insertBefore(menu,document.querySelector('.menubar .menu:last-child'));
    button.onclick=()=>{const open=menu.classList.contains('open');document.querySelectorAll('.menu').forEach(m=>m.classList.remove('open'));menu.classList.toggle('open',!open);};return drop;
  }
  function add(name,label,handler,{finish=true,replace=false}={}){
    const menu=ensureMenu(name);
    if(replace)for(const b of [...menu.querySelectorAll('button')])if(b.textContent.replace(/\s+/g,' ').trim()===label)b.remove();
    const button=el('button',label,{type:'button'});menu.append(button);
    if(!finish)button.onpointerdown=e=>{rememberTextSelection();e.preventDefault();};
    const run=async()=>{document.querySelectorAll('.menu').forEach(m=>m.classList.remove('open'));try{if(finish)finishEditing();await handler();}catch(error){W.show(label,error.message);}};
    button.onclick=run;commands.set(label,run);return button;
  }
  function transaction(update){const before=snapshot();try{update();doc=ChemCore.validate(doc);commit(before);}catch(error){doc=before;render();throw error;}}
  function current(){return JSON.stringify(doc);}
  function unchanged(snapshot){if(current()!==snapshot)throw Error('The drawing changed while processing. Run the command again.');}
  async function transform(op, extra={}){const saved=current(),r=await W.api(op,extra);unchanged(saved);transaction(()=>{doc=r.drawing;selection.clear();annSelection.clear();});return r;}
  function setAction(name,fn){document.querySelectorAll('[data-action="'+name+'"]').forEach(b=>b.onclick=fn);}
  function selectedAtom(){const atoms=doc.atoms.filter(a=>selection.has(a.id));if(atoms.length!==1||atoms[0].nodeType)throw Error('Select one chemical atom.');return atoms[0];}
  async function rotate(){if(!selection.size&&!annSelection.size)throw Error('Select objects to rotate.');const a=await fields('Rotate Objects',[
    {key:'degrees',label:'Angle (degrees)',type:'number',min:0,max:3600,step:.01,value:30},
    {key:'direction',label:'Direction',type:'select',options:[['1','Clockwise'],['-1','Counterclockwise']],value:'1'},
    {key:'labels',label:'Rotate atom labels',type:'checkbox',value:false}],'Rotate');if(a)rotateSelection(a.degrees*Number(a.direction),a.labels);}
  async function scale(){if(!selection.size&&!annSelection.size)throw Error('Select objects to scale.');const median=medianSelectedBond();const a=await fields('Scale Objects',[
    {key:'mode',label:'Scale mode',type:'select',options:[['percent','Percentage'],['fixed','To document bond length'],['median','To specified bond length']]},
    {key:'percent',label:'Scale (%)',type:'number',min:1,max:10000,value:100},
    {key:'length',label:'Target bond length (px)',type:'number',min:1,max:1000,value:median||L()},
    {key:'labels',label:'Scale atom labels',type:'checkbox',value:false}],'Scale');if(!a)return;if(a.mode!=='percent'&&!median)throw Error('Select a bond to use bond-length scaling.');scaleSelection(a.mode==='percent'?a.percent:100*(a.mode==='fixed'?L():a.length)/median,a.labels);}
  const ACS={bondLength:19.2,lineWidth:.8,boldWidth:8/3,marginWidth:32/15,hashSpacing:10/3,bondSpacing:.18,chainAngle:120};
  async function settings(){
    const m=modal('Document Settings',true),form=el('form'),tabs=el('nav',null,{'aria-label':'Settings categories',class:'web-settings-tabs'});m.body.append(form);form.append(tabs);
    const nameLabel=el('label','Document name',{class:'web-field'}),name=el('input',null,{'aria-label':'Document name',value:doc.name,maxLength:100});nameLabel.append(name);form.append(nameLabel);
    const template=el('button','Apply ACS Document 1996',{type:'button'});form.append(template);
    const controls={},panels=[];
    function section(title,specs){const panel=el('fieldset'),legend=el('legend',title);panel.append(legend);form.append(panel);panels.push(panel);const tab=el('button',title,{type:'button'});tab.onclick=()=>panels.forEach(p=>p.hidden=p!==panel);tabs.append(tab);
      for(const [key,label,value,type='number',options] of specs){const wrap=el('label',label,{class:'web-field'}),input=el(type==='select'?'select':'input',null,{'aria-label':label});if(type==='select')for(const option of options)input.add(new Option(Array.isArray(option)?option[1]:option,Array.isArray(option)?option[0]:option));else{input.type=type;if(type==='number'){input.min=key==='pageMargin'?0:.01;input.max=1000;input.step='any';input.required=true;}}input.value=type==='number'?Number(Number(value).toFixed(6)):value;controls[key]=input;wrap.append(input);panel.append(wrap);}}
    const drawing={...ACS,...doc.drawingSettings},text=doc.textSettings||{labelFont:'Arial',labelSize:18,captionFont:'Arial',captionSize:18},page=doc.pageSettings||{width:816,height:1056,margin:48},view=rulerSettings();
    section('Drawing',Object.entries({bondLength:'Fixed bond length (pt)',lineWidth:'Line width (pt)',boldWidth:'Bold width (pt)',marginWidth:'Margin width (pt)',hashSpacing:'Hash spacing (pt)'}).map(([key,label])=>[key,label,drawing[key]*.75]).concat([['bondSpacing','Bond spacing (%)',drawing.bondSpacing*100],['chainAngle','Chain angle (degrees)',drawing.chainAngle],['angleIncrement','Angle snap increment (degrees)',drawing.angleIncrement||15]]));
    const fonts=['Arial','Helvetica','Times New Roman','Georgia','Courier New','Verdana','Tahoma'];
    section('Text',[['labelFont','Atom label font',text.labelFont,'select',fonts],['labelSize','Atom label size (pt)',text.labelSize*.75],['captionFont','Caption font',text.captionFont,'select',fonts],['captionSize','Caption size (pt)',text.captionSize*.75]]);
    section('Page',[['pageWidth','Page width (in)',page.width/96],['pageHeight','Page height (in)',page.height/96],['pageMargin','Page margin (in)',page.margin/96]]);
    section('Rulers',[['units','Ruler units',view.units,'select',[['mm','Millimeters'],['cm','Centimeters'],['in','Inches'],['pt','Points']]]]);
    panels.forEach((p,i)=>p.hidden=i!==0);
    template.onclick=()=>{for(const key of ['bondLength','lineWidth','boldWidth','marginWidth','hashSpacing'])controls[key].value=Number((ACS[key]*.75).toFixed(6));controls.bondSpacing.value=18;controls.chainAngle.value=120;controls.angleIncrement.value=15;controls.labelFont.value=controls.captionFont.value='Arial';controls.labelSize.value=controls.captionSize.value=10;controls.pageWidth.value=8.5;controls.pageHeight.value=11;controls.pageMargin.value=.5;controls.units.value='mm';};
    const footer=el('footer');footer.append(el('button','Apply',{type:'submit'}));const cancel=el('button','Cancel',{type:'button'});cancel.onclick=()=>m.dialog.close();footer.append(cancel);form.append(footer,el('p','New drawings use ACS Document 1996. Drawing dimensions are in points; 72 pt = 1 in. Page margins define the drawing area. Applying settings keeps existing atom positions.'));
    form.onsubmit=e=>{e.preventDefault();const v=Object.fromEntries(Object.entries(controls).map(([key,input])=>[key,input.type==='number'?Number(input.value):input.value]));if(v.chainAngle>=180||v.angleIncrement>180||v.bondSpacing>100||v.pageMargin*2>=Math.min(v.pageWidth,v.pageHeight)){notify('Check chain angle, bond spacing, and page margins.');return;}try{transaction(()=>{doc.name=name.value.trim()||'Untitled structure';doc.drawingSettings={};for(const key of ['bondLength','lineWidth','boldWidth','marginWidth','hashSpacing'])doc.drawingSettings[key]=v[key]/.75;doc.drawingSettings.bondSpacing=v.bondSpacing/100;doc.drawingSettings.chainAngle=v.chainAngle;doc.drawingSettings.angleIncrement=v.angleIncrement;doc.textSettings={labelFont:v.labelFont,labelSize:v.labelSize/.75,captionFont:v.captionFont,captionSize:v.captionSize/.75};doc.pageSettings={width:v.pageWidth*96,height:v.pageHeight*96,margin:v.pageMargin*96};doc.viewSettings={...view,units:v.units};$('docName').value=doc.name;});m.dialog.close();}catch(error){notify(error.message);}};m.open();
  }
  setAction('settings',()=>settings().catch(e=>W.show('Document Settings',e.message)));
  setAction('rotate',()=>rotate().catch(e=>W.show('Rotate',e.message)));
  add('Object','Rotate…',rotate);add('Object','Scale Objects…',scale);
  add('Object','Fixed Lengths…',async()=>{const a=await fields('Fixed Bond Length',[{key:'enabled',label:'Use fixed bond lengths',type:'checkbox',value:fixedLengths},{key:'length',label:'Bond length (pt)',type:'number',min:.1,max:750,step:.1,value:Number((L()*.75).toFixed(6))}]);if(!a)return;transaction(()=>{doc.drawingSettings={...doc.drawingSettings,bondLength:a.length/.75};});fixedLengths=a.enabled;notify('Fixed lengths '+(fixedLengths?'on':'off')+' · '+a.length+' pt');});
  add('Object','Fixed Angles…',async()=>{const a=await fields('Fixed Angles',[{key:'enabled',label:'Snap bond angles',type:'checkbox',value:fixedAngles},{key:'angle',label:'Angle increment (degrees)',type:'number',min:.1,max:180,step:.1,value:doc.drawingSettings?.angleIncrement||15}]);if(!a)return;transaction(()=>{doc.drawingSettings={...doc.drawingSettings,angleIncrement:a.angle};});fixedAngles=a.enabled;notify('Fixed angles '+(fixedAngles?'on':'off')+' · '+a.angle+'°');});
  for(const [label,fn] of [['Group',()=>groupSelection()],['Ungroup',()=>ungroupSelection()],['Make Group Integral',()=>integralSelection()],['Flip Vertically',()=>flipSelection(true)],['Center on Page',()=>centerSelection()]])add('Object',label,fn);
  add('Edit','Repeat Rotate',()=>rotateSelection(lastRotation));
  for(const [mode,label] of [['left','Left'],['horizontal','Horizontal Centers'],['right','Right'],['top','Top'],['vertical','Vertical Centers'],['bottom','Bottom']])add('Object','Align '+label,()=>objectAlign(mode));
  add('Object','Distribute Horizontally',()=>objectDistribute('x'));add('Object','Distribute Vertically',()=>objectDistribute('y'));
  add('View','Show Rulers',()=>{showRulers=!showRulers;render();});
  add('View','Ruler Settings…',async()=>{
    const current=rulerSettings(),a=await fields('Ruler Settings',[
      {key:'units',label:'Units',type:'select',options:[['mm','Millimeters (mm)'],['cm','Centimeters (cm)'],['in','Inches (in)'],['pt','Points (pt)']],value:current.units},
      {key:'origin',label:'Zero point',type:'select',options:[['keep','Keep document origin'],['page','Page top-left (0, 0)'],['visible','Visible drawing area top-left']]}
    ],'Apply','Rulers measure from a fixed document origin. Zooming and panning do not change the zero point. One inch equals 96 drawing pixels.');
    if(!a)return;transaction(()=>{doc.viewSettings={...current,units:a.units};if(a.origin==='page'){doc.viewSettings.originX=0;doc.viewSettings.originY=0;}if(a.origin==='visible'){doc.viewSettings.originX=center.x-canvas.clientWidth/(2*zoom)+25/zoom;doc.viewSettings.originY=center.y-canvas.clientHeight/(2*zoom)+25/zoom;}});showRulers=true;render();
  });
  add('View','Go to Ruler Origin',()=>{const s=rulerSettings();center={x:s.originX+(canvas.clientWidth/2-65)/zoom,y:s.originY+(canvas.clientHeight/2-65)/zoom};showRulers=true;render();});
  add('View','Fit to Window',()=>{const p=doc.pageSettings||{width:816,height:1056,margin:48};center={x:p.width/2-p.margin,y:p.height/2-p.margin};zoomTo(Math.min(canvas.clientWidth/p.width,canvas.clientHeight/p.height)*.95);});
  async function saveDrawing(){
    const answer=await fields('Save Drawing',[{key:'name',label:'File name',value:doc.name,maxLength:100,required:true}],'Save');if(!answer)return;
    transaction(()=>{doc.name=answer.name.trim().replace(/\.chemjson$/i,'')||'Untitled structure';$('docName').value=doc.name;});
    download(JSON.stringify(doc,null,2),'chemjson','application/json');dirty=false;notify('Editable drawing downloaded.');
  }
  W.requestSave=()=>saveDrawing().catch(error=>W.show('Save Drawing',error.message));
  add('File','Save As…',saveDrawing);
  add('Structure','Expand Label',()=>transform('expand'));
  add('Structure','Contract Label…',async()=>{const a=await fields('Contract Label',[{key:'label',label:'Abbreviation',value:'R',required:true,maxLength:40}]);if(a)await transform('contract',a);});
  add('Structure','Convert Name to Structure…',async()=>{
    const a=await fields('Convert Name to Structure',[{key:'value',label:'Chemical name / SMILES',required:true,maxLength:1000},{key:'isSmiles',label:'Input is SMILES',type:'checkbox'},{key:'online',label:'Use PubChem for unknown names (sends the name to PubChem)',type:'checkbox'}],'Insert Structure');
    if(!a)return;const saved=current(),r=await W.api('name-to-structure',a);unchanged(saved);fitFragmentToBondLength(r.atoms,r.bonds);transaction(()=>{doc.atoms.push(...r.atoms);doc.bonds.push(...r.bonds);selection=new Set(r.atoms.map(a=>a.id));annSelection.clear();});fit();
  });
  async function moleculeLabel(){
    const saved=current(),prop=await W.api('properties');unchanged(saved);
    const a=await fields('Label Molecule',[{key:'name',label:'Molecule name',value:prop.name,maxLength:400},{key:'lookup',label:'Look up the exact structure in PubChem (sends this molecule)',type:'checkbox'},{key:'formula',label:'Formula',value:prop.formula,readonly:true},{key:'weight',label:'Molecular weight (g/mol)',value:prop.weight.toFixed(3),readonly:true}],'Insert Label');
    if(!a)return;let name=a.name.trim();if(a.lookup){const r=await W.api('lookup-name',{online:true});name=r.name;}unchanged(saved);if(!name)throw Error('Enter a name or choose PubChem lookup.');
    transaction(()=>{for(const [offset,text] of [[0,name],[23,'MW: '+prop.weight.toFixed(3)+' g/mol']])doc.annotations.push({id:id('label'),type:'text',x:prop.bounds.x,y:prop.bounds.y+40+offset,text});});
  }
  add('Structure','Label Molecule (Name and MW)…',moleculeLabel);add('Structure','Convert Structure to Name…',moleculeLabel);
  add('Structure','Atom Properties…',async()=>{
    const atom=selectedAtom(),saved=current();const a=await fields('Atom Properties',[
      {key:'label',label:'Element / label',value:atom.label,required:true,maxLength:40},
      {key:'charge',label:'Formal charge',type:'number',min:-20,max:20,value:atom.charge},
      {key:'automatic',label:'Automatic formal charge from bonding / ligands',type:'checkbox',value:atom.chargeMode!=='manual'&&(atom.chargeMode==='auto'||atom.charge===0)},
      {key:'complexCharge',label:'Total complex charge (single metal)',type:'number',min:-20,max:20,value:atom.complexCharge||0},
      {key:'radical',label:'Unpaired electrons',type:'number',min:0,max:2,value:atom.radical||0},
      {key:'lonePairs',label:'Displayed lone pairs',type:'number',min:0,max:4,value:atom.lonePairs||0}]);if(!a)return;unchanged(saved);
    transaction(()=>{if(a.label!==atom.label)delete atom.textRuns;Object.assign(atom,{label:a.label.trim(),charge:a.charge,chargeMode:a.automatic?'auto':'manual',complexCharge:a.complexCharge,radical:a.radical,lonePairs:a.lonePairs});});
  });
  add('Structure','Bond Properties…',async()=>{
    const bonds=doc.bonds.filter(b=>selection.has(b.a)&&selection.has(b.b));if(bonds.length!==1)throw Error('Select both ends of exactly one bond.');const bond=bonds[0],saved=current();
    const a=await fields('Bond Properties',[{key:'order',label:'Order',type:'select',value:bond.order,options:[['1','Single'],['2','Double'],['3','Triple'],['4','Aromatic']]},{key:'style',label:'Style',type:'select',value:bond.style,options:['normal','wedge','hash','coord','dashed','hashed','boldBond','hollowWedge','wavy','crossBond']},{key:'side',label:'Double bond position',type:'select',value:bond.doublePosition||'auto',options:['auto','left','right','center']},{key:'reverse',label:'Reverse bond direction',type:'checkbox'}]);if(!a)return;unchanged(saved);
    transaction(()=>{bond.order=Number(a.order);bond.style=a.style;delete bond.doublePosition;if(a.side!=='auto')bond.doublePosition=a.side;if(a.reverse)[bond.a,bond.b]=[bond.b,bond.a];});
  });
  // Replace the simple cleanup action with desktop options.
  [...W.menu('Structure').querySelectorAll('button')].filter(b=>b.textContent==='Clean Up Structure').forEach(b=>b.remove());
  add('Structure','Clean Up Structure…',async()=>{const a=await fields('Clean Up Structure',[{key:'preserveMetals',label:'Preserve metal and coordination geometry',type:'checkbox',value:true}],'Clean Up','Clean complete molecules touched by selected atoms, or all molecules when nothing is selected. Wedge/hash stereo is preserved; Undo restores the drawing.');if(a){const r=await transform('cleanup',{...a,bondLength:L()});fit();W.show('Cleanup result',r.cleaned_components+' molecule(s) cleaned.\n'+r.notes.join('\n'));}});
  // Complete text controls; retaining the rich editor's saved range is essential.
  for(const [label,key] of [['Bold','bold'],['Italic','italic'],['Underline','underline']])add('Text',label,()=>setTextStyle({[key]:!activeTextStyle()[key]}),{finish:false,replace:true});
  add('Text','Plain',()=>setTextStyle({plain:true}),{finish:false});
  add('Text','Subscript',()=>setTextStyle({script:'sub'}),{finish:false});add('Text','Superscript',()=>setTextStyle({script:'super'}),{finish:false});add('Text','Normal Script',()=>setTextStyle({script:'normal'}),{finish:false});add('Text','Formula',()=>formatFormula(),{finish:false});
  for(const alignment of ['left','center','right','justify'])add('Text','Align '+alignment,()=>paragraphStyle({alignment}),{finish:false});
  add('Text','Line Spacing…',async()=>{const a=await fields('Line Spacing',[{key:'lineSpacing',label:'Line height multiplier',type:'number',min:.5,max:5,step:.05,value:1.2}]);if(a)paragraphStyle(a);},{finish:false});
  ensureMenu('Color');for(const [name,color] of [['Black','#000000'],['Red','#cc0000'],['Blue','#0033cc'],['Green','#008000'],['Gray','#666666']])add('Color',name,()=>setTextStyle({color}),{finish:false});
  add('Color','More Colors…',async()=>{const a=await fields('Text Color',[{key:'color',label:'Text color',type:'color',value:activeTextStyle().color||'#000000'}]);if(a)setTextStyle(a);},{finish:false});
  const bar=el('div',null,{class:'web-textbar toolbar','aria-label':'Text Style'});
  const font=el('select',null,{'aria-label':'Font family'});for(const name of ['Arial','Helvetica','Times New Roman','Georgia','Courier New','Verdana','Tahoma'])font.add(new Option(name,name));bar.append(font);
  const size=el('input',null,{type:'number','aria-label':'Font size (points)',min:4,max:96,step:.1,value:Number((textStyle.size*.75).toFixed(2))});bar.append(size);
  for(const control of [font,size])control.addEventListener('pointerdown',()=>rememberTextSelection());
  font.onchange=()=>setTextStyle({font:font.value});size.onchange=()=>{if(size.checkValidity())setTextStyle({size:Number(size.value)/.75});};
  for(const [label,key] of [['B','bold'],['I','italic'],['U','underline']]){const b=el('button',label,{type:'button','aria-label':key});b.onpointerdown=e=>{rememberTextSelection();e.preventDefault();};b.onclick=()=>setTextStyle({[key]:!activeTextStyle()[key]});bar.append(b);}
  const color=el('input',null,{type:'color',value:'#000000','aria-label':'Text color'});color.onpointerdown=()=>rememberTextSelection();color.oninput=()=>setTextStyle({color:color.value});bar.append(color);
  setInterval(()=>{if(bar.contains(document.activeElement))return;const t=activeTextStyle();font.value=t.font;size.value=Number((t.size*.75).toFixed(2));color.value=t.color;},500);
  const atomLabel=el('input',null,{'aria-label':'Atom label',placeholder:'Atom / label',maxLength:40});atomLabel.value='C';atomLabel.onchange=()=>{elementLabel(atomLabel.value);};bar.append(atomLabel);
  function elementLabel(value){element=value.trim().slice(0,40)||'C';$('elementInput').value=element;if(selection.size===1)changeLabel(element);else setTool('atom');}
  document.querySelector('.toolbar').after(bar);
  ensureMenu('Curves');
  for(const [label,change] of [['Closed',{closed:true,heads:'none'}],['Open',{closed:false}],['Plain',{fill:'none',dashed:false,lineWidth:1.7}],['Filled',{closed:true,fill:'black',heads:'none'}],['Shaded',{closed:true,fill:'gray',heads:'none'}],['Dashed',{dashed:true}],['Bold',{lineWidth:3.4}],['Arrow at Start',{closed:false,heads:'start'}],['Arrow at End',{closed:false,heads:'end'}],['Arrows at Both Ends',{closed:false,heads:'both'}]])add('Curves',label,()=>curveCommand(change));
  add('Curves','Add Point',()=>curvePointCommand(false));add('Curves','Delete Point',()=>curvePointCommand(true));
  async function editTable(objectId){
    const a=doc.annotations.find(a=>a.id===objectId&&a.type==='table');if(!a)return;
    const saved=current(),m=modal('Edit Table',true),form=el('form'),grid=el('div',null,{class:'web-cell-grid'});m.body.append(form);
    const rowLabel=el('label','Rows '),rows=el('input',null,{type:'number',min:1,max:30,value:a.rows});rowLabel.append(rows);
    const colLabel=el('label','Columns '),cols=el('input',null,{type:'number',min:1,max:20,value:a.cols});colLabel.append(cols);form.append(rowLabel,colLabel,grid);
    let values=Array.from({length:a.rows},(_,r)=>Array.from({length:a.cols},(_,c)=>({text:a.cells[r*a.cols+c]||'',object:a.cellObjects?.[r*a.cols+c]||null}))),active=null;
    const redraw=()=>{grid.replaceChildren();grid.style.gridTemplateColumns=`repeat(${Number(cols.value)},minmax(110px,1fr))`;for(let r=0;r<Number(rows.value);r++)for(let c=0;c<Number(cols.value);c++){values[r]??=[];values[r][c]??={text:'',object:null};const input=el('textarea',null,{'aria-label':`Row ${r+1} Column ${c+1}`,maxLength:500});input.value=values[r][c].object?'[Drawing]':values[r][c].text;input.onfocus=()=>active=[r,c];input.oninput=()=>{values[r][c]={text:input.value,object:null};};grid.append(input);}};
    rows.onchange=cols.onchange=()=>{if(rows.checkValidity()&&cols.checkValidity())redraw();};redraw();
    const paste=el('button','Paste copied drawing into selected cell',{type:'button'});paste.onclick=()=>{if(!clipboard||!active){notify('Copy a drawing selection and select a cell first.');return;}const [r,c]=active;values[r][c]={text:'',object:ChemCore.clone(clipboard)};redraw();};form.append(paste);
    form.append(el('button','Apply',{type:'submit'}));form.onsubmit=e=>{e.preventDefault();try{unchanged(saved);transaction(()=>{a.rows=Number(rows.value);a.cols=Number(cols.value);a.cells=[];a.cellObjects=[];for(let r=0;r<a.rows;r++)for(let c=0;c<a.cols;c++){a.cells.push(values[r][c].text);a.cellObjects.push(values[r][c].object);}});m.dialog.close();}catch(error){notify(error.message);}};m.open();
  }
  add('Object','Edit Table…',()=>{const a=doc.annotations.find(a=>annSelection.has(a.id)&&a.type==='table');if(!a)throw Error('Select a table first.');return editTable(a.id);});
  // Shared model requests normally handled by the native Qt event loop.
  setInterval(()=>{if(document.querySelector('dialog[open]'))return;try{
    if(nativeRotateRequest){nativeRotateRequest=false;rotate().catch(e=>W.show('Rotate',e.message));}
    else if(nativeScaleRequest){nativeScaleRequest=false;scale().catch(e=>W.show('Scale',e.message));}
    else if(nativeGraphicRequest){const target=nativeGraphicRequest;nativeGraphicRequest=null;editTable(target);}
  }catch(error){W.show('Drawing',error.message);}},200);
  // Native-style panning without changing the white document surface.
  const horizontal=el('input',null,{type:'range',min:-2000,max:2000,value:0,'aria-label':'Horizontal pan',class:'web-hpan'}),vertical=el('input',null,{type:'range',min:-2000,max:2000,value:0,'aria-label':'Vertical pan',class:'web-vpan'});
  horizontal.oninput=()=>{center.x=500+Number(horizontal.value);render();};vertical.oninput=()=>{center.y=350+Number(vertical.value);render();};document.querySelector('.stage').append(horizontal,vertical);
  // CDX/CDXML/CDXL imports are handled by the same parser as the desktop build.
  const input=$('openFile'),oldOpen=input.onchange;input.accept+=',.cdx,.cdxml,.cdxl';
  input.onchange=async event=>{const file=input.files[0];if(!file||! /\.(cdx|cdxml|cdxl)$/i.test(file.name)){return oldOpen(event);}input.value='';try{
    if(file.size>5e6)throw Error('File too large (maximum 5 MB).');
    const a=await fields('Open ChemDraw File',[],'Open','Replace the current drawing with '+file.name+'? Undo restores the previous drawing.');if(!a)return;
    const saved=current(),body=new FormData();body.append('file',file);const response=await fetch('/api/import-chemdraw',{method:'POST',body});let result;try{result=await response.json();}catch{throw Error('Unexpected server response (HTTP '+response.status+').');}if(!response.ok)throw Error(result.error||'Unable to import this file.');unchanged(saved);replaceDoc(ChemCore.validate(result.drawing));if(result.warnings?.length)W.show('Import warnings',result.warnings.join('\n'));
  }catch(error){W.show('Open',error.message);}};
  async function copyGraphic(cut=false){
    if(editing){const part=textClipboard(cut);if(part&&navigator.clipboard&&window.isSecureContext)await navigator.clipboard.writeText(part.textSelection);return;}
    finishEditing();copy();
    if(navigator.clipboard&&window.isSecureContext&&window.ClipboardItem){
      const svg=exportSVG(true).text,blob=await svgPNG(svg);
      await navigator.clipboard.write([new ClipboardItem({'image/png':blob})]);notify('Copied editable selection internally and image to system clipboard.');
    }else notify('Selection copied inside ErezDraw. Use Copy as Image download for Word; system image clipboard requires HTTPS.');
    if(cut)deleteSelection();
  }
  async function svgPNG(svg){const url=URL.createObjectURL(new Blob([svg],{type:'image/svg+xml'}));try{const image=new Image();image.src=url;await image.decode();const c=document.createElement('canvas');c.width=Math.max(1,Math.ceil(image.width*2));c.height=Math.max(1,Math.ceil(image.height*2));const ctx=c.getContext('2d');ctx.drawImage(image,0,0,c.width,c.height);return await new Promise(resolve=>c.toBlob(resolve,'image/png'));}finally{URL.revokeObjectURL(url);}}
  setAction('copy',()=>copyGraphic().catch(e=>W.show('Copy',e.message)));setAction('cut',()=>copyGraphic(true).catch(e=>W.show('Cut',e.message)));
  add('Edit','Copy as Image / Word…',async()=>{if(navigator.clipboard&&window.isSecureContext)await copyGraphic();else{download(await svgPNG(exportSVG(true).text),'png','image/png');notify('Insert the downloaded PNG into Word. Direct image clipboard needs HTTPS.');}});
  add('Edit','Paste Drawing from Clipboard…',async()=>{if(!navigator.clipboard||!window.isSecureContext){paste();return;}const text=await navigator.clipboard.readText();if(/^\s*\{/.test(text)){let fragment=null;try{fragment=JSON.parse(text);}catch{}if(fragment&&Array.isArray(fragment.atoms)&&Array.isArray(fragment.bonds)){const checked=ChemCore.validate({format:'chemsketch-classic',version:1,name:'Clipboard',atoms:fragment.atoms,bonds:fragment.bonds,annotations:Array.isArray(fragment.annotations)?fragment.annotations:[],...(fragment.groups?{groups:fragment.groups}:{}),...(fragment.ligands?{ligands:fragment.ligands}:{})});clipboard={atoms:checked.atoms,bonds:checked.bonds,annotations:checked.annotations,groups:checked.groups||[],ligands:checked.ligands||[]};paste();return;}}paste();});
  document.addEventListener('keydown',e=>{if(!(e.ctrlKey||e.metaKey)||['INPUT','TEXTAREA','SELECT'].includes(e.target.tagName)||document.querySelector('dialog[open]'))return;const key=e.key.toLowerCase();const run={b:()=>setTextStyle({bold:!activeTextStyle().bold}),i:()=>setTextStyle({italic:!activeTextStyle().italic}),u:()=>setTextStyle({underline:!activeTextStyle().underline}),g:()=>e.shiftKey?ungroupSelection():groupSelection(),c:()=>copyGraphic(),x:()=>copyGraphic(true)}[key];if(run){e.preventDefault();e.stopImmediatePropagation();Promise.resolve(run()).catch(error=>W.show('Edit',error.message));}},true);
  const context=el('div',null,{class:'web-context',hidden:''});document.body.append(context);
  for(const [label,run] of [['Undo',()=>action('undo')],['Redo',()=>action('redo')],['Cut',()=>copyGraphic(true)],['Copy',()=>copyGraphic()],['Paste',()=>paste()],['Delete',()=>action('delete')],['Rotate…',rotate],['Scale Objects…',scale],['Flip Horizontally',()=>flipSelection()],['Flip Vertically',()=>flipSelection(true)]]){const b=el('button',label);b.onclick=()=>{context.hidden=true;Promise.resolve().then(run).catch(e=>W.show(label,e.message));};context.append(b);}
  canvas.addEventListener('contextmenu',e=>{e.preventDefault();context.hidden=false;context.style.left=Math.min(e.clientX,innerWidth-220)+'px';context.style.top=Math.min(e.clientY,innerHeight-350)+'px';});document.addEventListener('pointerdown',e=>{if(!context.contains(e.target))context.hidden=true;});
  Object.assign(W,{element:el,modal,fields,add,transaction,unchanged,current,transform,rotate,scale,settings,editTable,svgPNG,copyGraphic,commands});
  // Tool families and panels load independently from chemistry calculations.
  async function toolCatalog(){const response=await fetch('/web/catalog.json');if(!response.ok)throw Error('Unable to load drawing tools.');const {families}=await response.json(),palette=document.querySelector('.palette');palette.replaceChildren();const grid=el('div',null,{class:'web-tool-grid'});palette.append(grid);
    for(const [key,label,options] of families){const family=el('div',null,{class:'web-family'}),b=el('button',null,{type:'button',title:label,'aria-label':label,'data-tool':key,class:'tool'}),img=el('img',null,{src:'/web/icons/'+key+'.svg',alt:''});b.append(img);family.append(b);let chosen=key==='templates'?'ring6':key==='symbol'?'chargeUp':key;
      const choose=()=>{if(key==='fragment')W.massSpectrum();else if(key==='ligands')openLigands();else setTool(chosen);};b.onclick=choose;
      if(options){const open=el('button','▾',{type:'button',class:'web-family-toggle','aria-label':label+' variants'});family.append(open);open.onclick=()=>{const m=modal(label);const variants=el('div',null,{class:'web-variants'});m.body.append(variants);for(const [variant,name] of options){const v=el('button',null,{title:name,'aria-label':name});v.append(el('img',null,{src:'/web/icons/'+variant+'.svg',alt:''}),el('span',name));v.onclick=()=>{chosen=variant;img.src='/web/icons/'+variant+'.svg';b.dataset.tool=variant;setTool(variant);m.dialog.close();};variants.append(v);}m.open();};}grid.append(family);
    }
    const atoms=el('button','Periodic Table',{class:'web-palette-link'});atoms.onclick=openElements;palette.append(atoms);
  }
  let catalogPromise;function catalog(){return catalogPromise??=fetch('/api/catalog').then(async r=>{if(!r.ok)throw Error('Unable to load templates.');return r.json();}).catch(e=>{catalogPromise=null;throw e;});}
  async function openLigands(){try{const data=await catalog(),m=modal('Organometallic Ligands',true),filter=el('input',null,{type:'search',placeholder:'Find ligand','aria-label':'Find ligand'}),grid=el('div',null,{class:'web-ligands'});m.body.append(filter,grid);for(const ligand of data.ligands){const b=el('button',null,{title:ligand.category+' — '+ligand.name});b.innerHTML=ligand.svg;b.append(el('span',ligand.name));b.dataset.search=(ligand.category+' '+ligand.name).toLowerCase();b.onclick=()=>{setLigandTemplate(ligand.template);m.dialog.close();notify('Click or drag on the drawing to place '+ligand.name+'.');};grid.append(b);}filter.oninput=()=>{for(const b of grid.children)b.hidden=!b.dataset.search.includes(filter.value.toLowerCase());};m.open();}catch(error){W.show('Ligands',error.message);}}
  async function openElements(){const data=await catalog(),m=modal('Periodic Table',true),grid=el('div',null,{class:'web-elements'});m.body.append(el('p','Select an element to label a selected atom or activate its drawing tool.'),grid);const rows=[[1,...Array(16).fill(0),2],[3,4,...Array(10).fill(0),5,6,7,8,9,10],[11,12,...Array(10).fill(0),13,14,15,16,17,18],Array.from({length:18},(_,i)=>19+i),Array.from({length:18},(_,i)=>37+i),[55,56,57,...Array.from({length:15},(_,i)=>72+i)],[87,88,89,...Array.from({length:15},(_,i)=>104+i)],[0,0,0,...Array.from({length:14},(_,i)=>58+i)],[0,0,0,...Array.from({length:14},(_,i)=>90+i)]];
    rows.forEach((row,r)=>row.forEach((z,c)=>{if(!z)return;const a=data.elements[z-1],b=el('button',a.symbol,{title:`${z}: ${a.name}; atomic weight ${a.weight}`});b.style.gridArea=`${r+1}/${c+1}`;b.onclick=()=>{elementLabel(a.symbol);m.dialog.close();};grid.append(b);}));m.open();}
  add('View','Show Ligand Templates',openLigands);add('View','Show Periodic Table',openElements);
  add('View','Show Character Map',()=>{const m=modal('Character Map'),grid=el('div',null,{class:'web-characters'});m.body.append(grid);for(const ch of 'αβγδεζηθικλμνξοπρστυφχψωΔΣΩ±−×÷≈≠≤≥∞°Åηκ·•‡†←→↔⇌₀₁₂₃₄₅₆₇₈₉⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻'){const b=el('button',ch);b.onclick=()=>{insertCharacter(ch);};grid.append(b);}m.open();},{finish:false});
  function analysisTables(host,result,includeCalculated=false){
    host.replaceChildren();host.dataset.plaintext=Object.entries(result[0]).map(([k,v])=>k+': '+v).join('\n\n');
    function table(title,headers,rows){host.append(el('h3',title));const t=el('table',null,{class:'web-property-table'}),head=el('thead'),hr=el('tr'),body=el('tbody');for(const label of headers)hr.append(el('th',label));head.append(hr);for(const values of rows){const row=el('tr');for(const value of values)row.append(el('td',String(value)));body.append(row);}t.append(head,body);host.append(t);}
    const data=result[0],composition='Elemental composition',isotopes='Isotope envelope (mass Da : relative %)';
    table('Molecular analysis',['Property','Value'],Object.entries(data).filter(([key])=>key!==composition&&key!==isotopes));
    if(data[composition])table('Elemental composition',['Element','Mass (%)'],data[composition].split(';').map(part=>part.trim().split(/:\s*/)));
    if(data[isotopes])table('Isotope envelope',['Mass (Da)','Relative intensity (%)'],data[isotopes].split('\n').map(part=>part.split(/\s*:\s*/)));
    if(includeCalculated&&result[1]&&Object.keys(result[1]).length)table('Calculated properties',['Property','Value'],Object.entries(result[1]));
  }
  add('Structure','Analysis…',async()=>{const base=snapshot(),selected=[...selection],m=modal('Analysis',true);m.body.append(el('p','Calculating…',{role:'status'}));m.open();try{const result=await W.api('analysis',{drawing:base,selected});if(m.dialog.isConnected)analysisTables(m.body,result,true);}catch(error){if(m.dialog.isConnected)m.body.textContent=error.message;}});
  const panels=new Map();
  function openPanel(name){if(panels.has(name)){panels.get(name).remove();panels.delete(name);return;}
    const panel=el('aside',null,{class:'web-panel','aria-label':name}),header=el('header'),title=el('strong',name),close=el('button','Close'),pre=el(name==='Analysis'?'div':'pre','Loading…'),copyButton=el('button','Copy / Export'),pasteButton=el('button','Paste into Drawing');header.append(title,close);panel.append(header,pre,copyButton,pasteButton);document.querySelector('.workspace').append(panel);panels.set(name,panel);close.onclick=()=>{panel.remove();panels.delete(name);};
    let origin=null;header.onpointerdown=e=>{if(e.target===close)return;origin={x:e.clientX,y:e.clientY,left:panel.offsetLeft,top:panel.offsetTop};header.setPointerCapture(e.pointerId);};header.onpointermove=e=>{if(!origin)return;panel.style.left=Math.max(80,origin.left+e.clientX-origin.x)+'px';panel.style.top=Math.max(0,origin.top+e.clientY-origin.y)+'px';panel.style.right='auto';};header.onpointerup=()=>origin=null;
    copyButton.onclick=async()=>{if(navigator.clipboard&&window.isSecureContext)await navigator.clipboard.writeText(pre.dataset.plaintext||pre.textContent);else download(pre.dataset.plaintext||pre.textContent,'txt','text/plain');};pasteButton.onclick=()=>transaction(()=>{(pre.dataset.plaintext||pre.textContent).split('\n').filter(s=>s.trim()).slice(0,80).forEach((text,i)=>doc.annotations.push({id:id('analysis'),type:'text',x:center.x,y:center.y+i*24,text:text.slice(0,500)}));});
    let cached='',busy=false;async function update(){if(!panels.has(name))return;if(name==='Info'){const b=selectionBounds();pre.textContent=`Zoom: ${(zoom*100).toFixed(0)}%\nSelected atoms: ${selection.size}\nSelected annotations: ${annSelection.size}\nPointer: ${(lastPointer.x*.75).toFixed(1)}, ${(lastPointer.y*.75).toFixed(1)} pt`+(b?`\nPosition: ${(b.x*.75).toFixed(1)}, ${(b.y*.75).toFixed(1)} pt\nSize: ${((b.x2-b.x)*.75).toFixed(1)} × ${((b.y2-b.y)*.75).toFixed(1)} pt`:'');return;}
      const key=JSON.stringify([doc,[...selection]]);if(key===cached||busy)return;busy=true;try{const result=await W.api('analysis');if(!panels.has(name))return;cached=key;if(name==='Analysis'){analysisTables(pre,result);return;}const values=result[1];pre.textContent=Object.entries(values).map(([k,v])=>k+': '+v).join('\n\n');}catch(e){cached=key;pre.textContent=e.message;}finally{busy=false;}}
    update();const timer=setInterval(()=>{if(!panels.has(name)){clearInterval(timer);return;}update();},600);
  }
  for(const name of ['Analysis','Chemical Properties','Info'])add('View','Show '+(name==='Chemical Properties'?'Calculated Properties':name)+' Window',()=>openPanel(name));
  add('View','Show / Hide Text Style Toolbar',()=>bar.hidden=!bar.hidden);
  const about=document.querySelector('#aboutDialog');about.querySelectorAll('p')[2].textContent='Desktop drawing tools, object/text/curve editing, ligand templates, chemical analysis, NMR predictions and mass fragmentation are available in the browser. File dialogs use downloads and uploads. System image clipboard access requires HTTPS; this HTTP deployment provides PNG downloads for Word.';
  add('Help','Desktop / Web Feature Guide',()=>W.show('Desktop / Web Feature Guide','Use the 36-position palette and its variant arrows for advanced drawing tools. Structure contains atom/bond properties, name conversion, NMR and mass fragmentation. View contains live analysis/info panels, periodic table, character map and ligand templates. Double-click a table to edit cells. Object and Curves contain transforms and curve styles. All drawing edits use Undo/Redo.\n\nDownloads replace desktop Save dialogs. Browser-local autosave is separate for each browser. Copy as Image downloads PNG on HTTP; direct image clipboard requires HTTPS. Native operating-system window management is handled by your browser.'));
  // Keep chemistry commands focused and expose object operations directly.
  const removed=new Set(['Expand Label','Contract Label…','Atom Properties…','Bond Properties…']);
  for(const b of [...W.menu('Structure').querySelectorAll('button')])if(removed.has(b.textContent.trim())||['chargeUp','chargeDown'].includes(b.dataset.action))b.remove();
  W.menu('Object').querySelector('[data-action="rotate"]')?.remove();
  add('Structure','Chemical Properties…',async()=>{
    const base=snapshot(),selected=[...selection],m=modal('Chemical Properties — PubChem',true);
    const status=el('p','Querying PubChem for the selected structure…',{role:'status'});m.body.append(status);m.open();
    try{
      const result=await W.api('pubchem-properties',{drawing:base,selected});if(!m.dialog.isConnected)return;
      status.textContent='PubChem compound '+result.cid+' · '+result.name;
      m.body.append(el('a','View compound on PubChem',{href:result.url,target:'_blank',rel:'noopener noreferrer'}));
      const labels={Title:'Compound name',IUPACName:'IUPAC name',MolecularFormula:'Molecular formula',MolecularWeight:'Molecular weight (g/mol)',ExactMass:'Exact mass (Da)',MonoisotopicMass:'Monoisotopic mass (Da)',XLogP:'XLogP (computed)',TPSA:'Polar surface area (Å², computed)',HBondDonorCount:'Hydrogen bond donors',HBondAcceptorCount:'Hydrogen bond acceptors',RotatableBondCount:'Rotatable bonds',HeavyAtomCount:'Heavy atoms',Charge:'Formal charge',Complexity:'Complexity (computed)',InChIKey:'InChIKey',SMILES:'SMILES'};
      const table=el('table',null,{class:'web-property-table'});for(const [key,label] of Object.entries(labels)){const row=el('tr');row.append(el('th',label),el('td',String(result.properties[key]??'Not available')));table.append(row);}m.body.append(table);if(result.experimental?.length){m.body.append(el('h3','Reported physical properties'));for(const item of result.experimental){m.body.append(el('h4',item.name),el('p',item.value));if(item.source)m.body.append(el('p','Source: '+item.source));}}if(result.experimentalNote)m.body.append(el('p',result.experimentalNote));
      m.body.append(el('p','Source: PubChem. Values labeled computed are estimates. The structure is sent to PubChem when you open this dialog.'));
    }catch(error){if(m.dialog.isConnected)status.textContent=error.message;}
  });
  const alignmentIcons={"Align Left": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" aria-hidden=\"true\" focusable=\"false\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\"><path d=\"M4 3V29\"/><path d=\"M7 5H24V10H7Z M7 14H18V19H7Z M7 23H28V28H7Z\" fill=\"currentColor\"/></svg>", "Align Horizontal Centers": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" aria-hidden=\"true\" focusable=\"false\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\"><path d=\"M16 2V30\"/><path d=\"M6 5H26V10H6Z M11 14H21V19H11Z M3 23H29V28H3Z\" fill=\"currentColor\"/></svg>", "Align Right": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" aria-hidden=\"true\" focusable=\"false\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\"><path d=\"M28 3V29\"/><path d=\"M8 5H25V10H8Z M14 14H25V19H14Z M4 23H25V28H4Z\" fill=\"currentColor\"/></svg>", "Align Top": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" aria-hidden=\"true\" focusable=\"false\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\"><path d=\"M2 4H30\"/><path d=\"M4 7H9V24H4Z M13 7H18V18H13Z M23 7H28V28H23Z\" fill=\"currentColor\"/></svg>", "Align Vertical Centers": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" aria-hidden=\"true\" focusable=\"false\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\"><path d=\"M2 16H30\"/><path d=\"M4 6H9V26H4Z M13 11H18V21H13Z M23 3H28V29H23Z\" fill=\"currentColor\"/></svg>", "Align Bottom": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" aria-hidden=\"true\" focusable=\"false\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\"><path d=\"M2 28H30\"/><path d=\"M4 8H9V25H4Z M13 14H18V25H13Z M23 4H28V25H23Z\" fill=\"currentColor\"/></svg>", "Distribute Horizontally": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" aria-hidden=\"true\" focusable=\"false\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\"><path d=\"M3 4H8V28H3Z M14 8H19V24H14Z M25 4H30V28H25Z\" fill=\"currentColor\"/><path d=\"M9 2H13 M20 2H24 M10 0V4 M23 0V4\"/></svg>", "Distribute Vertically": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" aria-hidden=\"true\" focusable=\"false\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\"><path d=\"M4 3H28V8H4Z M8 14H24V19H8Z M4 25H28V30H4Z\" fill=\"currentColor\"/><path d=\"M2 9V13 M2 20V24 M0 10H4 M0 23H4\"/></svg>", "Center on Page": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" aria-hidden=\"true\" focusable=\"false\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\"><rect x=\"5\" y=\"2\" width=\"22\" height=\"28\"/><path d=\"M10 11H22V21H10Z M16 4V28 M7 16H25\"/></svg>", "Flip selection horizontally": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" aria-hidden=\"true\" focusable=\"false\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\"><path d=\"M15 3V29\" stroke-dasharray=\"2 2\"/><path d=\"M3 7L11 16L3 25Z M27 7L19 16L27 25Z\"/><path d=\"M3 3H11 M19 3H27\"/></svg>", "Rotate\u2026": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" aria-hidden=\"true\" focusable=\"false\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\"><path d=\"M6 20A11 11 0 1 0 8 7 M3 7H9V1\"/><path d=\"M12 12H20V20H12Z\" stroke-dasharray=\"2 2\"/></svg>", "Scale Objects\u2026": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" aria-hidden=\"true\" focusable=\"false\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\"><rect x=\"4\" y=\"16\" width=\"12\" height=\"12\"/><path d=\"M4 12V4H28V28H20\" stroke-dasharray=\"2 2\"/><path d=\"M17 15L28 4 M21 4H28V11\"/></svg>", "Group": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" aria-hidden=\"true\" focusable=\"false\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\"><rect x=\"3\" y=\"3\" width=\"26\" height=\"26\" stroke-dasharray=\"2 2\"/><rect x=\"6\" y=\"7\" width=\"11\" height=\"11\"/><rect x=\"15\" y=\"15\" width=\"11\" height=\"11\"/></svg>", "Ungroup": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" aria-hidden=\"true\" focusable=\"false\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\"><rect x=\"2\" y=\"3\" width=\"14\" height=\"14\" stroke-dasharray=\"2 2\"/><rect x=\"16\" y=\"16\" width=\"14\" height=\"14\" stroke-dasharray=\"2 2\"/></svg>", "Flip Vertically": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" aria-hidden=\"true\" focusable=\"false\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\"><path d=\"M3 16H29\" stroke-dasharray=\"2 2\"/><path d=\"M7 3L16 11L25 3Z M7 29L16 21L25 29Z\"/></svg>", "Edit Table\u2026": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" aria-hidden=\"true\" focusable=\"false\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\"><rect x=\"3\" y=\"4\" width=\"26\" height=\"24\"/><path d=\"M3 12H29 M3 20H29 M12 4V28 M21 4V28\"/></svg>", "Flatten Selection": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" aria-hidden=\"true\" focusable=\"false\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\"><path d=\"M3 24L12 18L29 22L20 28Z M5 13L14 7L27 10 M16 2V17 M12 13L16 17L20 13\"/></svg>", "Fixed Lengths\u2026": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" aria-hidden=\"true\" focusable=\"false\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\"><path d=\"M4 6H28V13H4Z M9 6V10 M15 6V12 M21 6V10 M5 24H27\"/><circle cx=\"5\" cy=\"24\" r=\"2\"/><circle cx=\"27\" cy=\"24\" r=\"2\"/></svg>", "Fixed Angles\u2026": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" aria-hidden=\"true\" focusable=\"false\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\"><path d=\"M5 4V27H28 M5 27L26 6 M5 17A10 10 0 0 1 12 20\"/><circle cx=\"24\" cy=\"23\" r=\"3\"/></svg>", "Make Group Integral": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" aria-hidden=\"true\" focusable=\"false\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\"><rect x=\"3\" y=\"5\" width=\"26\" height=\"22\" rx=\"2\"/><path d=\"M7 12H13V19H7Z M19 12H25V19H19Z M13 16H19\"/></svg>"};
  const objects=el('div',null,{class:'web-objectbar',role:'toolbar','aria-label':'Object actions'});
  const objectButtons=[...W.menu('Object').querySelectorAll('button')];
  const flipHorizontal=objectButtons.findIndex(b=>b.dataset.action==='flip'),flipVertical=objectButtons.findIndex(b=>b.textContent.trim()==='Flip Vertically');
  if(flipHorizontal>=0&&flipVertical>=0){const [vertical]=objectButtons.splice(flipVertical,1);objectButtons.splice(objectButtons.findIndex(b=>b.dataset.action==='flip')+1,0,vertical);}
  for(const original of objectButtons){
    const label=original.textContent.replace(/\s+/g,' ').trim(),button=el('button',label,{type:'button',title:label});
    if(alignmentIcons[label]){button.innerHTML=alignmentIcons[label];button.classList.add('web-alignment-button');button.setAttribute('aria-label',label);}
    button.onclick=()=>original.click();objects.append(button);
  }
  bar.before(objects);
  const mainIcons={"new": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" aria-hidden=\"true\" focusable=\"false\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\"><path d=\"M5 3H17L23 9V27H5Z\" fill=\"white\"/><path d=\"M17 3V9H23\"/></svg>", "open": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" aria-hidden=\"true\" focusable=\"false\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\"><path d=\"M3 9H12L15 12H28L24 26H3Z\" fill=\"#eee3aa\"/><path d=\"M3 9V6H12L15 9H27V12 M3 26L7 15H28\"/></svg>", "save": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" aria-hidden=\"true\" focusable=\"false\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\"><path d=\"M4 3H24L28 7V28H4Z\" fill=\"#b9c3cf\"/><path d=\"M8 3V12H22V3 M9 28V17H23V28\" fill=\"white\"/><path d=\"M18 5V10\" stroke-width=\"3\"/></svg>", "undo": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" aria-hidden=\"true\" focusable=\"false\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\"><path d=\"M7 11C19 3 29 13 23 22C21 25 16 26 12 24 M7 5V12H14\"/></svg>", "redo": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" aria-hidden=\"true\" focusable=\"false\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\"><path d=\"M25 11C13 3 3 13 9 22C11 25 16 26 20 24 M25 5V12H18\"/></svg>", "zoomIn": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" aria-hidden=\"true\" focusable=\"false\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\"><circle cx=\"12\" cy=\"12\" r=\"8\"/><path d=\"M18 18L29 29 M7 12H17 M12 7V17\"/></svg>", "zoomOut": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" aria-hidden=\"true\" focusable=\"false\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\"><circle cx=\"12\" cy=\"12\" r=\"8\"/><path d=\"M18 18L29 29 M7 12H17\"/></svg>", "fit": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" aria-hidden=\"true\" focusable=\"false\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\"><rect x=\"6\" y=\"6\" width=\"20\" height=\"20\"/><path d=\"M3 11V3H11 M21 3H29V11 M29 21V29H21 M11 29H3V21\"/></svg>", "grid": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" aria-hidden=\"true\" focusable=\"false\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\"><path d=\"M3 3H29V29H3Z M3 12H29 M3 21H29 M12 3V29 M21 3V29\"/></svg>"};
  const mainLabels={new:'New drawing',open:'Open drawing',save:'Save drawing',undo:'Undo',redo:'Redo',grid:'Toggle grid',zoomIn:'Zoom in',zoomOut:'Zoom out',fit:'Fit drawing'};
  for(const button of document.querySelectorAll('.toolbar [data-action]')){const key=button.dataset.action;if(mainIcons[key]){button.innerHTML=mainIcons[key];button.classList.add('web-toolbar-icon');button.title=mainLabels[key];button.setAttribute('aria-label',mainLabels[key]);}}
  const textIcons={"bold": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" aria-hidden=\"true\" focusable=\"false\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\"><path d=\"M10 4V28 M10 4H18C28 4 28 15 18 15H10 M10 15H19C29 15 29 28 19 28H10\" stroke-width=\"3\"/></svg>", "italic": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" aria-hidden=\"true\" focusable=\"false\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\"><path d=\"M13 4H26 M6 28H19 M20 4L12 28\"/></svg>", "underline": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" aria-hidden=\"true\" focusable=\"false\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\"><path d=\"M8 4V18C8 28 24 28 24 18V4 M5 29H27\"/></svg>"};
  for(const button of bar.querySelectorAll('button')){const key=button.getAttribute('aria-label');if(textIcons[key]){button.innerHTML=textIcons[key];button.classList.add('web-toolbar-icon');button.title=key[0].toUpperCase()+key.slice(1);}}

  $('bondLength').hidden=true;document.querySelector('label[for=bondLength]')?.remove();
  toolCatalog().catch(e=>W.show('Tools',e.message));
})();
