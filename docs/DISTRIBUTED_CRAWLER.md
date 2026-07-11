# Distributed crawler roles

The production crawler uses Supabase leases to keep one writer per scope.

| Node | Primary role | Schedule |
|---|---|---|
| `oci-free-a1` | Outlet plus MEC (MEC is blocked from Lightsail egress) | every 3 hours, MEC offset 60 minutes |
| `aws-lightsail-us-west-2` | EVO/REI/SSENSE and daily URL revalidation | every 3 hours, offset 90 minutes |
| GitHub Actions | Outlet and EVO/REI/SSENSE fallback; all-source freshness monitor | runs only when the corresponding primary is stale/failed |

Each server wrapper claims `outlet`, `mec`, `dealers`, or `revalidate` before writing.
An active lease makes overlapping cron or GitHub runs exit without crawling.

`dealers/results.json` records `fresh_dealers` and a per-dealer `refreshed_at`.
Seeded fallback blocks remain available to the static client, but
`dealers.supabase_sync` skips them so a failed scrape cannot fake freshness.
MEC currently has OCI as its primary verified egress. GitHub-hosted runner
egress was verified with the manual `Diagnose MEC Egress` workflow
(52/52/24 items on 2026-07-11). `Refresh MEC Data` checks 20 minutes after
each OCI window and claims the same `mec` lease only when the primary is stale
or failed.

Apply these migrations before enabling the schedules:

1. `dealers/supabase_migration_product_lifecycle.sql`
2. `dealers/supabase_migration_crawler_leases.sql`

Deploy server-specific crontabs from `ops/cron/`. Keep the previous crontab as
`crontab.before-distribution-<timestamp>` on each node for rollback.

Server Git remotes use the dedicated `~/.ssh/arcteryx_deploy_ed25519` key via
the repository-local `core.sshCommand` and must not contain PATs.
