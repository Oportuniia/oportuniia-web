// Render static build: include the local OCR engines before publishing pages.
const fs = require('fs');
const path = require('path');
require('./build-secretary.cjs');
const root = path.resolve(__dirname, '../..');
const source = path.join(root, 'frontend/public');
const destination = path.join(root, 'deploy');
fs.mkdirSync(destination, {recursive: true});
fs.cpSync(source, destination, {recursive: true});
// These small, shared styles are critical to first paint. Inline in their original
// cascade order to avoid three serial network waits on slow mobile connections.
for (const name of ['web2.html', 'oportunidades.html']) {
  const file = path.join(destination, name);
  const html = fs.readFileSync(file, 'utf8').replace(
    /<link rel="stylesheet" href="\/(oportuniia-(?:remix|header-unified|public)\.css)\?[^\"]*">/g,
    (_, css) => `<style data-source="${css}">${fs.readFileSync(path.join(source, css), 'utf8')}</style>`);
  fs.writeFileSync(file, html);
}
fs.copyFileSync(path.join(destination, 'web2.html'), path.join(destination, 'index.html'));
// Only explicitly public pages belong in the search index. Never discover
// URLs by scanning all HTML: that would include account and review screens.
const publicPages = {
  'index.html': '/', 'web2.html': '/',
  'nuestra-filosofia.html': '/nuestra-filosofia',
  'como-funciona.html': '/como-funciona',
  'oportunidades.html': '/oportunidades',
  'grupo-oportuniia.html': '/grupo-oportuniia',
  'tecnologia.html': '/tecnologia', 'contacto.html': '/contacto',
  'servicers.html': '/servicers',
};
const canonicalOrigin = 'https://oportuniia.com';
for (const [name, route] of Object.entries(publicPages)) {
  const file = path.join(destination, name);
  const html = fs.readFileSync(file, 'utf8')
    .replace(/<link\b[^>]*rel=["']canonical["'][^>]*>/gi, '')
    .replace('</head>', `<link rel="canonical" href="${canonicalOrigin}${route}"></head>`);
  fs.writeFileSync(file, html);
}
const publicUrls = [...new Set(Object.values(publicPages))];
fs.writeFileSync(path.join(destination, 'sitemap.xml'),
  '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
  publicUrls.map(route => `  <url><loc>${canonicalOrigin}${route}</loc></url>`).join('\n') + '\n</urlset>\n');
// Private HTML already has noindex. Keep it crawlable so search engines can
// read that directive; access to the underlying data still requires login.
fs.writeFileSync(path.join(destination, 'robots.txt'),
  `User-agent: *\nAllow: /\nDisallow: /api/\n\nSitemap: ${canonicalOrigin}/sitemap.xml\n`);
// Preserve the existing clean admin URL as well as the explicit HTML page.
fs.mkdirSync(path.join(destination, 'gestion-usuarios'), {recursive: true});
fs.copyFileSync(path.join(destination, 'gestion-usuarios.html'), path.join(destination, 'gestion-usuarios/index.html'));
for (const file of ['secretary-engines.js', 'pdf.worker.min.mjs', 'ocr/worker.min.js',
                    'ocr/lang/spa.traineddata.gz', 'ocr/lang/eng.traineddata.gz']) {
  if (!fs.statSync(path.join(destination, 'private/vendor', file)).size) throw Error('Missing OCR artifact: ' + file);
}
console.log('PUBLIC_SITE_AND_LOCAL_OCR_READY');
