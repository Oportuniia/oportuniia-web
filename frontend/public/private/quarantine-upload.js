import {post} from './api.js';

export async function uploadToQuarantine(file, category){
  if(!file.size || file.size>20*1024*1024)throw Error('El archivo debe ocupar entre 1 byte y 20 MB, también si es un original.');
  if(!['application/pdf','image/jpeg','image/png'].includes(file.type))throw Error('Admite PDF, JPG o PNG. No se admiten archivos ZIP.');
  const hash=await crypto.subtle.digest('SHA-256',await file.arrayBuffer());
  const sha256=Array.from(new Uint8Array(hash),b=>b.toString(16).padStart(2,'0')).join('');
  const intent=await post('investor/personal-documents/upload-intent',{category,mime:file.type,size:file.size,sha256});
  const destination=new URL(intent.upload.url);
  if(destination.protocol!=='https:' || !destination.hostname.endsWith('.amazonaws.com'))throw Error('Destino de cuarentena no válido.');
  const form=new FormData();
  Object.entries(intent.upload.fields).forEach(([key,value])=>form.append(key,value));
  form.append('file',file);
  const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),120000);
  try{
    const response=await fetch(destination.href,{method:'POST',body:form,credentials:'omit',signal:controller.signal});
    if(!response.ok)throw Error('La cuarentena no ha aceptado el archivo. Inténtalo de nuevo.');
  }finally{clearTimeout(timer)}
  // Scan status is server-derived; browser success never certifies safety or identity.
  return {document_id:intent.document_id,name:'Documento recibido · pendiente de análisis',scan_state:'QUARANTINED'};
}

export async function refreshQuarantine(documents){
  for(const doc of documents){
    if(doc.scan_state!=='QUARANTINED' && doc.scan_state!=='PROMOTING')continue;
    try{await post('investor/personal-documents/'+encodeURIComponent(doc.document_id)+'/scan-status')}catch{/* Keep pending on transport failure. */}
  }
}
