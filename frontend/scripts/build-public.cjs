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
// Preserve the existing clean admin URL as well as the explicit HTML page.
fs.mkdirSync(path.join(destination, 'gestion-usuarios'), {recursive: true});
fs.copyFileSync(path.join(destination, 'gestion-usuarios.html'), path.join(destination, 'gestion-usuarios/index.html'));
for (const file of ['secretary-engines.js', 'pdf.worker.min.mjs', 'ocr/worker.min.js',
                    'ocr/lang/spa.traineddata.gz', 'ocr/lang/eng.traineddata.gz']) {
  if (!fs.statSync(path.join(destination, 'private/vendor', file)).size) throw Error('Missing OCR artifact: ' + file);
}
console.log('PUBLIC_SITE_AND_LOCAL_OCR_READY');
