# Distributed crawler roles

The production crawler uses Supabase leases to keep one writer per scope.

| Node | Primary role | Schedule |
|---|---|---|
| `oci-free-a1` | Outlet list, SKU detail, Outlet sync | every 3 hours |
| `aws-lightsail-us-west-2` | MEC/EVO/REI/SSENSE and daily URL revalidation | every 3 hours, offset 90 minutes |
| GitHub Actions | monitored fallback | checks each primary window and runs only when stale/failed |

Each server wrapper claims `outlet`, `dealers`, or `revalidate` before writing.
An active lease makes overlapping cron or GitHub runs exit without crawling.

Apply these migrations before enabling the schedules:

1. `dealers/supabase_migration_product_lifecycle.sql`
2. `dealers/supabase_migration_crawler_leases.sql`

Deploy server-specific crontabs from `ops/cron/`. Keep the previous crontab as
`crontab.before-distribution-<timestamp>` on each node for rollback.

Server Git remotes use the dedicated `~/.ssh/arcteryx_deploy_ed25519` key via
the repository-local `core.sshCommand` and must not contain PATs.
