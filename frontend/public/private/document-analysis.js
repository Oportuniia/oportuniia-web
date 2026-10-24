const norm=s=>String(s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/\s+/g,' ').trim();
export const labels={identity:'DNI',representative_identity:'DNI DEL ADMINISTRADOR O SOCIO',company_tax_document:'CIF / NIF DE EMPRESA',constitution:'ESCRITURA DE CONSTITUCIÓN',beneficial_ownership:'ACTA DE TITULARIDAD REAL',representation:'PODER DE REPRESENTACIÓN',other:'Otro documento'};
export function classify(records){
 const text=records.map(r=>r.text).join('\n'),s=norm(text),kinds=[];
 for(const [key,rx] of Object.entries({identity:/documento nacional de identidad|identity card|\bdni\b|id.?esp/,constitution:/escritura de constitucion|constitucion de (?:la )?sociedad|estatutos sociales/,beneficial_ownership:/titularidad real|titular real|beneficiario efectivo/,company_tax_document:/tarjeta de identificacion fiscal|codigo de identificacion fiscal|nif definitivo|nif provisional/,representation:/poder notarial|apoderamiento|poder de representacion/}))if(rx.test(s))kinds.push(key);
 const upper=text.toUpperCase();
 const mrz=upper.match(/(?:^|\n)\s*([A-ZÁÉÍÓÚÑ]{2,}(?:<[A-ZÁÉÍÓÚÑ]+)*)<<([A-ZÁÉÍÓÚÑ]+(?:<[A-ZÁÉÍÓÚÑ]+)*)/);
 function labelled(label){const rx=new RegExp('(?:^|\\n)\\s*'+label+'(?:\\s*[/|]\\s*[A-Z ]{2,20})?\\s*[:.]?\\s*\\n?\\s*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ ]{1,80})(?=\\n|$)','m');const m=upper.match(rx);return m?m[1].trim():''}
 const name=labelled('NOMBRE'),surname=labelled('APELLIDOS');
 const detected=mrz?`${mrz[2]} ${mrz[1]}`.replace(/</g,' ').trim():name&&surname?`${name} ${surname}`:'';
 const meaningful=text.replace(/[^\p{L}\p{N}]/gu,'').length;
 const scores=records.filter(r=>r.method==='OCR local').map(r=>Number(r.confidence)||0);
 const quality=meaningful<20||(scores.length===records.length&&scores.length>0&&scores.every(n=>n<35))?'UNREADABLE':'READABLE';
 return {kinds:kinds.length?kinds:['other'],name:detected,quality};
}
export function mismatch(a,b){return !!(a&&b&&norm(a).split(' ').sort().join(' ')!==norm(b).split(' ').sort().join(' '));}
export function uniqueDocuments(docs){const seen=new Set();return docs.filter(d=>{const key=d.sha256||d.document_id;if(seen.has(key))return false;seen.add(key);return true})}
