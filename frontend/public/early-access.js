export function catalogMessage(state,early=true){
 if(state==='empty')return early?'Las primeras oportunidades están en camino':'Todavía no hay oportunidades publicadas';
 if(state==='no_matches')return 'No hay oportunidades que coincidan con tu búsqueda';
 if(state==='error')return 'No hemos podido cargar las oportunidades. Inténtalo de nuevo.';
 return 'Explora las oportunidades disponibles en tu área privada';
}
if(typeof document!=='undefined'){
 const catalog=document.querySelector('#early-catalog-status');
 const main=document.querySelector('.hero');
 async function load(){
  try{
   const response=await fetch('/api/account/config',{cache:'no-store'});
   if(!response.ok)throw Error('configuration');
   const config=await response.json();
   if(typeof config.early_access!=='boolean')throw Error('configuration');
   if(config.early_access&&main&&!document.querySelector('#early-access-banner')){
    const banner=document.createElement('section');banner.id='early-access-banner';banner.className='early-access-banner';banner.setAttribute('aria-labelledby','early-access-title');
    banner.innerHTML='<span class="early-access-label">OPORTUNIIA · ACCESO ANTICIPADO</span><h2 id="early-access-title">Algo grande está a punto de comenzar</h2><p>Estamos preparando nuestras primeras oportunidades inmobiliarias. El lanzamiento será próximamente. Puedes crear tu cuenta desde ahora y conocer la plataforma.</p><a class="btn" href="/cuenta#registro">Crear mi cuenta gratuita</a><small>El registro gratuito no es una suscripción de pago ni genera cargos.</small>';
    main.insertAdjacentElement('afterend',banner);
   }
   if(catalog){catalog.replaceChildren();const heading=document.createElement('h3');heading.textContent=catalogMessage(config.catalog_state,config.early_access);const paragraph=document.createElement('p');paragraph.textContent=config.catalog_state==='empty'?'Estamos preparando las primeras oportunidades. Mientras tanto, puedes crear tu cuenta gratuita.':config.catalog_state==='error'?'El catálogo no está disponible temporalmente. Puedes seguir utilizando tu cuenta.':'Accede a tu área privada para consultar el catálogo actualizado y la información disponible según tus permisos.';const link=document.createElement('a');link.className='btn';link.href='/mi-oportuniia#oportunidades';link.textContent='Consultar oportunidades';catalog.append(heading,paragraph,link);}
  }catch(error){if(catalog){catalog.replaceChildren();const p=document.createElement('p');p.textContent=catalogMessage('error');const retry=document.createElement('button');retry.type='button';retry.className='btn';retry.textContent='Volver a intentar';retry.onclick=load;catalog.append(p,retry)}}
 }
 if(main||catalog)load();
}
