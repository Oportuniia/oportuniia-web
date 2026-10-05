import { useMemo, useState } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";

const plans = {
  monthly: { name: "Premium mensual", price: "1.000 €", detail: "+ impuestos / mes", duration: "1 mes", code: "PREMIUM_MONTHLY" },
  annual: { name: "Premium anual", price: "10.000 €", detail: "+ impuestos / 12 meses", duration: "12 meses desde la activación", code: "PREMIUM_ANNUAL" },
};

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
  return <main className="shell"><section className="checkout">
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
      <p><strong>Modalidad D:</strong> se añaden ambos anexos: Servicio Jurídico B/D y Comercialización Posterior C/D.</p>
      <p>La documentación PBC, privacidad y retención se incorpora cuando corresponda al expediente. Cada aceptación queda vinculada a su versión y evidencia electrónica.</p>
    </section>
    <div className="summary"><div><span>Modalidad elegida</span><strong>{investorModes[mode].title}</strong></div></div>
  </section></main>;
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

  return <main className="shell">
    <section className="checkout">
      <p className="eyebrow">OPORTUNIIA · PREMIUM</p>
      <h1>Contratar Experiencia Premium</h1>
      <p className="lead">Elige modalidad. El plan anual dura 12 meses completos desde su activación; el 31 de diciembre no altera su vigencia.</p>
      <div className="plans" role="radiogroup" aria-label="Modalidad Premium">
        {Object.entries(plans).map(([key, p]) => <label className={"plan "+(plan===key?"selected":"")} key={key}>
          <input type="radio" name="plan" value={key} checked={plan===key} onChange={() => setPlan(key)} />
          <span><strong>{p.name}</strong><b>{p.price}</b><small>{p.detail}</small><small>{p.duration}</small></span>
        </label>)}
      </div>
      <section className="legal premium-benefits">
        <h2>Ventajas de OPORTUNIIA Premium</h2>
        <p>Premium amplía el acceso a herramientas, información y coordinación operativa de OPORTUNIIA. Las prestaciones se aplican según el perfil, la operación y las condiciones particulares.</p>
        <ul>
          <li><strong>Universo Acuerdos:</strong> acceso para perfiles autorizados a oportunidades y acuerdos disponibles en este entorno.</li>
          <li><strong>Perímetros personalizados y actualizados:</strong> preparación y seguimiento de perímetros adaptados a los criterios del cliente.</li>
          <li><strong>Análisis avanzado:</strong> herramientas de filtrado, análisis y apoyo a la evaluación de oportunidades, sin garantía de resultado o rentabilidad.</li>
          <li><strong>Peticiones a la carta:</strong> posibilidad de solicitar búsquedas, documentación o actuaciones específicas dentro del alcance disponible.</li>
          <li><strong>Documentación y reportajes ampliados:</strong> acceso a información, evidencias y materiales adicionales cuando existan y puedan facilitarse.</li>
          <li><strong>MI OPORTUNIIA:</strong> espacio privado para organizar documentación, operaciones, comunicaciones y seguimiento.</li>
          <li><strong>Recordatorios y seguimiento:</strong> apoyo para mantener al día hitos, documentación y actuaciones vinculadas a las operaciones.</li>
          <li><strong>Motor de IA OPORTUNIIA:</strong> asistencia tecnológica para análisis, organización y apoyo operativo; sus resultados no sustituyen validaciones profesionales exigibles.</li>
          <li><strong>Apoyo jurídico cuando proceda:</strong> acceso y coordinación con profesionales o despachos externos e independientes, sujeto a modalidad, encargo, disponibilidad y condiciones aplicables.</li>
          <li><strong>Secretaría MI OPORTUNIIA:</strong> apoyo en preparación, actualización, organización y subsanación documental, sin sustituir Compliance ni conceder validaciones.</li>
          <li><strong>Ofertas y reservas:</strong> preparación y coordinación ágil de ofertas y reservas dentro de los circuitos habilitados.</li>
          <li><strong>Visitas y comprobaciones de campo:</strong> posibilidad de solicitar actuaciones presenciales cuando estén disponibles, autorizadas y sean viables.</li>
        </ul>
        <p><strong>Alcance:</strong> determinadas prestaciones son bajo petición o están sujetas a disponibilidad, autorización, viabilidad, territorio, modalidad de operación y cumplimiento normativo. Premium no garantiza adjudicación, rentabilidad, financiación, aceptación de ofertas ni resultado jurídico o comercial.</p>
      </section>
      <section className="legal">
        <h2>Antes de contratar</h2>
        <p>Precio seleccionado: <strong>{selected.price} {selected.detail}</strong>. No existe permanencia adicional ni renovación obligatoria. Una nueva contratación al finalizar requiere una nueva decisión del cliente.</p>
        <p>Antes del pago deben ponerse a disposición del cliente la información precontractual y una copia descargable de las condiciones aplicables, identificadas por versión y huella documental.</p>
        <p>Si actúas como consumidor, se aplicarán los derechos imperativos que correspondan, incluido el desistimiento cuando sea aplicable. Si solicitas que el servicio comience durante ese plazo, esa petición debe quedar registrada expresamente y se aplicará, cuando corresponda, el régimen legal de ejecución anticipada y pago proporcional.</p>
        <label className="check"><input type="checkbox" checked={early} onChange={e=>setEarly(e.target.checked)} /> Solicito expresamente que, una vez confirmado el pago, el servicio pueda comenzar antes de finalizar el plazo de desistimiento, cuando éste resulte aplicable.</label>
        <label className="check required"><input type="checkbox" checked={accepted} onChange={e=>setAccepted(e.target.checked)} /> He leído y acepto expresamente las condiciones de Premium y la información precontractual aplicable. Entiendo que el siguiente paso implica una obligación de pago.</label>
      </section>
      <div className="summary"><div><span>Modalidad</span><strong>{selected.name}</strong></div><div><span>Importe</span><strong>{selected.price} {selected.detail}</strong></div><div><span>Vigencia</span><strong>{selected.duration}</strong></div></div>
      <button className="pay" disabled={!accepted} onClick={prepare}>Contratar Premium y pagar {selected.price} + impuestos</button>
      <p className="closed">PASARELA DE COBRO: CERRADA · SANDBOX · ningún cargo real</p>
    </section>
  </main>;
}

export default function App() {
  return <div className="App"><BrowserRouter><Routes><Route path="/" element={<Home />} /><Route path="/inversor" element={<Investor />} /><Route path="/premium" element={<PremiumCheckout />} /></Routes></BrowserRouter></div>;
}
