// Keep the approved photographs and framing; request appropriately sized WebP.
const fs = require('fs');
const path = require('path');
for (const name of ['web2.html', 'oportunidades.html']) {
  const file = path.join(__dirname, '../public', name);
  let html = fs.readFileSync(file, 'utf8');
  html = html.replace(/<img src="(https:\/\/images\.unsplash\.com\/[^?]+)\?crop=entropy&cs=srgb&fm=jpg&q=85&w=900"([^>]+)>/g,
    (_, url, attributes) => `<img src="${url}?auto=format&fit=max&q=75&w=640" srcset="${url}?auto=format&fit=max&q=75&w=400 400w, ${url}?auto=format&fit=max&q=75&w=640 640w, ${url}?auto=format&fit=max&q=75&w=900 900w" sizes="(max-width: 650px) 92vw, (max-width: 1050px) 46vw, 400px" decoding="async"${attributes}>`);
  fs.writeFileSync(file, html);
}
