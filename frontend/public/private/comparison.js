import {esc} from './api.js';
const fields=[['Municipio','municipio_name'],['Provincia','provincia_name'],['Tipo de activo','asset_type'],['Precio','price'],['ROI','roi'],['Plazo','timeframe'],['Fase judicial','phase']];
export function comparisonCard(item){
 const visible=item.locked?fields.filter(([,key])=>['municipio_name','roi','phase'].includes(key)):fields;
 return `<article class="card"><h3>${esc(item.locked?item.municipio_name||'Operación':item.title||item.op_ref)}</h3><dl>${visible.map(([label,key])=>`<dt>${label}</dt><dd>${esc(item[key]??'Pendiente de confirmar')}</dd>`).join('')}</dl>${item.locked?'<p>Completa la identificación para solicitar más información.</p>':''}</article>`;
}
export function mountComparison(host,items=[]){
 host.innerHTML=`<section class="card"><h2>Comparar operaciones</h2><p>Elige dos operaciones para verlas juntas. Se muestran únicamente los datos disponibles para tu perfil.</p>${items.length<2?'<p>Necesitas al menos dos operaciones disponibles para comparar.</p>':`<div class="comparison-toolbar">${['Primera operación','Segunda operación'].map((label,n)=>`<label class="field">${label}<select data-comparison="${n}"><option value="">Seleccionar…</option>${items.map((item,i)=>`<option value="${i}">${esc(item.locked?item.municipio_name||'Operación':item.title||item.op_ref)} · ${i+1}</option>`).join('')}</select></label>`).join('')}</div><p role="status" data-comparison-status></p><div class="comparison-grid" data-comparison-results></div>`}</section>`;
 if(items.length<2)return;
 const selects=[...host.querySelectorAll('select')],status=host.querySelector('[data-comparison-status]'),results=host.querySelector('[data-comparison-results]');
 selects.forEach(select=>select.onchange=()=>{
  results.replaceChildren();const [a,b]=selects.map(s=>s.value);
  if(a===''||b===''){status.textContent='Selecciona las dos operaciones.';return}
  if(a===b){status.textContent='Selecciona dos operaciones diferentes.';return}
  status.textContent='Comparación de dos operaciones.';
  results.innerHTML=[items[Number(a)],items[Number(b)]].map(comparisonCard).join('');
 });
}
