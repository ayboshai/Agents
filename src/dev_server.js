#!/usr/bin/env node
'use strict';

const http = require('http');

const HOST = '127.0.0.1';
const PORT = Number(process.env.PORT || 3001);
const PKG = require('../package.json');

const INDEX_HTML = `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>CMAS-OS Template</title>
  </head>
  <body>
    <main>
      <h1>CMAS-OS Template</h1>
      <p>This is a minimal server used to keep the E2E gate operational on a clean repo.</p>
    </main>
  </body>
</html>
`;

function respondText(res, statusCode, body) {
  res.statusCode = statusCode;
  res.setHeader('Content-Type', 'text/plain; charset=utf-8');
  res.end(body);
}

function respondHtml(res, statusCode, body) {
  res.statusCode = statusCode;
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  res.end(body);
}

function respondJson(res, statusCode, value) {
  res.statusCode = statusCode;
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.end(JSON.stringify(value));
}

const server = http.createServer((req, res) => {
  const url = (req.url || '').split('?', 1)[0];

  if (req.method === 'GET' && url === '/health') {
    return respondText(res, 200, 'OK');
  }

  if (req.method === 'GET' && url === '/version') {
    return respondJson(res, 200, { name: PKG.name, version: PKG.version });
  }

  if (req.method === 'GET' && url === '/') {
    return respondHtml(res, 200, INDEX_HTML);
  }

  return respondText(res, 404, 'Not Found');
});

server.listen(PORT, HOST, () => {
  process.stdout.write(`CMAS-OS template server listening on http://${HOST}:${PORT}\n`);
});

function shutdown() {
  server.close(() => process.exit(0));
}

process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
