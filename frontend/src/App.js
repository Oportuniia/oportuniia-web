import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import "@/App.css";
import PublicFooter from "@/components/PublicFooter";

const publicLinks = [["/nuestra-filosofia","Nuestra filosofía"],["/como-funciona","Cómo funciona"],["/oportunidades#producto","Oportunidades"],["/grupo-oportuniia","Grupo OPORTUNIIA"],["/tecnologia","Tecnología"],["/contacto","Contacto"],["/servicers","Canal profesional"]];
function BrandHeader() {
  const [open,setOpen] = useState(false);
  return <header className="brand-header">
    <a href="/"><img src="/oportuniia-logo.webp?v=20260929-web1" alt="OPORTUNIIA" /></a>
    <nav aria-label="Navegación principal">{publicLinks.map(([href,label])=><a key={href} href={href} aria-current={window.location.pathname===href?"page":undefined}>{label}</a>)}</nav>
    <a className="account-link" href="/acceso">Login / Registro</a>
    <button className="public-mobile-toggle" type="button" aria-label={open?"Cerrar menú":"Abrir menú"} aria-expanded={open} aria-controls="react-mobile-menu" onClick={()=>setOpen(!open)}>☰</button>
    {open && <nav id="react-mobile-menu" aria-label="Navegación móvil" onKeyDown={e=>{if(e.key==="Escape")setOpen(false)}}>{publicLinks.map(([href,label])=><a key={href} href={href}>{label}</a>)}<a href="/premium">Premium</a></nav>}
  </header>;
}

function Home() {
  window.location.replace("/web2.html");
  return null;
}

const investorModes = {
  A: { title: "A · Compra", text: "Compra de la oportunidad con el circuito operativo y documental aplicable." },
  B: { title: "B · Compra + servicio jurídico", text: "Compra con activación del servicio jurídico externo e independiente para la operación." },
  C: { title: "C · Compra + comercialización", text: "Compra con encargo posterior de comercialización a OPORTUNIIA." },
  D: { title: "D · Integral", text: "Compra con servicio jurídico y comercialización posterior, sujetos a sus condiciones específicas." },
};

function Investor() {
  const [mode, setMode] = useState("A");
  return <><BrandHeader /><main className="shell"><section className="checkout">
    <p className="eyebrow">OPORTUNIIA · INVERSOR</p><h1>Elige cómo quieres operar</h1>
    <p className="lead">La modalidad se elige para cada operación. Tu perfil de inversor no queda fijado para siempre en una modalidad.</p>
    <div className="plans" role="radiogroup" aria-label="Modalidad de operación del inversor">
      {Object.entries(investorModes).map(([key,m]) => <label className={"plan "+(mode===key?"selected":"")} key={key}>
        <input type="radio" name="investor-mode" value={key} checked={mode===key} onChange={()=>setMode(key)} />
        <span><strong>{m.title}</strong><small>{m.text}</small></span>
      </label>)}
    </div>
    <section className="legal">
      <h2>Documentación contractual</h2>
      <p><strong>Siempre:</strong> Condiciones Marco del Inversor + Condiciones Particulares de la operación A/B/C/D.</p>
      <p><strong>Modalidad B:</strong> se añade el Anexo de Servicio Jurídico B/D.</p>
      <p><strong>Modalidad C:</strong> se añade el Anexo de Comercialización Posterior C/D.</p>
      <p><strong>Modalidad D:</strong> se añaden ambos anexos.</p>
      <p>La documentación PBC, privacidad y retención se incorpora cuando corresponda al expediente.</p>
    </section>
    <div className="summary"><div><span>Modalidad elegida</span><strong>{investorModes[mode].title}</strong></div></div>
  </section></main></>;
}

function PremiumCheckout() {
  const [interest,setInterest] = useState("inversor");
  return <div className="premium-experience"><BrandHeader />
    <main className="premium-main">
      <div className="premium-ambient" aria-hidden="true" />
      <div className="premium-wrap">
        <div className="premium-intro">
          <span className="premium-kicker">OPORTUNIIA <span>·</span> EXPERIENCIA PREMIUM</span>
          <h1>Una perspectiva<br/><em>más profunda.</em></h1>
          <p>Accede a una experiencia de inversión diseñada para quienes necesitan más información, mayor control y una visión completa de cada oportunidad.</p>
          <div className="premium-highlights"><span>Universo Acuerdos</span><span>Información ampliada</span><span>Atención profesional</span></div>
        </div>
        <section className="premium-feature" aria-label="Ventajas Premium">
          <div className="premium-feature-top"><span>01 / ACCESO DIFERENCIAL</span><span>UNIVERSO ACUERDOS</span></div>
          <h2>Más control.<br/>Menos incertidumbre.</h2>
          <p>Operaciones estructuradas con visibilidad sobre capital, horizonte temporal y resultado económico previsto, sujetas al análisis y documentación de cada operación.</p>
          <div className="premium-benefit-grid">
            <div><b>01</b><strong>Oportunidades</strong><span>Exploración de NPL, CDR, REO y Universo Acuerdos.</span></div>
            <div><b>02</b><strong>Perímetros a medida</strong><span>Filtros, seguimiento y selección de activos.</span></div>
            <div><b>03</b><strong>Documentación</strong><span>Mayor profundidad documental según perfil y operación.</span></div>
            <div><b>04</b><strong>MI OPORTUNIIA</strong><span>Un entorno de trabajo conectado a tu actividad.</span></div>
          </div>
        </section>
        <section className="premium-interest">
          <div><span className="premium-kicker">ACCESO PROFESIONAL</span><h2>El siguiente paso empieza aquí.</h2><p>El acceso Premium está sujeto a validación. En esta versión de pruebas no se realizan pagos ni se recogen solicitudes.</p></div>
          <div className="premium-interest-actions">
            <label htmlFor="premium-profile">Perfil profesional</label>
            <select id="premium-profile" value={interest} onChange={e=>setInterest(e.target.value)}><option value="inversor">Inversor</option><option value="colaborador">Colaborador</option></select>
            <a className="premium-action" href={interest==="inversor"?"/registro?rol=inversor":"/solicitar-colaboracion"}>Solicitar acceso <span aria-hidden="true">↗</span></a>
            <small>Sin contratación ni cargos en esta fase.</small>
          </div>
        </section>
      </div>
    </main>
  </div>;
}

function MiOportuniia() {
  window.location.replace("/mi-oportuniia.html?demo=1");
  return null;
}

function AccessForm({kind}) {
  useEffect(()=>{
    const profile=kind==="colaborador"?"Colaborador":"Inversor";
    window.location.replace(kind==="login"?"/acceso":"/acceso?perfil="+encodeURIComponent(profile)+"#registro");
  },[kind]);
  return <p role="status">Abriendo las opciones de acceso…</p>;
}

export default function App() {
  return <div className="App"><BrowserRouter><Routes>
    <Route path="/" element={<Home />} />
    <Route path="/inversor" element={<Investor />} />
    <Route path="/premium" element={<PremiumCheckout />} />
    <Route path="/mi-oportuniia" element={<MiOportuniia />} />
    <Route path="/login" element={<AccessForm kind="login" />} />
    <Route path="/registro" element={<AccessForm kind="inversor" />} />
    <Route path="/solicitar-colaboracion" element={<AccessForm kind="colaborador" />} />
    <Route path="*" element={<><BrandHeader/><main className="shell"><h1>Página no encontrada</h1><p><a href="/">Volver a OPORTUNIIA</a></p></main></>} />
  </Routes><PublicFooter/></BrowserRouter></div>;
}

