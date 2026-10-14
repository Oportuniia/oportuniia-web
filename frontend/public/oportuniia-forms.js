(()=>{
const login=document.getElementById('demo-login');
if(login){
 const status=document.getElementById('login-status');status.setAttribute('role','status');status.tabIndex=-1;
 login.addEventListener('submit',e=>{e.preventDefault();const email=login.querySelector('input[type=email]').value.trim().toLowerCase(),password=login.querySelector('input[type=password]').value;
 if(email!=='demo@oportuniia.com'||password!=='OportuniiaDemo2026!'){status.textContent='Este acceso es de prueba. Puedes explorar la DEMO con el enlace inferior, sin contraseña.';return;}
 try{sessionStorage.setItem('opp_demo_access','yes');location.assign('/mi-oportuniia.html?demo=1')}catch{status.textContent='No se pudo guardar el acceso de prueba. Utiliza el enlace directo a la DEMO.'}
 });
 const forgot=login.querySelector('a[href="#"]');if(forgot){forgot.href='#login-status';forgot.onclick=e=>{e.preventDefault();status.textContent='La recuperación de contraseña estará disponible con el acceso real. Puedes explorar la DEMO sin contraseña.';status.focus()}}
 const remember=login.querySelector('input[type=checkbox]');if(remember){remember.id='demo-remember';remember.closest('label').lastChild.textContent=' Recordar acceso DEMO'}
 const direct=document.createElement('a');direct.className='opp-demo-entry';direct.href='/mi-oportuniia.html?demo=1';direct.textContent='Explorar MI OPORTUNIIA · DEMO';direct.onclick=()=>{try{if(remember?.checked)localStorage.setItem('opp_demo_remember','yes');else localStorage.removeItem('opp_demo_remember')}catch{}};login.after(direct);
}
const register=document.getElementById('demo-register');
if(register){
 const params=new URLSearchParams(location.search),select=register.querySelector('select');const requested=params.get('perfil');if(requested&&[...select.options].some(o=>o.value===requested))select.value=requested;
 const status=document.getElementById('reg-status');status.setAttribute('role','status');
 register.addEventListener('submit',e=>{e.preventDefault();const inputs=register.querySelectorAll('input');const draft={id:'ALTA-DEMO-'+Date.now(),name:inputs[0].value.trim(),email:inputs[1].value.trim(),profile:select.value,state:'Pendiente de revisión (DEMO)',createdAt:new Date().toISOString()};
 try{sessionStorage.setItem('opp_demo_registration',JSON.stringify(draft));status.textContent='Solicitud DEMO guardada en esta sesión: '+draft.id+'. Puedes recuperarla o eliminarla aquí. No se ha enviado ni activado ninguna cuenta.';showActions()}catch{status.textContent='No se pudo guardar la solicitud. Revisa los permisos de almacenamiento de tu navegador.'}});
 function showActions(){let actions=document.getElementById('registration-actions');if(!actions){actions=document.createElement('div');actions.id='registration-actions';actions.style.cssText='display:flex;gap:12px;flex-wrap:wrap;margin-top:12px';register.append(actions)}actions.replaceChildren();
 const restore=document.createElement('button');restore.type='button';restore.className='btn';restore.textContent='Recuperar solicitud DEMO';restore.onclick=()=>{try{const draft=JSON.parse(sessionStorage.getItem('opp_demo_registration'));if(!draft)return;const inputs=register.querySelectorAll('input');inputs[0].value=draft.name;inputs[1].value=draft.email;select.value=draft.profile;status.textContent=draft.id+' · '+draft.state}catch{status.textContent='No se pudo recuperar la solicitud.'}};
 const remove=document.createElement('button');remove.type='button';remove.className='btn';remove.textContent='Eliminar solicitud DEMO';remove.onclick=()=>{try{sessionStorage.removeItem('opp_demo_registration');register.reset();actions.remove();status.textContent='Solicitud DEMO eliminada de esta sesión.'}catch{status.textContent='No se pudo eliminar la solicitud.'}};actions.append(restore,remove)}
 try{if(sessionStorage.getItem('opp_demo_registration'))showActions()}catch{}
}
})();
