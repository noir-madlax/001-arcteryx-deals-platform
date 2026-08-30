# Direct server deployment

The production web surface can run without Vercel hosting. Nginx serves an
allowlisted static release, while a loopback-only Node service preserves the
canonical `/p?sku=...` product pages previously supplied by the Vercel
function.

## Layout

- `/srv/geardrop/source`: deployment-only clone; never shared with crawlers.
- `/srv/geardrop/releases/<commit>`: immutable, allowlisted releases.
- `/srv/geardrop/current`: atomic symlink to the active release.
- `/srv/geardrop/acme`: HTTP-01 challenge webroot.
- `geardrop-product.service`: loopback product-page service on port 4181.
- `geardrop-deploy.timer`: checks `main` every five minutes and switches only
  after candidate and live product smokes pass.

The public root is built from `ops/web/public-files.txt`. Repository source,
SQL, tests, task notes, mobile code, Git metadata, and credentials are not
copied into it. The release builder also creates deterministic gzip sidecars
for public text files of at least 1 KiB. The shared Nginx snippet serves those
sidecars only when the client advertises gzip support and adds
`Vary: Accept-Encoding`; unencoded responses remain available.

## Primary and legacy domains

`geardrop.100app.dev` is the only canonical public host. It serves the shared
static release and loopback product service through its own Nginx virtual host
and TLS certificate. `001.100app.dev` remains resolvable with its own
certificate, but permanently redirects every non-ACME request to
`https://geardrop.100app.dev$request_uri`, preserving paths and queries for old
links and released App versions.

Install `ops/web/nginx/geardrop.100app.dev-tls.conf` only after its independent
certificate exists. Validate it with `nginx -t` and `curl --resolve` before
adding the exact `geardrop` DNS record. Configure that certificate to renew
through the shared `/srv/geardrop/acme` webroot after DNS points to the server.
Only install the 001 redirect template after the new host is publicly healthy
and the canonical release is active.

## Initial installation outline

1. Create `/srv/geardrop/{releases,acme}` and a dedicated source clone owned by
   the deployment user. Configure that clone to use the server deploy key and
   `git@github.com:wantai-dev/001-arcteryx-deals-platform.git`.
2. Build the exact approved commit with
   `ops/web/build-release.sh /srv/geardrop/releases/<commit> <commit>`, then
   point `/srv/geardrop/current` to it.
3. Install and enable the product service, then install the Nginx shared
   snippet and HTTP-only virtual host. Apply the persistent SELinux
   `httpd_sys_content_t` label to `/srv/geardrop` and verify `nginx -t`.
4. Validate HTTP with an explicit `Host: geardrop.100app.dev` before changing DNS.
5. Obtain a certificate, install the TLS virtual host, and validate with
   `curl --resolve` before moving the production DNS record.
6. Install the deploy service/timer only after the first release passes.

## Release gates

```bash
node --test tests/test_product_server.js tests/test_geo_product_endpoint.js
python -m unittest tests.test_direct_server_release
bash -n ops/web/build-release.sh ops/web/deploy-server.sh
```

Each automated release verifies a loopback health endpoint, invalid-SKU 404,
and a live canonical product sampled from `sitemap-products.xml`. A failed
candidate is never activated. A failed post-switch smoke restores the previous
symlink and restarts the prior product service. The release build also rejects
missing or corrupt compressed variants for the homepage, full catalog, dealer
results, and product sitemap.

## Rollback

Server rollback is an atomic `current` symlink change followed by a product
service restart. For a primary-domain rollback, restore the prior 001 content
virtual host before rolling the release back so the legacy entry point serves
content again. Remove the exact `geardrop` A record only after 001 content and
canonical metadata are restored; other `100app.dev` records remain outside
this deployment.
