# Static Registration Site

This folder contains a plain static site to collect student pre-registrations.

## Files

- `index.html`: Form UI
- `styles.css`: Styling
- `app.js`: API submission logic (`POST /public/pre-registrations`)
- `wall2.png`: Mosaic-style background image asset
- `nginx.conf.template`: Nginx runtime config template (Railway `${PORT}` + security headers)
- `Dockerfile`: Static container image for Railway (Nginx)

## Configure API URL

Do not hardcode the API URL in `index.html`.

This site loads `config.js` before `app.js`.

Default behavior:
- If `window.__API_BASE_URL__` is set in `config.js`, that value is used.
- Otherwise, `app.js` infers the API from the site hostname:
  - host contains `production` -> `https://backend-unique-tenderness-production.up.railway.app`
  - host contains `stage` or `staging` -> `https://backend-unique-tenderness-stage.up.railway.app`

For local/manual static hosting, you can edit `Static/config.js` directly.

## Railway deployment model

1. Deploy backend API service (FastAPI) on Railway.
2. Deploy static site as another Railway service (Nginx/static) or any static host.
3. In backend env vars, set:
   - `API_CORS_ALLOW_ORIGINS=https://your-static-site.up.railway.app`
4. Form submissions are stored in `t_web_pre_registrations`.
5. Staff imports pending rows using:
   - `POST /pre-registrations/import?dry_run=true`
   - `POST /pre-registrations/import?dry_run=false`

## Current UX/Feature Snapshot (2026-03-11)

- Bilingual form (`Deutsch` default, manual switch to English).
- Localized labels, tooltips, and popup validation messages.
- Gender field constrained to `M` / `F`.
- Hidden `location_id=1` in form payload.
- Contact/footer section with social links (Instagram, X, YouTube, Facebook + website).
- Dark theme card over mosaic background pattern.
- Mobile polish for Android/iPhone:
  - Safe-area padding, larger tap targets, 16px form controls to avoid iOS zoom.

## Common Railway Issues (and fixes)

- `502` on `/` after deploy:
  - Ensure Nginx listens on `${PORT}` in `nginx.conf.template`.
- Build error `nginx.conf.template not found`:
  - Ensure Docker `COPY` paths match build context (usually repo root on Railway).
- Form submits but fails in browser:
  - Confirm `API_BASE_URL` (or generated `config.js`) points to API domain.
  - Confirm backend `API_CORS_ALLOW_ORIGINS` includes static domain.
