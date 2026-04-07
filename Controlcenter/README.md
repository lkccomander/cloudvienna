# Control Center

Frontend V1 del command center web para `cloudvienna`.

## Requisitos

- Node.js 20+
- Backend FastAPI operativo

## Variables

Crear `.env` en esta carpeta si quieres cambiar el backend:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

En Railway, configura `VITE_API_BASE_URL` con la URL publica del backend, por ejemplo:

```env
VITE_API_BASE_URL=https://cloudvienna-production.up.railway.app
```

Ademas, en el backend agrega el dominio del Controlcenter a `API_CORS_ALLOW_ORIGINS`.

## Desarrollo

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```
