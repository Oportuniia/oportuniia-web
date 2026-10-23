// Render static build: include the local OCR engines before publishing pages.
const fs = require('fs');
const path = require('path');
require('./build-secretary.cjs');
const root = path.resolve(__dirname, '../..');
const source = path.join(root, 'frontend/public');
const destination = path.join(root, 'deploy');
fs.mkdirSync(destination, {recursive: true});
fs.cpSync(source, destination, {recursive: true});
fs.copyFileSync(path.join(source, 'web2.html'), path.join(destination, 'index.html'));
for (const file of ['secretary-engines.js', 'pdf.worker.min.mjs', 'ocr/worker.min.js',
                    'ocr/lang/spa.traineddata.gz', 'ocr/lang/eng.traineddata.gz']) {
  if (!fs.statSync(path.join(destination, 'private/vendor', file)).size) throw Error('Missing OCR artifact: ' + file);
}
console.log('PUBLIC_SITE_AND_LOCAL_OCR_READY');
