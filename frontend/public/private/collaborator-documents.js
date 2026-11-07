import {api,esc} from './api.js';

export async function mountCollaboratorDocuments(host){
  try{
    const data=await api('collaborator/legal-templates');
    host.innerHTML=`<article class="card"><h2>Modalidad A · Reconocimiento previo</h2><p>El inversor y el colaborador deben firmar antes de formalizar la operación; como límite, en notaría y antes de la firma. Sin ambas firmas en plazo no nace el derecho al 50 % de los honorarios netos efectivamente cobrados por OPORTUNIIA.</p><p>Los honorarios futuros acordados entre inversor y colaborador son independientes. Descargar esta matriz no acredita que el acuerdo esté firmado.</p></article>`+data.items.map(d=>`<article class="card"><h2>${esc(d.title)}</h2><p>Versión ${esc(data.version)} · Para completar y firmar.</p><a class="button primary" href="${esc(d.url)}">Descargar PDF</a></article>`).join('');
  }catch(error){host.innerHTML=`<article class="card"><h2>No se han podido cargar los documentos</h2><p>${esc(error.message)}</p></article>`;}
}
