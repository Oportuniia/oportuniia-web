// No launch date is promised until confirmed.
(() => {
  if (document.getElementById('launch-notice')) return;
  const style = document.createElement('style');
  style.textContent = `
    .launch-notice{position:fixed;inset:0 0 auto;z-index:110;display:flex;align-items:center;gap:16px;box-sizing:border-box;padding:14px 18px;background:linear-gradient(100deg,#006a80,#13b8bf);color:#fff;box-shadow:0 3px 14px #001a3655;font:600 16px/1.5 Poppins,Arial,sans-serif}
    .launch-window{overflow:hidden;flex:1;min-width:0}.launch-track{display:flex;width:max-content;animation:launch-slide 32s linear infinite}.launch-track span{padding-right:70px;white-space:nowrap}.launch-pause{flex:none;border:1px solid #fff9;border-radius:6px;background:#004957;color:white;padding:7px 10px;font:inherit;font-size:12px;cursor:pointer}
    .launch-notice.paused .launch-track,.launch-notice:hover .launch-track,.launch-notice:focus-within .launch-track{animation-play-state:paused}
    @keyframes launch-slide{from{transform:translateX(0)}to{transform:translateX(-50%)}}
    .launch-registration-warning{padding:20px;margin:0 0 22px;border:2px solid #b42318;border-radius:10px;background:#fff0ef;color:#8c1d18;font:500 16px/1.6 Poppins,Arial,sans-serif}.launch-registration-warning strong{display:block;font-size:19px;margin-bottom:6px}
    @media(max-width:600px){.launch-notice{font-size:14px;padding:12px;gap:8px}.launch-pause{font-size:11px}}
    @media(prefers-reduced-motion:reduce){.launch-track{animation:none;width:auto}.launch-track span{white-space:normal;padding:0}.launch-track span+span{display:none}.launch-pause{display:none}}
  `;
  document.head.append(style);
  const notice = document.createElement('aside');
  notice.id = 'launch-notice'; notice.className = 'launch-notice';
  notice.setAttribute('aria-label','Próximo lanzamiento de OPORTUNIIA');
  const viewport = document.createElement('div'); viewport.className='launch-window';
  const track = document.createElement('div'); track.className='launch-track';
  const text = 'PRÓXIMAMENTE · Estamos preparando OPORTUNIIA. Anunciaremos aquí la apertura de la plataforma. ·';
  for(let i=0;i<2;i++){const item=document.createElement('span');item.textContent=text;if(i)item.setAttribute('aria-hidden','true');track.append(item);}
  viewport.append(track);
  const pause=document.createElement('button');pause.type='button';pause.className='launch-pause';pause.textContent='Pausar aviso';pause.setAttribute('aria-pressed','false');
  pause.onclick=()=>{const stopped=notice.classList.toggle('paused');pause.textContent=stopped?'Animar aviso':'Pausar aviso';pause.setAttribute('aria-pressed',String(stopped));};
  notice.append(viewport,pause);document.body.prepend(notice);
  const spacer=document.createElement('div');spacer.setAttribute('aria-hidden','true');notice.after(spacer);
  const header=document.querySelector('header');
  const layout=()=>{const height=notice.getBoundingClientRect().height;spacer.style.height=`${height}px`;if(header&&['fixed','sticky'].includes(getComputedStyle(header).position))header.style.top=`${height}px`;};
  new ResizeObserver(layout).observe(notice);layout();
  const status=document.getElementById('reg-status');
  if(status){const form=status.closest('form');const warning=document.createElement('aside');warning.className='launch-registration-warning';warning.setAttribute('aria-label','Aviso de lanzamiento');const title=document.createElement('strong');title.textContent='La plataforma todavía no está abierta';const message=document.createElement('span');message.textContent='Estamos preparando el lanzamiento. El registro de cuentas aún no está habilitado. No se guardarán datos ni se activarán servicios desde este formulario.';warning.append(title,message);form.before(warning);}
})();
