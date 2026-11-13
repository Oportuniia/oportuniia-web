// Visual state follows server permissions; it never grants access or charges.
export function accessColors(a={}) {
  return {identity:a.identity_status==='VERIFIED',dossier:a.dossier_status==='APPROVED',enabled:a.contracting?.verified===true,active:a.premium===true&&a.contracting?.verified===true};
}
export function paintAccess(host,a={}) {
  const cards=host.querySelectorAll('.access-stages>div');
  if(cards.length!==4)return;
  const s=accessColors(a);
  cards[1].classList.toggle('stage-approved',s.identity);
  cards[2].classList.toggle('stage-approved',s.dossier);
  cards[3].classList.toggle('stage-enabled',s.enabled&&!s.active);
  cards[3].classList.toggle('premium-active',s.active);
  const description=cards[3].querySelector('small');
  if(s.active)description.innerHTML='Premium activo<br><span class="premium-permissions">Cada operación requiere sus permisos</span>';
  else description.textContent=s.enabled?'Perfil habilitado · Premium disponible para contratar':'Bloqueados hasta 100% y verificación';
}
