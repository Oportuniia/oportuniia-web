/* Shared public navigation; private navigation belongs to the private app. */
(()=>{
const links=[['/nuestra-filosofia','Nuestra filosofía'],['/como-funciona','Cómo funciona'],['/oportunidades#producto','Oportunidades'],['/grupo-oportuniia','Grupo OPORTUNIIA'],['/tecnologia','Tecnología'],['/contacto','Contacto'],['/servicers','Canal profesional']];
const header=document.querySelector('body>header');if(!header)return;
header.classList.add('opp-public-header');
const path=location.pathname.replace(/\/$/,'')||'/';
const nav=document.createElement('div');nav.className='nav';
nav.innerHTML='<a class="brand" href="/"><img src="/oportuniia-logo.webp?v=20260929-web1" alt="OPORTUNIIA"></a><nav class="menu" aria-label="Navegación principal">'+links.map(([href,label])=>'<a href="'+href+'"'+(new URL(href,location.origin).pathname===path?' aria-current="page" class="opp-current"':'')+'>'+label+'</a>').join('')+'</nav><a class="login" href="/acceso">Login / Registro</a><button id="public-menu-toggle" class="burger" type="button" aria-expanded="false" aria-controls="public-mobile-menu" aria-label="Abrir menú">☰</button>';
const mobile=document.createElement('nav');mobile.id='public-mobile-menu';mobile.className='mobile';mobile.setAttribute('aria-label','Navegación móvil');mobile.hidden=true;
mobile.innerHTML=links.map(([href,label])=>'<a href="'+href+'">'+label+'</a>').join('')+'<a href="/premium">Premium</a><a href="/acceso">MI OPORTUNIIA · Acceso</a>';
header.replaceChildren(nav,mobile);const toggle=nav.querySelector('button');
function close(){mobile.hidden=true;mobile.classList.remove('open');toggle.setAttribute('aria-expanded','false')}
toggle.onclick=()=>{const open=toggle.getAttribute('aria-expanded')!=='true';toggle.setAttribute('aria-expanded',String(open));mobile.hidden=!open;mobile.classList.toggle('open',open)};
mobile.addEventListener('click',e=>{if(e.target.closest('a'))close()});addEventListener('keydown',e=>{if(e.key==='Escape'){close();toggle.focus()}});addEventListener('resize',()=>{if(innerWidth>1050)close()});
// One approved footer resource for static pages and React routes.
fetch('/public-chrome.json').then(r=>{if(!r.ok)throw Error('footer');return r.json()}).then(config=>{
 let footer=document.querySelector('body>footer');if(!footer){footer=document.createElement('footer');document.body.append(footer)}
 footer.className='opp-public-footer';footer.innerHTML=config.footerHtml;
}).catch(()=>{ /* The existing approved footer remains visible on failure. */ });
})();
