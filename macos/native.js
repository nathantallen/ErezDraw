/* Native macOS integration around the unchanged Docker application. */
new QWebChannel(qt.webChannelTransport, channel => {
  const native = channel.objects.native;
  window.ErezNative = native;
  const style = document.createElement('style');
  style.textContent = '.menubar,.titlebar{display:none!important}';
  document.head.append(style);
  document.querySelector('.statusbar > span:last-child').textContent = 'macOS';
  const theme = document.getElementById('web-theme');
  window.nativeAppearance = (mode, dark) => {
    theme.value = mode;
    theme.onchange();
    document.documentElement.dataset.appearance = dark ? 'dark' : 'light';
  };
  document.querySelectorAll('[data-action=\"open\"]').forEach(b=>b.onclick=()=>native.openDocument());
  window.ErezWeb.requestSave = () => { finishEditing(); native.save(JSON.stringify(doc)); };
  window.nativeSaveComplete = (name) => {
    doc.name = name; $('docName').value = name; dirty = false; autosave();
    native.saved(JSON.stringify(doc));
  };
  window.nativeRestore = drawing => {
    doc = ChemCore.validate(drawing); updateBondCharges(); updateCentroids();
    $('docName').value = doc.name; selection.clear(); annSelection.clear();
    undoStack = []; redoStack = []; dirty = false; fit();
  };
  document.querySelectorAll('.menu .dropdown button').forEach(b=>{if(b.textContent.trim()==='Save As…')b.onclick=()=>window.ErezWeb.requestSave();});
  const menus = [];
  document.querySelectorAll('.menubar .menu').forEach((menu, mi) => {
    const items = [];
    menu.querySelectorAll('.dropdown button').forEach((button, bi) => {
      button.dataset.nativeCommand = mi + '-' + bi;
      items.push({id:button.dataset.nativeCommand, label:[...button.childNodes].filter(n=>n.nodeName!=='KBD').map(n=>n.textContent).join('').replace(/\s+/g,' ').trim().replace('About ErezDraw Web','About ErezDraw'), action:button.dataset.action || ''});
    });
    menus.push({label:menu.querySelector(':scope > button').textContent, items});
  });
  window.nativeCommand = id => document.querySelector('[data-native-command="'+id+'"]').click();
  const about = document.querySelector('#aboutDialog');
  about.innerHTML = '<h2>ErezDraw for macOS</h2><p>The complete Docker drawing application, packaged with a native Mac shell. Chemistry runs locally. PubChem lookups require an internet connection.</p><p>GPL-3.0-or-later. Independent software, not affiliated with ChemDraw.</p><button>Close</button>';
  about.querySelector('button').onclick=()=>about.close();
  document.addEventListener('keydown', e => {
    if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='o'){e.preventDefault();e.stopImmediatePropagation();native.openDocument();return;}
    if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='p') {e.preventDefault();e.stopImmediatePropagation();native.printDocument();}
  },true);
  let last = null;
  setInterval(() => {
    if(editing||gesture)return;
    const value = JSON.stringify(doc);
    if(value !== last){last = value; native.autosave(value);}
  },500);
  native.ready(JSON.stringify(menus));
});
