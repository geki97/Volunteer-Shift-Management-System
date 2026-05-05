# Supabase (Optional)

This folder contains an optional Supabase Edge Function to support GitHub Pages check-ins.

## Why this exists

GitHub Pages is static, so it cannot write attendance by itself. The static page posts the QR token to a hosted endpoint, which verifies the token (HMAC + expiry) and then inserts a row into the database.

## Edge Function: `checkin`

Deploy `supabase/functions/checkin/index.ts` as an Edge Function named `checkin`.

Configure environment variables on Supabase:

- `QR_SIGNING_KEY` (must match your `.env` used to generate QR tokens)
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `ALLOWED_ORIGINS` (comma-separated allowed browser origins; defaults to `https://geki97.github.io`)

Then set the frontend config in:

- `docs/web/static/js/pages_config.js`

Example:

```js
window.VMS_CONFIG = {
  checkinApiUrl: "https://<project>.functions.supabase.co/checkin",
  dataBasePath: "./appflowy_exports",
};
```

## Database table

Use these migrations:

- `supabase/migrations/20260426_create_checkins.sql` (creates table)
- `supabase/migrations/20260429_harden_checkins_nonce.sql` (prevents nonce replay via a unique index)
