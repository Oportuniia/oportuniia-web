// Public examples never open an operation or grant account permissions.
(() => {
  const dialog = document.createElement('dialog');
  dialog.setAttribute('aria-label', 'Acceso a las oportunidades');
  dialog.style.cssText = 'max-width:480px;width:calc(100% - 32px);margin:auto;padding:30px;border:1px solid #57c6e4;border-radius:16px;background:#102d3d;color:#eef7fc';
  dialog.innerHTML = '<h2 style="font-size:24px;color:#fff">Estás viendo una demo</h2><p style="line-height:1.7;margin:18px 0">Cuando iniciemos oficialmente, podrás consultar las oportunidades dentro de MI OPORTUNIIA, según los permisos de tu cuenta.</p><a class="btn" href="/cuenta">Iniciar sesión</a> <a class="btn" href="/cuenta#registro">Crear cuenta gratuita</a><button type="button" style="display:block;margin:22px auto 0;color:#fff">Cerrar</button>';
  document.body.append(dialog);
  dialog.querySelector('button').onclick = () => dialog.close();
  dialog.onclick = event => { if (event.target === dialog) dialog.close(); };
  document.addEventListener('click', event => {
    if (!event.target.closest('#producto .deal')) return;
    event.preventDefault(); event.stopImmediatePropagation(); dialog.showModal();
  }, true);
  document.addEventListener('keydown', event => {
    if (!['Enter', ' '].includes(event.key) || !event.target.closest('#producto .deal')) return;
    event.preventDefault(); event.stopImmediatePropagation(); dialog.showModal();
  }, true);
})();
