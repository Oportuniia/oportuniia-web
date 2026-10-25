// The circular preview and saved square use the same crop coordinates.
export function showPhoto(photo){
  const d=document.createElement('dialog');d.className='photo-modal';
  d.innerHTML='<button class="button" aria-label="Cerrar fotografía">Cerrar</button><h2>Tu fotografía</h2><img class="photo-large" alt="Tu fotografía ampliada">';
  d.querySelector('img').src=photo;d.querySelector('button').onclick=()=>d.close();
  d.addEventListener('close',()=>d.remove(),{once:true});document.body.append(d);d.showModal();
}
export async function editPhoto(source,save){
  const bitmap=await createImageBitmap(source);
  if(bitmap.width*bitmap.height>24000000){bitmap.close();throw Error('La fotografía es demasiado grande. Usa una imagen de hasta 24 megapíxeles.');}
  const d=document.createElement('dialog');d.className='photo-modal';
  d.innerHTML='<h2>Encuadra tu fotografía</h2><p>Así se verá en tu perfil. Ajusta el tamaño y la posición antes de guardar.</p><canvas width="400" height="400" class="photo-circle" aria-label="Vista previa circular"></canvas><label>Acercar<input name="zoom" type="range" min="1" max="4" step="0.01" value="1"></label><label>Posición horizontal<input name="x" type="range" min="0" max="100" value="50"></label><label>Posición vertical<input name="y" type="range" min="0" max="100" value="50"></label><div class="row"><button class="button primary" data-save>Guardar fotografía</button><button class="button" data-cancel>Cancelar</button></div><p role="status"></p>';
  const canvas=d.querySelector('canvas'),ctx=canvas.getContext('2d');
  const draw=()=>{const size=Math.min(bitmap.width,bitmap.height)/Number(d.querySelector('[name=zoom]').value);const x=(bitmap.width-size)*Number(d.querySelector('[name=x]').value)/100,y=(bitmap.height-size)*Number(d.querySelector('[name=y]').value)/100;ctx.fillStyle='#fff';ctx.fillRect(0,0,400,400);ctx.drawImage(bitmap,x,y,size,size,0,0,400,400)};
  d.querySelectorAll('input').forEach(i=>i.oninput=draw);
  let saving=false;
  d.querySelector('[data-cancel]').onclick=()=>d.close();
  d.addEventListener('cancel',e=>{if(saving)e.preventDefault()});
  d.addEventListener('close',()=>{bitmap.close();d.remove()},{once:true});
  d.querySelector('[data-save]').onclick=async()=>{saving=true;d.querySelectorAll('button,input').forEach(b=>b.disabled=true);try{await save(canvas.toDataURL('image/jpeg',.9));d.close()}catch(e){d.querySelector('[role=status]').textContent=e.message}finally{saving=false;d.querySelectorAll('button,input').forEach(b=>b.disabled=false)}};
  document.body.append(d);draw();d.showModal();
}
