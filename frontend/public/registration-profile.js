import {mountOnboarding} from './private/onboarding.js';
const host=document.createElement('div');host.style.cssText='max-width:1000px;margin:0 auto;padding:0 24px 50px';const registration=document.getElementById('registro');
if(registration){registration.append(host);let draft={};try{draft=JSON.parse(sessionStorage.getItem('opp_demo_identity_draft')||'{}')}catch{}
 const requested=new URLSearchParams(location.search).get('perfil');if(requested==='Colaborador')draft.account_kind='colaborador';
 mountOnboarding(host,{onboarding:draft},values=>{try{sessionStorage.setItem('opp_demo_identity_draft',JSON.stringify(values));return true}catch{return false}});
}
