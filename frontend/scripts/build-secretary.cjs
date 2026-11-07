// Build-time only. All runtime PDF/OCR code and language data are served same-origin.
const fs=require('fs'),path=require('path'),{execFileSync}=require('child_process');
const cache=process.env.OPP_SECRETARY_BUILD_CACHE||'/tmp/oportuniia-secretary-runtime';
const specs=['esbuild@0.25.12','pdfjs-dist@4.10.38','pdf-lib@1.17.1','tesseract.js@6.0.1','@tesseract.js-data/spa@1.0.0','@tesseract.js-data/eng@1.0.0','fflate@0.8.2'];
fs.mkdirSync(cache,{recursive:true});
if(!fs.existsSync(path.join(cache,'node_modules','esbuild')))execFileSync('npm',['install','--prefix',cache,'--ignore-scripts','--no-audit','--no-fund',...specs],{stdio:'inherit'});
const vendor=path.resolve(__dirname,'../public/private/vendor');fs.mkdirSync(vendor,{recursive:true});const nm=path.join(cache,'node_modules');
const copy=(source,target)=>{fs.mkdirSync(path.dirname(target),{recursive:true});fs.copyFileSync(source,target)};
copy(path.join(nm,'pdfjs-dist/build/pdf.worker.min.mjs'),path.join(vendor,'pdf.worker.min.mjs'));
copy(path.join(nm,'tesseract.js/dist/worker.min.js'),path.join(vendor,'ocr/worker.min.js'));
for(const f of ['tesseract-core-lstm.wasm.js','tesseract-core-simd-lstm.wasm.js'])copy(path.join(nm,'tesseract.js-core',f),path.join(vendor,'ocr',f));
for(const lang of ['spa','eng'])copy(path.join(nm,`@tesseract.js-data/${lang}/4.0.0_best_int/${lang}.traineddata.gz`),path.join(vendor,'ocr/lang',`${lang}.traineddata.gz`));
for(const pkg of ['pdfjs-dist','pdf-lib','tesseract.js','tesseract.js-core','fflate']){for(const name of ['LICENSE','LICENSE.txt','LICENSE.md']){const src=path.join(nm,pkg,name);if(fs.existsSync(src)){copy(src,path.join(vendor,'licenses',pkg.replace('/','-')+'.txt'));break}}}
require(path.join(nm,'esbuild')).buildSync({stdin:{contents:"export {PDFDocument} from 'pdf-lib';export {getDocument,GlobalWorkerOptions} from 'pdfjs-dist/build/pdf.mjs';export {createWorker} from 'tesseract.js';export {zipSync,strToU8} from 'fflate';",resolveDir:cache},bundle:true,format:'esm',platform:'browser',target:'es2022',minify:true,outfile:path.join(vendor,'secretary-engines.js'),legalComments:'linked'});
fs.writeFileSync(path.join(vendor,'manifest.json'),JSON.stringify({dependencies:specs,processing:'LOCAL_BROWSER_ONLY',file_upload:false},null,2));
console.log('SECRETARY_RUNTIME_READY: same-origin PDF, OCR, split and ZIP');
