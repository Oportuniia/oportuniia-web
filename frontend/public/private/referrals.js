import {api,esc} from './api.js';

export async function referrals(page) {
  const data=await api('account/referrals');
  page('Mis referidos',`<section class="card"><h2>Invita con tu enlace o QR</h2><p>Las nuevas altas realizadas con este enlace quedarán asociadas a tu cuenta.</p><label>Tu enlace personal<input id="referral-link" readonly value="${esc(data.link)}"></label><button class="button primary" id="copy-referral">Copiar enlace</button><p id="referral-status" role="status"></p><img src="${esc(data.qr_image)}" width="220" height="220" alt="Tu QR personal de referidos"><p><a class="button" href="${esc(data.qr_image)}" download="mi-qr-oportuniia.svg">Descargar QR</a></p></section><section class="card"><h2>Altas atribuidas</h2><p>${data.items.length} altas${data.limited?' · Se muestran las 100 más recientes':''}. La atribución no concede acceso a datos ni documentos de clientes.</p><ul>${data.items.map(r=>`<li>${esc(r.account_kind||'Cuenta')} · ${esc(r.acquisition?.source)} · ${esc(String(r.created_at||'').slice(0,10))}</li>`).join('')}</ul><p>Los incentivos están pendientes de conexión y validación de cobros. Esta pantalla no muestra importes a cobrar.</p></section>`);
  document.querySelector('#copy-referral').onclick=async()=>{
    try {await navigator.clipboard.writeText(data.link);document.querySelector('#referral-status').textContent='Enlace copiado.';}
    catch {document.querySelector('#referral-link').select();document.querySelector('#referral-status').textContent='Selecciona y copia tu enlace.';}
  };
}
