// OPORTUNIIA · Fase 2 — enruta las páginas SSR y las APIs al backend FastAPI.
// El resto (assets de /public, hot-reload) lo sigue sirviendo el dev server.
const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function (app) {
  const target = 'http://localhost:8001';

  const shouldProxy = (pathname) => {
    if (pathname === '/') return true;                       // HOME V54 (SSR)
    if (pathname.startsWith('/api')) return true;            // JSON APIs
    if (pathname === '/oportunidades') return true;          // catálogo
    if (pathname.startsWith('/oportunidades/')) return true; // detalle
    return false;
  };

  app.use(
    createProxyMiddleware(shouldProxy, {
      target,
      changeOrigin: false, // conserva el Host público para canonical/OG
      ws: false,
      logLevel: 'warn',
    })
  );
};
