// Reuse the editor's minimal DOM harness, then drive actual pointer handlers.
const fs=require('fs'),vm=require('vm');
const harness=fs.readFileSync(__dirname+'/verify-engine.cjs','utf8').split('click(200,200);')[0];
const tests=`
const catalog=JSON.parse(fs.readFileSync(__dirname+'/assets/glassware.json','utf8'));
for(const item of catalog){
 evaluate("action('new')");
 evaluate('setGlasswareTemplate('+JSON.stringify(item.template)+')');
 get('canvas').handlers.pointerdown(event(200,200));
 assert.equal(state().annotations.length,0,'Mouse down must only preview');
 get('canvas').handlers.pointermove(event(260,240));
 assert.equal(state().annotations.length,0,'Drag must not commit');
 get('canvas').handlers.pointerup(event(260,240));
 const placed=state();assert.equal(placed.atoms.length,0);assert.equal(placed.bonds.length,0);
 assert.equal(placed.annotations.length,item.template.annotations.length,item.name);
 assert.equal(placed.groups.length,1);assert.equal(placed.groups[0].annotations.length,placed.annotations.length);
 assert.ok(placed.annotations.every(a=>a.x===260&&a.y===240));
 evaluate('ChemCore.validate(doc);doc=ChemCore.validate(JSON.parse(JSON.stringify(doc)))');
 evaluate("action('undo')");assert.equal(state().annotations.length,0);
 evaluate("action('redo');setTool('select');action('selectAll');rotateSelection(90);scaleSelection(150)");
 evaluate('ChemCore.validate(doc)');
 evaluate("action('copy');action('paste')");
 assert.equal(state().annotations.length,placed.annotations.length*2);
 assert.equal(new Set(state().annotations.map(a=>a.id)).size,state().annotations.length);
 assert.equal(state().groups.length,2);evaluate('ChemCore.validate(doc)');
 evaluate("action('new')");evaluate('setGlasswareTemplate('+JSON.stringify(item.template)+')');
 get('canvas').handlers.pointerdown(event(200,200));get('canvas').handlers.pointermove(event(230,240));
 get('canvas').handlers.pointercancel?.(event(230,240));evaluate('cancelGesture()');
 assert.equal(state().annotations.length,0);
}
evaluate('ChemCore.validate('+fs.readFileSync(__dirname+'/examples/Glassware-and-Pilot-Equipment.chemjson','utf8')+')');
console.log('PASS: all '+catalog.length+' glassware/pilot templates: placement preview, one-step Undo/Redo, cancellation, native save validation, rotation, scaling, grouped clipboard copies and independent IDs; no chemistry atoms.');
`;
vm.runInNewContext(harness+tests,{require,__dirname,console,Blob,URL});
