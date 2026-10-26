# Deployment

Topology: static frontend (`frontend/`) on its own origin + Node API (`backend/`) + MongoDB. CORS and Socket.IO accept only `CLIENT_URL` (+ `CORS_ORIGINS`).

## 1. Before the first deploy
- [ ] `cd backend && cp .env.example .env`; set `NODE_ENV=production`, `MONGODB_URI`, `CLIENT_URL` (exact frontend origin, no trailing slash), `EMAIL_*`.
- [ ] Generate two different secrets (>= 32 chars): `node -e "console.log(require('crypto').randomBytes(48).toString('hex'))"` for `JWT_SECRET` and `JWT_REFRESH_SECRET`. The server refuses to start in production otherwise.
- [ ] Behind a proxy (Nginx, Render, Railway, Cloudflare): `TRUST_PROXY=1`.
- [ ] Payments: use TEST keys until checkout -> webhook -> access works. Webhook URLs: `https://API/api/webhooks/...` (see docs/PAYMENTS.md).
- [ ] `npm install` in root and `backend/` once, then commit both `package-lock.json` files (none exist yet) so builds are reproducible.
- [ ] Android app: add `https://localhost` to `CORS_ORIGINS`.

## 2. Frontend
1. Copy `frontend/config.production.example.js` to `frontend/config.js` with your API domain.
2. `npm run build` (regenerates `frontend/sw.js` with a new cache version; run it on every release).
3. Publish the `frontend/` folder to any static host (Netlify, Cloudflare Pages, Nginx). Serve over HTTPS (required for the PWA and service worker).

## 3. API
**Docker:** `docker compose up -d --build` (API + MongoDB, volumes for uploads, backups, signatures, logs).
**Without Docker:** `cd backend && npm ci --omit=dev && NODE_ENV=production node server.js` under a process manager (pm2/systemd).
Then once: `npm --prefix backend run seed:admin` and `npm --prefix backend run seed:plans`.
Health check: `GET /api/health`.

## 4. Persistent storage
`backend/uploads`, `backups` and `storage/signatures` are git-ignored and must live on a persistent disk or volume. Ephemeral platforms (Render free tier, Heroku) will lose uploads on every restart.

## 5. Verify
- `npm test` and `npm run test:integration` pass.
- Register, log in, upload a lesson file, pay with a test card, receive the webhook, download a certificate.
- Rotate the seeded admin password after first login.
