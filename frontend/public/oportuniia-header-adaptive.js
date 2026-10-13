(function(){
var header=document.querySelector('header');if(!header)return;
var sections=Array.from(document.querySelectorAll('main section, body>section, section, main, footer')).filter(function(el){return el!==header&&el.getBoundingClientRect().height>40});
function rgb(v){var m=String(v||'').match(/rgba?\((\d+)[, ]+(\d+)[, ]+(\d+)(?:[, /]+([\d.]+))?/);return m?[+m[1],+m[2],+m[3],m[4]===undefined?1:+m[4]]:null}
function sample(el){for(var n=el;n&&n!==document.documentElement;n=n.parentElement){var style=getComputedStyle(n),c=rgb(style.backgroundColor);if(c&&c[3]>.7)return c}return [7,22,35,1]}
function tick(){var rect=header.getBoundingClientRect(),y=Math.min(innerHeight-5,Math.max(1,rect.bottom+8)),x=innerWidth/2;var el=document.elementFromPoint(x,y);if(!el)return;var c=sample(el);var brightness=(c[0]*.2126+c[1]*.7152+c[2]*.0722);header.classList.toggle('opp-over-light',brightness>155)}
var pending=false;function schedule(){if(pending)return;pending=true;requestAnimationFrame(function(){pending=false;tick()})}
addEventListener('scroll',schedule,{passive:true});addEventListener('resize',schedule);addEventListener('load',schedule);schedule();
})();