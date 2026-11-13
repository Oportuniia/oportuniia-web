import {api, post, esc} from './api.js';

export function mountRequest(root, operations = []) {
  root.innerHTML = `<section class="card"><h2>Cuéntanos qué necesitas</h2><p>Revisaremos tu petición y te responderemos en Notificaciones. Si requiere un encargo de pago, recibirás su alcance y presupuesto antes de contratar. Enviar esta solicitud no genera cargos.</p><form class="form-grid"><label class="full">Operación (opcional)<select name="operation"><option value="">Consulta general</option>${operations.map(o=>`<option value="${esc(o.op_ref)}">${esc(o.op_ref)}</option>`).join('')}</select></label><label class="full">Tu petición<textarea name="body" required minlength="10" maxlength="3800"></textarea></label><button class="button primary">Enviar petición</button><p role="status" aria-live="polite"></p></form></section>`;
  const form = root.querySelector('form'), status = root.querySelector('[role=status]');
  form.onsubmit = async event => {
    event.preventDefault(); const button = form.querySelector('button'); button.disabled = true;
    try {
      const result = await post('investor/messages', {op_ref: form.elements.operation.value, body: 'Petición a la carta\n'+form.elements.body.value.trim()});
      if (!result.saved) throw Error('No se ha confirmado el guardado.');
      form.reset(); status.textContent = 'Petición guardada. Puedes consultarla y ver nuestra respuesta en Notificaciones.';
    } catch (error) { status.textContent = error.message; }
    finally { button.disabled = false; }
  };
}

export async function mountTeamInbox(root) {
  let offset = 0;
  async function load() {
    const result = await api('account/team-messages?offset='+offset);
    root.innerHTML = `<h2>Consultas de clientes</h2><p>Responde desde aquí. La respuesta queda en el área privada; el aviso por correo respeta las preferencias del cliente.</p>${result.items.map((item,i)=>`<article class="card"><h3>${esc(item.name)}${item.op_ref?' · '+esc(item.op_ref):''}</h3><p>${item.state==='PENDING_TEAM_REPLY'?'Pendiente de respuesta':'Respondida'}</p>${item.messages.map(m=>`<p style="white-space:pre-wrap"><strong>${m.sender==='OPORTUNIIA'?'OPORTUNIIA':'Cliente'}:</strong> ${esc(m.body)}</p>`).join('')}<form data-index="${i}" class="form-grid"><label class="full">Respuesta<textarea name="body" required maxlength="4000"></textarea></label><button class="button primary">Enviar respuesta</button><p role="status" aria-live="polite"></p></form></article>`).join('') || '<p>No hay consultas en esta página.</p>'}<div class="row"><button class="button" data-prev ${offset===0?'disabled':''}>Anterior</button><button class="button" data-next ${result.next_offset===null?'disabled':''}>Siguiente</button></div>`;
    root.querySelector('[data-prev]').onclick = ()=>{offset=Math.max(0,offset-25);load().catch(showError)};
    root.querySelector('[data-next]').onclick = ()=>{offset=result.next_offset;load().catch(showError)};
    root.querySelectorAll('form').forEach(form=>{
      let eventId = crypto.randomUUID(), previousBody = '';
      form.onsubmit = async event=>{
        event.preventDefault(); const button=form.querySelector('button'), status=form.querySelector('[role=status]');
        const body=form.elements.body.value.trim(); if(!body){status.textContent='Escribe la respuesta.';return}
        if(previousBody && previousBody!==body)eventId=crypto.randomUUID();previousBody=body;button.disabled=true;
        try {
          await post('account/team-messages/reply',{thread_id:result.items[Number(form.dataset.index)].thread_id,event_id:eventId,body});
          await load();
        } catch(error){status.textContent=error.message;button.disabled=false}
      };
    });
  }
  function showError(error){const p=document.createElement('p');p.setAttribute('role','alert');p.textContent=error.message;root.prepend(p)}
  await load();
}
