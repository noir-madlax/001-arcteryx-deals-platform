# GearDrop Support Operations

Public intake URL:

```text
https://001.100app.dev/support.html
```

The public page calls only `public.submit_support_request(...)`. Anonymous and authenticated roles have no direct access to `public.support_requests`; staff access must use the Supabase dashboard or a server-side `service_role` client. Never place a service-role key in the app, static website, screenshots, or support replies.

## Triage

Review new requests without exporting the queue:

```sql
select id, email, subject, message, locale, created_at
from public.support_requests
where status = 'new'
order by created_at asc
limit 100;
```

Claim a request before replying:

```sql
update public.support_requests
set status = 'in_progress', updated_at = now()
where id = '<request-id>' and status = 'new';
```

After the response or requested action is complete:

```sql
update public.support_requests
set status = 'resolved', updated_at = now()
where id = '<request-id>';
```

For privacy or deletion requests, verify control of the submitted email address before deleting or disclosing alert records. Do not request Apple ID passwords, payment-card details, full receipts, or unrelated identity documents. Apple purchase and refund questions should be routed to Apple's standard purchase-management flow; GearDrop can help diagnose entitlement and restore behavior.

## Release smoke

After the database migration and website deployment:

1. Confirm the public Support URL returns HTTP 200 and includes `submit_support_request`.
2. Submit one controlled request, confirm exactly one `new` row, then mark that row `resolved` or delete the smoke row.
3. Confirm `anon` cannot select `support_requests` or insert `price_alerts` directly.
4. Confirm repeat submissions receive a bounded rate-limit response.
5. Review Supabase security and performance advisors and record any findings that apply to the new tables/functions.

Do not use a fabricated customer address for the persistent production smoke. Use an approved address at execution time, or run the database behavior test inside a transaction and roll it back.
