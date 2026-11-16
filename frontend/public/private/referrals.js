import {api,esc} from './api.js';

export async function referrals(page) {
  const data=await api('account/referrals');
  const wallet=await api('account/referrals/bonuses');
  const message=(data.sender_name?'Hola, soy '+data.sender_name+'. ':'Hola. ')+'Te invito a conocer OPORTUNIIA y sus oportunidades de inversión. Puedes crear tu cuenta desde mi enlace personal: '+data.link;
  page('Mis referidos',`<section class="card"><h2>Invita con tu enlace o QR</h2><p>Las nuevas altas realizadas con este enlace quedarán asociadas a tu cuenta.</p><label>Tu enlace personal<input id="referral-link" readonly value="${esc(data.link)}"></label><button class="button primary" id="copy-referral">Copiar enlace</button><p><a class="button" target="_blank" rel="noopener noreferrer" href="https://wa.me/?text=${encodeURIComponent(message)}">Preparar mensaje de WhatsApp</a></p><p id="referral-status" role="status"></p><img src="${esc(data.qr_image)}" width="220" height="220" alt="Tu QR personal de referidos"><p><a class="button" href="${esc(data.qr_image)}" download="mi-qr-oportuniia.svg">Descargar QR</a></p></section><section class="card"><h2>Altas atribuidas</h2><p>${data.items.length} altas${data.limited?' · Se muestran las 100 más recientes':''}. La atribución no concede acceso a datos ni documentos de clientes.</p><ul>${data.items.map(r=>`<li>${esc(r.account_kind||'Cuenta')} · ${esc(r.acquisition?.source)} · ${esc(String(r.created_at||'').slice(0,10))}</li>`).join('')}</ul><p>Los incentivos están pendientes de conexión y validación de cobros. Esta pantalla no muestra importes a cobrar.</p></section>`);
  document.querySelector('#copy-referral').onclick=async()=>{
    try {await navigator.clipboard.writeText(data.link);document.querySelector('#referral-status').textContent='Enlace copiado.';}
    catch {document.querySelector('#referral-link').select();document.querySelector('#referral-status').textContent='Selecciona y copia tu enlace.';}
  };
  const section=document.createElement('section');
  section.className='card';
  section.innerHTML=`<h2>Tus bonos Premium</h2><p><strong>${esc(wallet.available_bonuses)} bonos disponibles</strong></p><p>Tú eliges: un bono para una mensualidad al 50%, o tres bonos para una mensualidad gratuita. Los bonos consumidos no vuelven a contar.</p><p>El canje en facturación está pendiente de conexión. No se aplicará ningún descuento ni se consumirá tu saldo desde esta pantalla.</p><h2>Conoce cada figura</h2><ul>${[['partner','Partner / generador de negocio'],['suscriptor','Suscriptor / agencia'],['equipo','Mi equipo / adherido'],['colaborador','Colaborador externo'],['inversor','Inversor']].map(([id,title])=>`<li><a href="/api/account/referrals/dossiers/${id}" target="_blank" rel="noopener">${esc(title)} · PDF</a></li>`).join('')}</ul>`;
  document.querySelector('#copy-referral').closest('section').after(section);
}
