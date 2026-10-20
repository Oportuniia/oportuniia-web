import { useEffect, useState } from "react";
export default function PublicFooter(){
  const [html,setHtml]=useState("");
  useEffect(()=>{
    const controller=new AbortController();
    fetch('/public-chrome.json',{signal:controller.signal})
      .then(r=>{if(!r.ok)throw new Error('footer');return r.json()})
      .then(config=>setHtml(config.footerHtml))
      .catch(()=>{});
    return ()=>controller.abort();
  },[]);
  // This HTML is our versioned, same-origin static resource; it contains no user input.
  return html ? <footer className="opp-public-footer" dangerouslySetInnerHTML={{__html:html}}/> :
    <footer className="opp-public-footer"><a href="/contacto">Contactar con OPORTUNIIA</a></footer>;
}
