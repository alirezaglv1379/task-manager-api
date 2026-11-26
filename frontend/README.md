# Task Manager Frontend

React + TypeScript + Vite interface for the Task Manager API. The UI is Persian-first and right-to-left.

## Development

```bash
npm install
npm run dev
```

Vite proxies `/api/*` to `http://127.0.0.1:8000/*`, so refresh cookies are used in a same-origin browser context during development.

## Tests

```bash
npm run test
```

## Production build

```bash
npm run build
npm run preview
```

In production, serve the built `dist/` directory and reverse-proxy `/api/*` to the FastAPI backend on the same origin. Configure the backend `CSRF_TRUSTED_ORIGINS` and `CORS_ORIGINS` to the deployed origin. Set `COOKIE_SECURE=true` when HTTPS is enabled.

Access tokens are held only in JavaScript memory. The refresh token is never read by the frontend; it is stored in an HttpOnly cookie by the backend.
