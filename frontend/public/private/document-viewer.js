import {esc} from './api.js';
export function documentViewer(host){
 let controller=null,task=null,objectUrl=null,generation=0;
 function close(){generation++;controller?.abort();task?.destroy();task=null;if(objectUrl)URL.revokeObjectURL(objectUrl);objectUrl=null;host.replaceChildren()}
 async function open(url,title='Documento recibido'){
  close();const current=generation;controller=new AbortController();const activeController=controller;
  host.innerHTML='<section class="card"><h3>Abriendo documento…</h3><p role="status">Preparando la vista del original.</p></section>';host.scrollIntoView({behavior:'smooth',block:'start'});
  const timeout=setTimeout(()=>activeController.abort(),60000);
  try{
   const r=await fetch(url,{credentials:'same-origin',cache:'no-store',signal:controller.signal});
   if(!r.ok)throw Error(r.status===401?'Tu sesión ha caducado. Vuelve a entrar.':r.status===403?'Esta cuenta no tiene permiso para consultar este documento.':'No se puede abrir el documento ahora. Puedes volver a intentarlo.');
   const blob=await r.blob();if(current!==generation)return;
   if(!blob.size||blob.size>20*1024*1024)throw Error('El archivo no tiene un tamaño admitido.');
   const pdf=blob.type.includes('pdf'),image=blob.type.startsWith('image/');if(!pdf&&!image)throw Error('El servidor no ha devuelto el documento. Actualiza la página e inténtalo de nuevo.');
   objectUrl=URL.createObjectURL(blob);
   host.innerHTML=`<section class="card"><h3>${esc(title)}</h3><p><a class="button" href="${objectUrl}" download="documento${pdf?'.pdf':blob.type.includes('jpeg')?'.jpg':'.png'}">Descargar original</a> <button class="button" type="button" data-close-document>Cerrar documento</button></p><div data-original></div></section>`;
   host.querySelector('[data-close-document]').onclick=close;const view=host.querySelector('[data-original]');
   if(image){const img=new Image();img.alt='Documento original aportado';img.src=objectUrl;img.style='display:block;max-width:100%;max-height:750px;object-fit:contain;margin:auto';view.append(img);return}
   const E=await import('./vendor/secretary-engines.js');if(current!==generation)return;
   E.GlobalWorkerOptions.workerSrc=new URL('./vendor/pdf.worker.min.mjs',import.meta.url).href;
   task=E.getDocument({data:new Uint8Array(await blob.arrayBuffer()),isEvalSupported:false});const doc=await task.promise;if(current!==generation)return;
   let page=1;view.innerHTML='<div class="row"><button type="button" class="button" data-prev>Anterior</button><span data-page></span><button type="button" class="button" data-next>Siguiente</button></div><canvas style="display:block;max-width:100%;height:auto;margin-top:12px"></canvas>';
   async function draw(){if(current!==generation)return;view.querySelectorAll('button').forEach(b=>b.disabled=true);const p=await doc.getPage(page),v=p.getViewport({scale:Math.min(1.5,1000/p.getViewport({scale:1}).width)}),canvas=view.querySelector('canvas');canvas.width=v.width;canvas.height=v.height;await p.render({canvasContext:canvas.getContext('2d'),viewport:v}).promise;if(current!==generation)return;view.querySelector('[data-page]').textContent=`Página ${page} de ${doc.numPages}`;view.querySelector('[data-prev]').disabled=page===1;view.querySelector('[data-next]').disabled=page===doc.numPages;p.cleanup()}
   view.querySelector('[data-prev]').onclick=()=>{page--;draw().catch(fail)};view.querySelector('[data-next]').onclick=()=>{page++;draw().catch(fail)};await draw();
  }catch(e){if(current===generation)fail(e)}finally{clearTimeout(timeout)}
 }
 function fail(e){host.innerHTML=`<section class="card"><p role="alert">${esc(e.name==='AbortError'?'La apertura está tardando demasiado. Vuelve a intentarlo.':e.message)}</p><button type="button" class="button">Cerrar</button></section>`;host.querySelector('button').onclick=close}
 return {open,close};
}
