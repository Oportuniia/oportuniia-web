import {mountSecretary} from './secretary.js';
import {esc} from './api.js';

// Only the authenticated download route can release an antivirus-clean file.
// OCR is an aid to reading, never an approval of identity or an entitlement.
export function mountDocumentOCR(host, documents=[],onRefresh=()=>{}){
  let dispose=null,controller=null,destroyed=false;
  host.innerHTML=`<section class="card"><h2>Leer mis documentos mediante OCR</h2><p>El análisis de seguridad debe terminar antes de leer el archivo. La lectura no aprueba tu identidad ni modifica los datos del perfil.</p><button type="button" class="button" id="document-ocr-refresh">Actualizar estado del antivirus</button><div class="row">${documents.map((d,i)=>`<button type="button" class="button" data-read="${i}" ${d.scan_state==='CLEAN'?'':'disabled'}>${esc(d.category==='identity'?'Documento de identidad':d.category==='representative_identity'?'DNI del administrador o socio':d.category==='company_tax_document'?'CIF / NIF de empresa':'Documento')} · ${d.scan_state==='CLEAN'?'Leer documento':'No disponible para OCR'}</button>`).join('')||'<p>Aporta un documento en tu perfil para comenzar.</p>'}</div><p role="status" id="document-ocr-status"></p><div id="document-ocr-reader"></div></section>`;
  const status=host.querySelector('#document-ocr-status'),reader=host.querySelector('#document-ocr-reader');
  host.querySelector('#document-ocr-refresh').onclick=()=>onRefresh();
  host.querySelectorAll('[data-read]').forEach(button=>button.onclick=async()=>{
    const doc=documents[Number(button.dataset.read)];
    if(doc.scan_state!=='CLEAN'||controller)return;
    dispose?.();reader.replaceChildren();controller=new AbortController();
    const timer=setTimeout(()=>controller?.abort(),60000);
    button.disabled=true;status.textContent='Recuperando tu documento protegido…';
    try{
      const response=await fetch('/api/investor/personal-documents/'+encodeURIComponent(doc.document_id),{credentials:'same-origin',cache:'no-store',signal:controller.signal});
      if(!response.ok)throw Error(response.status===401?'La sesión ha caducado. Vuelve a iniciar sesión.':'El documento no está disponible o aún no ha superado el análisis de seguridad.');
      const blob=await response.blob();
      if(!blob.size||blob.size>20*1024*1024)throw Error('El documento supera el límite de 20 MB o está vacío.');
      if(!['application/pdf','image/png','image/jpeg','image/webp'].includes(blob.type))throw Error('Formato de documento no admitido.');
      if(destroyed)return;
      const file=new File([blob],'documento-personal',{type:blob.type});
      dispose=mountSecretary(reader,{initialFiles:[file]});
      reader.querySelector('.eyebrow').textContent='LECTURA DE TU DOCUMENTO';
      reader.querySelector('h2').textContent='Comprueba el texto leído antes de usarlo.';
      reader.querySelector('#secretary-files').closest('label').hidden=true;
      status.textContent='Documento recuperado tras el análisis limpio. La lectura se realiza en este navegador.';
      reader.querySelector('#secretary-process').click();
    }catch(error){if(!destroyed)status.textContent=error.name==='AbortError'?'Se ha interrumpido la descarga. Puedes volver a intentarlo.':error.message;}
    finally{clearTimeout(timer);controller=null;if(!destroyed)button.disabled=false;}
  });
  return ()=>{destroyed=true;controller?.abort();dispose?.();};
}
