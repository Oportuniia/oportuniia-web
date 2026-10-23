(()=>{
/* Navegación unificada: cabecera oscura arriba, translúcida al desplazarse, logo original y página activa. */
(function(){
 const links=[['/nuestra-filosofia','Nuestra filosofía'],['/como-funciona','Cómo funciona'],['/oportunidades#producto','Oportunidades'],['/grupo-oportuniia','Grupo OPORTUNIIA'],['/tecnologia','Tecnología'],['/contacto','Contacto'],['/servicers','Canal profesional']];
 const current=location.pathname.replace(/\.html$/,'').replace(/\/$/,'')||'/';
 const header=document.querySelector('header');if(!header)return;
 if(current==='/tecnologia'){
   const nav=header.querySelector('.nav');if(nav){nav.innerHTML='<a class="brand" href="/"><img src="/oportuniia-logo.webp?v=20260929-web1" alt="OPORTUNIIA"></a><nav class="menu">'+links.map(([u,t])=>'<a href="'+u+'">'+t+'</a>').join('')+'</nav><a class="login" href="/acceso">Login / Registro</a><button class="burger" id="opp-burger" type="button" aria-label="Abrir menú" aria-expanded="false">☰</button>';}
   const mobile=document.createElement('div');mobile.id='opp-mobile-nav';mobile.className='mobile';mobile.innerHTML=links.map(([u,t])=>'<a href="'+u+'">'+t+'</a>').join('')+'<a class="login" href="/acceso">Login / Registro</a>';header.appendChild(mobile);
   const btn=header.querySelector('#opp-burger');btn?.addEventListener('click',()=>{const open=mobile.classList.toggle('open');btn.setAttribute('aria-expanded',String(open))});
 }
 const style=document.createElement('style');style.textContent=`
 header,header.sc{background:#081a2a!important;border-bottom:1px solid rgba(255,255,255,.12)!important;backdrop-filter:none!important;transition:background .35s,border-color .35s,backdrop-filter .35s!important}
 header.opp-scrolled,header.sc.opp-scrolled{background:rgba(255,255,255,.12)!important;border-bottom:1px solid rgba(19,55,78,.13)!important;backdrop-filter:blur(22px) saturate(135%)!important;-webkit-backdrop-filter:blur(22px) saturate(135%)!important}
 header .brand img,header .brand-logo-img,header .nav img{filter:brightness(0) invert(1)!important;transition:filter .35s!important}
 header.opp-scrolled .brand img,header.opp-scrolled .brand-logo-img,header.opp-scrolled .nav img{filter:none!important}
 header .menu a,header .navitem>a,header .back{font-weight:700!important;color:#f5f9fc!important}
 header.opp-scrolled .menu a,header.opp-scrolled .navitem>a,header.opp-scrolled .back{color:#102a3e!important}
 header .menu a.active,header .navitem>a.active,header .mobile a.active{font-weight:800!important;text-decoration:underline;text-decoration-thickness:2px;text-underline-offset:7px}
 header .burger{color:#fff!important}header.opp-scrolled .burger{color:#102a3e!important}
 header .burger span,header .burger span::before,header .burger span::after{background:#fff!important}
 header.opp-scrolled .burger span,header.opp-scrolled .burger span::before,header.opp-scrolled .burger span::after{background:#102a3e!important}
 header .nav{min-height:70px}header .menu{display:flex;align-items:center;gap:clamp(9px,1.25vw,22px)}
 header .menu a{font-weight:700!important;font-size:clamp(10px,.85vw,13px);white-space:nowrap;text-decoration:none}
 header .menu a.active{font-weight:900!important;text-decoration:underline}
 header .login{white-space:nowrap}
 header .mobile,#opp-mobile-nav{display:none}
 header .mobile.open,#opp-mobile-nav.open{display:grid!important;gap:14px;padding:20px;background:#0b2437;color:#fff}
 header .mobile a{font-weight:700!important}header .mobile a.active{font-weight:900!important}
 @media(max-width:1050px){header .menu{display:none!important}header .burger{display:block!important}header .nav{justify-content:space-between}header .brand{margin-right:auto}}
 `;document.head.appendChild(style);
 header.querySelectorAll('a[href]').forEach(a=>{const u=new URL(a.href,location.origin);if((u.pathname.replace(/\/$/,'')===current&&current!=='/')||(u.pathname==='/oportunidades'&&location.hash==='#producto'))a.classList.add('active')});
 const sync=()=>header.classList.toggle('opp-scrolled',window.scrollY>35);window.addEventListener('scroll',sync,{passive:true});sync();
})();
const p=location.pathname.replace(/\.html$/,'').replace(/\/$/,'')||'/';document.querySelectorAll('a[href]').forEach(a=>{try{const u=new URL(a.href,location.origin);if(u.origin===location.origin&&u.pathname.replace(/\/$/,'')===p)a.classList.add('active')}catch(e){}});document.querySelectorAll('.deal[data-href],.card[data-href],.entry[data-href]').forEach(el=>{el.tabIndex=0;const go=()=>{if(el.dataset.href)location.href=el.dataset.href};el.addEventListener('click',e=>{if(e.target.closest('a,button,input,select,textarea'))return;go()});el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();go()}})});document.querySelectorAll('[data-premium-gate]').forEach(el=>el.addEventListener('click',e=>{e.preventDefault();const g=document.getElementById('opp-premium-gate');if(g)g.classList.add('open')}));const g=document.getElementById('opp-premium-gate');if(g){g.addEventListener('click',e=>{if(e.target===g||e.target.closest('[data-close-gate]'))g.classList.remove('open')});addEventListener('keydown',e=>{if(e.key==='Escape')g.classList.remove('open')})}

const trustTemplate=document.getElementById('opportunities-trust-template');
if(trustTemplate){
 if(p==='/oportunidades')trustTemplate.replaceWith(trustTemplate.content);
 else trustTemplate.remove();
}

if(p==='/oportunidades'){
 document.body.classList.add('catalog-page');
 document.querySelectorAll('body>section').forEach(s=>{if(s.id!=='producto')s.hidden=true});
 const producto=document.getElementById('producto'); if(producto){producto.hidden=false;producto.style.paddingTop='84px'}
 const acuerdosBtn=[...document.querySelectorAll('.ms-btn')].find(b=>b.dataset.mode==='acuerdos');
 if(!document.getElementById('opp-premium-gate')){
   const gate=document.createElement('div');gate.id='opp-premium-gate';gate.className='opp-gate';gate.innerHTML='<div class="opp-gate-card"><div style="font-size:11px;letter-spacing:.2em;color:#57c6e4">UNIVERSO ACUERDOS · PREMIUM</div><h3>Más control. Menos incertidumbre.</h3><p>Este catálogo está reservado para perfiles Premium autorizados. Activa Premium para acceder a operaciones estructuradas, perímetros personalizados y documentación ampliada.</p><a class="btn" href="/premium">Activar Premium</a><button data-close-gate style="display:block;margin:18px auto 0;color:#9db4c2">Cerrar</button></div>';document.body.appendChild(gate);gate.addEventListener('click',e=>{if(e.target===gate||e.target.closest('[data-close-gate]'))gate.classList.remove('open')});
 }
}
})();