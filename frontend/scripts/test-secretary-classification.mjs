import {suggestCategory} from '../public/private/secretary.js';
import assert from 'node:assert/strict';
const cases=[['DOCUMENTO NACIONAL DE IDENTIDAD','identidad'],['ESCRITURA DE CONSTITUCION '+ 'texto '.repeat(60)+'registro mercantil y poder notarial','societaria'],['ACTA DE TITULARIDAD REAL '+ 'texto '.repeat(60)+'documento nacional de identidad','titularidad'],['ESCRITURA DE PODER GENERAL','representacion'],['CERTIFICADO DE TITULARIDAD BANCARIA','fondos'],['JUZGADO DE PRIMERA INSTANCIA SENTENCIA','judicial'],['no hay informacion reconocible','pendiente'],['DOCUMENTO NACIONAL DE IDENTIDAD PASAPORTE ACTA DE TITULARIDAD REAL BENEFICIARIO EFECTIVO','pendiente']];
for(const [text,want] of cases)assert.equal(suggestCategory(text),want,text);
console.log(cases.length+' classification cases passed');

import {classifyPage} from '../public/private/secretary.js';
const previous={source:0,sourcePage:0,category:'societaria'};
assert.deepEqual(classifyPage('Página 2 de 3. '+ 'Contenido de la sociedad y sus participaciones. '.repeat(3),previous,{source:0,sourcePage:1}),{category:'societaria',start:false});
assert.equal(classifyPage('Página 2 de 3. '+ 'Contenido de la sociedad. '.repeat(4),previous,{source:1,sourcePage:1}).category,'pendiente');
assert.equal(classifyPage('DOCUMENTO NACIONAL DE IDENTIDAD '+ 'contenido '.repeat(8),previous,{source:0,sourcePage:1,confidence:20}).category,'pendiente');
assert.equal(classifyPage('SENTENCIA JUZGADO '+ 'contenido '.repeat(8),previous,{source:0,sourcePage:1}).start,true);
console.log('4 mixed-page and poor-reading cases passed');
assert.equal(suggestCategory('Se hace constar en la escritura de constitución de la hipoteca y en la resolución. Administración de Justicia'),'judicial');
assert.equal(suggestCategory('DECRETO. Antecedentes de hecho. Administración de Justicia'),'judicial');
assert.equal(suggestCategory('ESCRITURA DE CONSTITUCION DE SOCIEDAD LIMITADA. Estatutos sociales'),'societaria');
assert.equal(classifyPage('Servicio Común de Ejecución. Tribunal de Instancia. Resolución judicial.',{source:0,sourcePage:6,category:'judicial'},{source:0,sourcePage:7}).start,true);
console.log('4 judicial separation regressions passed');
