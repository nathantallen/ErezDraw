/* Browser controls for the same document, undo stack, and rendering engine. */
(() => {
  document.title = 'ErezDraw — Structure Editor';
  document.querySelector('.titlebar strong').textContent = 'ErezDraw';
  const theme = document.createElement('select');
  theme.id = 'web-theme'; theme.setAttribute('aria-label', 'Appearance');
  for (const mode of ['System', 'Light', 'Dark']) theme.add(new Option(mode, mode));
  document.querySelector('.titlebar').append(theme);
  let saved = 'System';
  try { saved = localStorage.getItem('erezdraw-appearance') || 'System'; } catch {}
  theme.value = ['System','Light','Dark'].includes(saved) ? saved : 'System';
  const media = matchMedia('(prefers-color-scheme: dark)');
  function appearance() {
    const dark = theme.value === 'Dark' || (theme.value === 'System' && media.matches);
    document.documentElement.dataset.appearance = dark ? 'dark' : 'light';
  }
  theme.onchange = () => { try { localStorage.setItem('erezdraw-appearance', theme.value); } catch {} appearance(); };
  media.addEventListener('change', appearance); appearance();
  const dialog = document.createElement('dialog');
  dialog.innerHTML = '<h2 id="web-result-title"></h2><pre id="web-result"></pre><button type="button">Close</button>';
  dialog.setAttribute('aria-labelledby', 'web-result-title'); document.body.append(dialog);
  dialog.querySelector('button').onclick = () => dialog.close();
  function show(title, value) {
    dialog.querySelector('h2').textContent = title;
    dialog.querySelector('pre').textContent = typeof value === 'string' ? value : JSON.stringify(value, null, 2);
    dialog.showModal();
  }
  async function api(operation, extra = {}) {
    const response = await fetch('/api/' + operation, {method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({drawing:doc, selected:[...selection], ...extra})});
    let result;
    try { result = await response.json(); } catch { throw Error('Unexpected server response (HTTP ' + response.status + ').'); }
    if (!response.ok) throw Error(result.error || 'Unable to process this structure.');
    return result;
  }
  function menu(name) {
    return [...document.querySelectorAll('.menu')].find(m => m.querySelector(':scope > button').textContent === name).querySelector('.dropdown');
  }
  function add(name, label, handler) {
    const button = document.createElement('button'); button.textContent = label;
    button.onclick = async () => {
      document.querySelectorAll('.menu').forEach(m => m.classList.remove('open'));
      button.disabled = true;
      try { finishEditing(); await handler(); } catch(error) { show(label, error.message); }
      finally { button.disabled = false; }
    };
    menu(name).append(button);
  }
  add('Structure', 'Check Structure…', async () => {
    const result = await api('validate');
    validationIds = new Set(result.issues.flatMap(i => i.atom_ids)); render();
    show('Structure check', result.summary + '\n\n' + result.issues.map(i => i.severity + ': ' + i.message).join('\n'));
  });
  function applyDrawing(next) { const before = snapshot(); doc = ChemCore.validate(next); commit(before); }
  for (const [operation, label] of [['cleanup','Clean Up Structure'], ['add-hydrogens','Add Explicit Hydrogens'], ['remove-hydrogens','Remove Explicit Hydrogens']]) {
    add('Structure', label, async () => {
      const before = JSON.stringify(doc), result = await api(operation);
      if (JSON.stringify(doc) !== before) throw Error('The drawing changed while processing. Try again.');
      applyDrawing(result.drawing);
      if (result.notes?.length) show(label, result.notes.join('\n')); else notify(label + ' complete.');
    });
  }


  const smilesDialog = document.createElement('dialog');
  smilesDialog.innerHTML = '<form method="dialog"><h2>Insert from SMILES</h2><label for="web-smiles">SMILES string</label><input id="web-smiles" required maxlength="1000" placeholder="CCO for ethanol"><p><button value="insert">Insert</button><button value="cancel" formnovalidate>Cancel</button></p></form>';
  document.body.append(smilesDialog);
  add('Structure', 'Insert from SMILES…', () => { smilesDialog.showModal(); });
  smilesDialog.addEventListener('close', async () => {
    if (smilesDialog.returnValue !== 'insert') return;
    const smiles = smilesDialog.querySelector('input').value.trim(); if (!smiles) return;
    try {
    const fragment = await api('smiles', {smiles}); const before = snapshot(); fitFragmentToBondLength(fragment.atoms, fragment.bonds);
    doc.atoms.push(...fragment.atoms); doc.bonds.push(...fragment.bonds);
    selection = new Set(fragment.atoms.map(a => a.id)); annSelection.clear(); commit(before); fit();
    } catch(error) { show('Insert from SMILES', error.message); }
  });
  add('Object', 'Flatten Selection', () => flattenSelection());
  add('Text', 'Bold', () => { setTextStyle({bold:!activeTextStyle().bold}); });
  add('Text', 'Italic', () => { setTextStyle({italic:!activeTextStyle().italic}); });
  const about = document.querySelector('#aboutDialog');
  about.innerHTML = '<h2>ErezDraw Web</h2><p>Chemical drawing with local browser autosave, editable JSON/MOL files, SVG/PNG export, and server-side RDKit structure checks, cleanup and analysis.</p><p>Drawings stay in this browser unless you download them or run a chemistry command. Chemistry commands send the current structure to this server for processing; drawings are not stored on the server.</p><p>The web version does not yet include all desktop dialogs, NMR/mass spectrum windows, or Word clipboard integration. Copy/paste within a drawing uses an internal clipboard; use file export to transfer between applications.</p><p>GPL-3.0-or-later. Independent software, not affiliated with ChemDraw.</p><button>Close</button>';
  about.querySelector('button').onclick = () => about.close();
  document.querySelectorAll('[data-action=about]').forEach(b => b.textContent = 'About ErezDraw Web');
  document.querySelectorAll('.titlebar > span').forEach(span => span.remove());
  const hint = document.querySelector('.settings-body .hint:last-child');
  if (hint) hint.textContent = 'Use Structure for RDKit checks, cleanup, properties, analysis and SMILES import.';
  document.querySelector('.chip').textContent = 'Browser autosave · Download to keep a copy';
  document.querySelector('.statusbar > span:last-child').textContent = 'Web';
  window.ErezWeb = {api, add, menu, show, applyDrawing};
})();
