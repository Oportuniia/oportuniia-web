import { useMemo, useState } from "react";
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import "@/App.css";

const plans = {
  monthly: { name: "Premium mensual", price: "1.000 €", detail: "+ impuestos / mes", duration: "1 mes", code: "PREMIUM_MONTHLY" },
  annual: { name: "Premium anual", price: "10.000 €", detail: "+ impuestos / 12 meses", duration: "12 meses desde la activación", code: "PREMIUM_ANNUAL" },
};

const BrandHeader = () => <header className="brand-header">
  <a href="/"><img src="/oportuniia-logo.webp?v=20260929-web1" alt="OPORTUNIIA" /></a>
  <nav><a href="/nuestra-filosofia">Nuestra filosofía</a><a href="/como-funciona">Cómo funciona</a><a href="/oportunidades">Oportunidades</a><a href="/tecnologia">Tecnología</a><a href="/grupo-oportuniia">Grupo OPORTUNIIA</a><a href="/contacto">Contacto</a><a href="/servicers">Canal profesional</a></nav>
  <a className="account-link" href="/mi-oportuniia">MI OPORTUNIIA</a>
</header>;

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
  const [plan, setPlan] = useState("annual");
  const [accepted, setAccepted] = useState(false);
  const [early, setEarly] = useState(false);
  const selected = useMemo(() => plans[plan], [plan]);

  const prepare = (event) => {
    event.preventDefault();
    if (!accepted) return;
    window.alert("Checkout preparado en sandbox. No se realizará ningún cargo mientras la pasarela permanezca cerrada.");
  };

  return <><BrandHeader /><main className="shell"><section className="checkout">
    <p className="eyebrow">OPORTUNIIA · PREMIUM</p>
    <h1>Contratar Experiencia Premium</h1>
    <p className="lead">Elige modalidad. El plan anual dura 12 meses completos desde su activación.</p>
    <div className="plans" role="radiogroup" aria-label="Modalidad Premium">
      {Object.entries(plans).map(([key, p]) => <label className={"plan "+(plan===key?"selected":"")} key={key}>
        <input type="radio" name="plan" value={key} checked={plan===key} onChange={() => setPlan(key)} />
        <span><strong>{p.name}</strong><b>{p.price}</b><small>{p.detail}</small><small>{p.duration}</small></span>
      </label>)}
    </div>
    <section className="legal premium-benefits">
      <h2>Ventajas de OPORTUNIIA Premium</h2>
      <ul><li>Universo Acuerdos</li><li>Perímetros personalizados y screening avanzado</li><li>Peticiones a la carta</li><li>Documentación ampliada</li><li>MI OPORTUNIIA</li><li>Secretaría, PBC/Compliance, IA y trazabilidad según perfil y operación</li></ul>
    </section>
    <section className="legal">
      <h2>Antes de contratar</h2>
      <p>Precio seleccionado: <strong>{selected.price} {selected.detail}</strong>.</p>
      <label className="check"><input type="checkbox" checked={early} onChange={e=>setEarly(e.target.checked)} /> Solicito expresamente que el servicio pueda comenzar antes de finalizar el plazo de desistimiento, cuando resulte aplicable.</label>
      <label className="check required"><input type="checkbox" checked={accepted} onChange={e=>setAccepted(e.target.checked)} /> He leído y acepto expresamente las condiciones de Premium y la información precontractual aplicable.</label>
    </section>
    <div className="summary"><div><span>Modalidad</span><strong>{selected.name}</strong></div><div><span>Importe</span><strong>{selected.price} {selected.detail}</strong></div><div><span>Vigencia</span><strong>{selected.duration}</strong></div></div>
    <button className="pay" disabled={!accepted} onClick={prepare}>Contratar Premium y pagar {selected.price} + impuestos</button>
    <p className="closed">PASARELA DE COBRO: CERRADA · SANDBOX · ningún cargo real</p>
  </section></main></>;
}

const privateDeals = [
  {code:"NPL", city:"Madrid", title:"Residencial con garantía hipotecaria", roi:"31,8%", term:"9 meses", status:"Judicial", img:"https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1000&q=80"},
  {code:"CDR", city:"Barcelona", title:"Activo residencial · cesión de remate", roi:"26,4%", term:"6 meses", status:"Cesión", img:"https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?auto=format&fit=crop&w=1000&q=80"},
  {code:"REO", city:"Valencia", title:"Local comercial en zona consolidada", roi:"21,7%", term:"12 meses", status:"Disponible", img:"https://images.unsplash.com/photo-1497366811353-6870744d04b2?auto=format&fit=crop&w=1000&q=80"},
  {code:"NPL", city:"Málaga", title:"Residencial con estrategia de acuerdo", roi:"34,1%", term:"8 meses", status:"Acuerdo", img:"https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1000&q=80"},
];

function DealCard({deal}) {
  return <article className="private-deal">
    <div className="private-deal-media"><img src={deal.img} alt="" /><span className="private-tag">{deal.code}</span><button className="favorite" aria-label="Añadir a favoritos">♡</button></div>
    <div className="private-deal-body"><div className="private-city">{deal.city}</div><h3>{deal.title}</h3>
      <div className="private-kpis"><div><span>ROI</span><b>{deal.roi}</b></div><div><span>Plazo</span><b>{deal.term}</b></div><div><span>Estado</span><b>{deal.status}</b></div></div>
      <div className="private-actions"><button>Añadir a Mis operaciones</button><a href="/oportunidades">Ver operación →</a></div>
    </div>
  </article>
}

function MiOportuniia() {
  const [section,setSection] = useState("Oportunidades");
  const sections=["Oportunidades","Mis operaciones","Favoritos y búsquedas","Documentación","Secretaría","PBC / Compliance","Comunicaciones","IA","LEGAL","Ofertas / reservas","Visitas","Premium"];
  return <div className="private-app">
    <header className="private-topbar"><a href="/"><img src="/oportuniia-logo.webp?v=20260929-web1" alt="OPORTUNIIA"/></a><div className="private-user"><span>MI OPORTUNIIA</span><button>RAFAEL QUEROL ▾</button></div></header>
    <div className="private-shell">
      <aside className="private-sidebar">
        <div className="private-side-k">ÁREA PRIVADA</div>
        {sections.map(x=><button key={x} className={section===x?"active":""} onClick={()=>setSection(x)}>{x}</button>)}
        <a href="/" className="private-back">← Volver a la web</a>
      </aside>
      <main className="private-main">
        {section==="Oportunidades" ? <>
          <div className="private-head"><div><span className="private-eyebrow">OPORTUNIDADES</span><h1>El mismo catálogo.<br/><em>Más capacidad.</em></h1><p>Busca, filtra, guarda y sigue oportunidades sin perder la experiencia visual de OPORTUNIIA.</p></div>
          <div className="private-head-actions"><button>Guardar búsqueda</button><button className="primary-private">Crear perímetro</button></div></div>
          <div className="private-catalog">
            <aside className="private-filters">
              <input placeholder="Buscar por ubicación, operación..." />
              <label>Producto<select><option>Todos</option><option>NPL</option><option>CDR</option><option>REO</option></select></label>
              <label>Situación<select><option>Todas</option><option>Judicial</option><option>Acuerdo</option><option>Cesión</option></select></label>
              <label>Ubicación<select><option>España</option><option>Madrid</option><option>Barcelona</option><option>Valencia</option></select></label>
              <label>ROI mínimo<input type="range" min="0" max="40" defaultValue="15"/></label>
              <label>Precio / inversión<select><option>Cualquier rango</option><option>Hasta 100.000 €</option><option>100.000–250.000 €</option><option>+250.000 €</option></select></label>
              <button className="filter-save">Guardar filtros</button>
            </aside>
            <section className="private-results"><div className="private-results-head"><span>24 oportunidades · acceso profesional</span><div><button className="universe active">Ejecuciones Judiciales</button><button className="universe">Universo Acuerdos</button></div></div>
              <div className="private-grid">{privateDeals.map((d,i)=><DealCard deal={d} key={i}/>)}</div>
            </section>
          </div>
        </> : <PrivateSection title={section}/>}
      </main>
    </div>
  </div>
}

function PrivateSection({title}) {
  const copy={
    "Mis operaciones":"Seguimiento privado de las operaciones que has incorporado a tu perímetro.",
    "Favoritos y búsquedas":"Tus favoritos, búsquedas guardadas y perímetros personalizados en un solo lugar.",
    "Documentación":"Documentación ampliada organizada por usuario y por operación.",
    "Secretaría":"Preparación, actualización y subsanación documental desde Secretaría MI OPORTUNIIA.",
    "PBC / Compliance":"Estado documental y de cumplimiento asociado a tu perfil y a cada operación.",
    "Comunicaciones":"Historial de comunicaciones y trazabilidad operativa.",
    "IA":"Asistencia de IA OPORTUNIIA aplicada a análisis, organización y apoyo operativo.",
    "LEGAL":"Acceso al circuito legal cuando proceda para la operación.",
    "Ofertas / reservas":"Preparación y seguimiento de ofertas y reservas dentro de los circuitos habilitados.",
    "Visitas":"Solicitudes de visitas y comprobaciones de campo cuando estén disponibles.",
    "Premium":"Servicios Premium disponibles para ampliar el acceso y la profundidad de trabajo."
  };
  return <section className="private-section"><span className="private-eyebrow">MI OPORTUNIIA</span><h1>{title}</h1><p>{copy[title]}</p>
    <div className="private-placeholder-grid"><div><b>Estado</b><span>Preparado para integración con datos reales.</span></div><div><b>Trazabilidad</b><span>La capa visual queda separada de la autoridad backend existente.</span></div><div><b>M2M</b><span>Sin tráfico real abierto. Válvulas permanecen cerradas.</span></div></div>
  </section>
}

export default function App() {
  return <div className="App"><BrowserRouter><Routes>
    <Route path="/" element={<Home />} />
    <Route path="/inversor" element={<Investor />} />
    <Route path="/premium" element={<PremiumCheckout />} />
    <Route path="/mi-oportuniia" element={<MiOportuniia />} />
  </Routes></BrowserRouter></div>;
}
