(function(){
var header=document.querySelector('header');if(!header)return;
var path=location.pathname.replace(/\/$/,'')||'/';
document.querySelectorAll('header nav.menu a').forEach(function(a){
 var href=new URL(a.href,location.href),dest=href.pathname.replace(/\/$/,'')||'/';
 var current=dest===path||(path==='/oportunidades'&&dest==='/oportunidades')||(path==='/'&&dest==='/');
 a.classList.toggle('opp-current',current);
 if(current)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');
});
function colorOf(el){for(var n=el;n&&n!==document.documentElement;n=n.parentElement){
 var cs=getComputedStyle(n),c=cs.backgroundColor.match(/rgba?\(\s*(\d+)[, ]+\s*(\d+)[, ]+\s*(\d+)(?:[, /]+([\d.]+))?/);
 if(c&&(+c[4]||1)>.75)return [+c[1],+c[2],+c[3]];
}return [7,22,35]}
function update(){
 var rect=header.getBoundingClientRect();
 var x=Math.round(innerWidth*.5),y=Math.min(innerHeight-2,Math.max(2,Math.round(rect.bottom+18)));
 var target=document.elementFromPoint(x,y);if(!target)return;
 var c=colorOf(target),lum=.2126*c[0]+.7152*c[1]+.0722*c[2];
 header.classList.toggle('opp-over-light',lum>160);
}
var pending=false;function schedule(){if(pending)return;pending=true;requestAnimationFrame(function(){pending=false;update()})}
addEventListener('scroll',schedule,{passive:true});addEventListener('resize',schedule);addEventListener('load',schedule);schedule();
})();