import "@/App.css";

export default function App() {
  return (
    <main className="brand-home">
      <div className="brand-glow" aria-hidden="true" />
      <section className="brand-card">
        <img
          src="/brand/official-full.svg"
          alt="OPORTUNIIA"
          className="brand-logo"
          data-testid="official-brand-logo"
        />
        <p className="brand-kicker">Ideas · Herramientas · Oportunidades</p>
        <p className="brand-copy">Ecosistema OPORTUNIIA.</p>
      </section>
    </main>
  );
}
