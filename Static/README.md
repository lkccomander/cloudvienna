# Static Registration Site

This folder contains a plain static site to collect student pre-registrations.

## Files

- `index.html`: Form UI
- `styles.css`: Styling
- `app.js`: API submission logic (`POST /public/pre-registrations`)

## Configure API URL

Set `window.__API_BASE_URL__` in `index.html` before loading `app.js`.

Example:

```html
<script>
  window.__API_BASE_URL__ = "https://your-api.up.railway.app";
</script>
```

## Railway deployment model

1. Deploy backend API service (FastAPI) on Railway.
2. Deploy static site as another Railway service (Nginx/static) or any static host.
3. In backend env vars, set:
   - `API_CORS_ALLOW_ORIGINS=https://your-static-site.up.railway.app`
4. Form submissions are stored in `t_web_pre_registrations`.
5. Staff imports pending rows using:
   - `POST /pre-registrations/import?dry_run=true`
   - `POST /pre-registrations/import?dry_run=false`
