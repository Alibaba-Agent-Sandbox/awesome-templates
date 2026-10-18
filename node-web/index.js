// Built-in dependency-free HTTP sample; replace with your Express/Fastify app.
const http = require('node:http');
http.createServer((req, res) => {
  res.writeHead(200, {'Content-Type': 'text/plain; charset=utf-8'});
  res.end('node-web ready\n');
}).listen(Number(process.env.PORT || 3000), '0.0.0.0', () => {
  console.log('node-web listening');
});
