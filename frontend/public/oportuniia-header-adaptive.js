(function(){
'use strict';
var header=document.querySelector('header');if(!header)return;
var path=location.pathname.replace(/\/$/,'')||'/';
document.querySelectorAll('header nav.menu a').forEach(function(a){
 var dest=new URL(a.href,location.href).pathname.replace(/\/$/,'')||'/';
 var current=dest===path||(path==='/oportunidades'&&dest==='/oportunidades');
 a.classList.remove('active','opp-current');a.removeAttribute('aria-current');
 if(current){a.classList.add('opp-current');a.setAttribute('aria-current','page')}
});
function parse(str){var m=String(str).match(/rgba?\(\s*(\d+)[, ]+\s*(\d+)[, ]+\s*(\d+)(?:[, /]+([\d.]+))?/);return m?[+m[1],+m[2],+m[3],m[4]===undefined?1:+m[4]]:null}
function background(el){
 var fallback=null;
 for(var n=el;n;n=n.parentElement){
  if(n===header||header.contains(n))continue;
  var st=getComputedStyle(n),c=parse(st.backgroundColor);
  if(c&&c[3]>.85)return c;
  if(st.backgroundImage&&st.backgroundImage!=='none'&&/gradient/.test(st.backgroundImage)){var colors=st.backgroundImage.match(/#[0-9a-fA-F]{6}/g);if(colors&&colors.length){var h=colors[0];return [parseInt(h.slice(1,3),16),parseInt(h.slice(3,5),16),parseInt(h.slice(5,7),16),1]}}
  if(c&&c[3]>.25&&!fallback)fallback=c;
 }
 return fallback||[7,22,35,1]
}
function update(){
 var rect=header.getBoundingClientRect(),y=Math.min(innerHeight-4,Math.max(rect.bottom+70,innerHeight*.15));
 var xs=[.25,.5,.75],lights=0;
 xs.forEach(function(f){var el=document.elementFromPoint(Math.round(innerWidth*f),Math.round(y));if(!el)return;var c=background(el);if(c[0]*.2126+c[1]*.7152+c[2]*.0722>155)lights++});
 header.classList.toggle('opp-over-light',lights>=2);
}
var busy=false;function request(){if(busy)return;busy=true;requestAnimationFrame(function(){busy=false;update()})}
addEventListener('scroll',request,{passive:true});addEventListener('resize',request);addEventListener('load',request);request();
})();