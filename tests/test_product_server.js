import assert from 'node:assert/strict';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

import { createProductServer, isMainModule } from '../ops/web/product-server.mjs';

async function listen(server) {
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  return `http://127.0.0.1:${server.address().port}`;
}

test('direct public server exposes only healthz, /p, and /api/catalog', async (t) => {
  const productRequests = [];
  const catalogRequests = [];
  const server = createProductServer({
    handler: async (req, res) => {
      productRequests.push(req.url);
      res.statusCode = 200;
      res.setHeader('Content-Type', 'text/plain');
      res.end(`handled ${req.url}`);
    },
    catalog: async (req, res) => {
      catalogRequests.push(req.url);
      res.statusCode = 200;
      res.setHeader('Content-Type', 'application/json');
      res.end('{"rows":[]}');
    },
  });
  t.after(() => new Promise((resolve) => server.close(resolve)));
  const base = await listen(server);

  const health = await fetch(`${base}/healthz`);
  assert.equal(health.status, 200);
  assert.equal(await health.text(), 'ok\n');

  const healthHead = await fetch(`${base}/healthz`, { method: 'HEAD' });
  assert.equal(healthHead.status, 200);
  assert.equal(await healthHead.text(), '');

  const missing = await fetch(`${base}/api/product`);
  assert.equal(missing.status, 404);

  const product = await fetch(`${base}/p?sku=evo%3Aexample`);
  assert.equal(product.status, 200);
  assert.equal(await product.text(), 'handled /p?sku=evo%3Aexample');
  const catalog = await fetch(`${base}/api/catalog?region=us`);
  assert.equal(catalog.status, 200);
  assert.deepEqual(await catalog.json(), { rows: [] });
  assert.deepEqual(productRequests, ['/p?sku=evo%3Aexample']);
  assert.deepEqual(catalogRequests, ['/api/catalog?region=us']);
});

test('main-module detection resolves symlinked path components', () => {
  const modulePath = fileURLToPath(new URL('../ops/web/product-server.mjs', import.meta.url));
  assert.equal(isMainModule(modulePath), true);
});
