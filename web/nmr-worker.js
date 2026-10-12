importScripts('/nmr/predictor.js');
onmessage = event => {
  try { postMessage({rows:ErezNMR.predict(event.data.molfile,event.data.nucleus)}); }
  catch (error) { postMessage({error:error.message}); }
};
