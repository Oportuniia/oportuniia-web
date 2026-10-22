// Launch date deliberately unset. Add a countdown only after a confirmed date.
(() => {
  if (document.getElementById('launch-notice')) return;
  const style = document.createElement('style');
  style.textContent = '.launch-notice{box-sizing:border-box;position:relative;z-index:30;width:100%;padding:14px 24px;background:#0b1a28;color:#fff;text-align:center;font:400 14px/1.6 Poppins,Arial,sans-serif;border-bottom:2px solid #33a9bb}.launch-notice strong{display:inline-block;margin-right:12px;color:#8de0d7;font-weight:600;letter-spacing:.04em}.launch-notice span{display:inline}@media(max-width:600px){.launch-notice{padding:12px 18px;font-size:12px}.launch-notice strong{display:block;margin:0 0 3px}}';
  document.head.appendChild(style);
  const notice = document.createElement('aside');
  notice.id = 'launch-notice';
  notice.className = 'launch-notice';
  notice.setAttribute('aria-label', 'Próximo lanzamiento');
  const title = document.createElement('strong');
  title.textContent = 'PRÓXIMAMENTE';
  const message = document.createElement('span');
  message.textContent = 'Estamos preparando OPORTUNIIA. La plataforma estará operativa próximamente. Anunciaremos aquí la fecha de apertura.';
  notice.append(title, message);
  document.body.prepend(notice);
})();
