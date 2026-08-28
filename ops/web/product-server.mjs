import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import productHandler from '../../api/product.mjs';

function sendText(req, res, status, body, extraHeaders = {}) {
  res.statusCode = status;
  res.setHeader('Content-Type', 'text/plain; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  res.setHeader('X-Content-Type-Options', 'nosniff');
  for (const [name, value] of Object.entries(extraHeaders)) res.setHeader(name, value);
  res.end(req.method === 'HEAD' ? '' : body);
}

function parsePort(value) {
  const port = Number(value || 4181);
  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    throw new Error(`Invalid GEARDROP_PRODUCT_PORT: ${value}`);
  }
  return port;
}

export function createProductServer({ handler = productHandler } = {}) {
  const server = http.createServer(async (req, res) => {
    const url = new URL(req.url || '/', 'http://127.0.0.1');

    if (url.pathname === '/healthz') {
      if (!['GET', 'HEAD'].includes(req.method || '')) {
        return sendText(req, res, 405, 'method not allowed\n', { Allow: 'GET, HEAD' });
      }
      return sendText(req, res, 200, 'ok\n');
    }

    if (url.pathname !== '/p') return sendText(req, res, 404, 'not found\n');

    try {
      await handler(req, res);
    } catch (error) {
      console.error('product_handler_failed', error);
      if (!res.headersSent) return sendText(req, res, 503, 'temporarily unavailable\n');
      res.destroy();
    }
  });

  server.requestTimeout = 15_000;
  server.headersTimeout = 10_000;
  server.keepAliveTimeout = 5_000;
  server.on('clientError', (_error, socket) => {
    if (socket.writable) socket.end('HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n');
  });
  return server;
}

export function isMainModule(entryPath = process.argv[1]) {
  if (!entryPath) return false;
  try {
    return fs.realpathSync(path.resolve(entryPath)) === fs.realpathSync(fileURLToPath(import.meta.url));
  } catch (_) {
    return false;
  }
}

if (isMainModule()) {
  const host = process.env.GEARDROP_PRODUCT_HOST || '127.0.0.1';
  const port = parsePort(process.env.GEARDROP_PRODUCT_PORT);
  const server = createProductServer();

  server.listen(port, host, () => {
    console.log(`geardrop_product_server listening=${host}:${port}`);
  });

  const shutdown = (signal) => {
    console.log(`geardrop_product_server shutdown=${signal}`);
    server.close((error) => {
      if (error) {
        console.error('geardrop_product_server close_failed', error);
        process.exitCode = 1;
      }
    });
  };
  process.on('SIGTERM', () => shutdown('SIGTERM'));
  process.on('SIGINT', () => shutdown('SIGINT'));
}
