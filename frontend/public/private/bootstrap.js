// Explicit DEMO remains isolated. The official path always requires a server session.
if(new URLSearchParams(location.search).get('demo')==='1')await import('./app.js');else await import('./live.js');
