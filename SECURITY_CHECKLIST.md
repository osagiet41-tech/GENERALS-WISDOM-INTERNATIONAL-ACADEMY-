# Security checklist

Tick every box before the first real user. `[x]` = enforced by the code in this repository; `[ ]` = something you must do on your server.

## Authentication and sessions
- [x] Passwords hashed with bcrypt (cost 12, configurable), 8-72 characters, complexity rules, common passwords refused
- [x] Account lock-out after 5 failures (30 min) plus per-IP and per-IP+e-mail rate limits
- [x] Identical response and timing for unknown e-mail / wrong password / locked account
- [x] Short-lived access tokens (15 min); rotating refresh tokens stored **hashed**; reuse of a rotated token revokes all sessions
- [x] JWT algorithm pinned, `type`/`aud`/`iss` verified, refresh/classroom tokens cannot be used as access tokens
- [x] Password change/reset invalidates existing access tokens immediately
- [x] E-mail verification and reset tokens are random, expire (24 h / 1 h), single use, stored hashed
- [x] Public sign-up creates students only; teachers are provisioned by an admin
- [ ] `JWT_SECRET` and `JWT_REFRESH_SECRET` generated randomly (48+ bytes), different, stored only in the server environment
- [ ] Admin account created with `npm run seed:admin` and a strong unique password; seed password removed from shell history / env afterwards

## Authorization
- [x] Every route is authenticated except an explicit allow-list (14 routes); enforced by `test/unit/route-security.test.js`
- [x] Role checks on all `/api/admin/*`, `/api/student/*`, AI and write routes; ownership checks on course content, submissions, conversations, payments, certificates, notifications
- [x] Generated test calls every protected route without a token (expects 401) and with the wrong role (expects 403)
- [x] Admins cannot suspend or re-role themselves; admin roles cannot be changed through the API

## Injection and input
- [x] Mongo operator keys removed from all input; token/credential fields must be strings
- [x] express-validator on all write routes; request body limited to 1 MB; urlencoded nesting disabled
- [x] Regex search input escaped; pagination capped at 100
- [x] No `eval`, no shell with user input (backups use `execFile`)
- [x] Frontend renders API data as text nodes only; external links limited to http(s)
- [x] HTML e-mails escape user text

## Files
- [x] Allow-listed MIME types, size limits per type, extension chosen by the server, magic-number verification
- [x] Private files only through signed, expiring, user-bound links after an access check; path traversal impossible
- [x] Uploaded files served with `nosniff`, restrictive CSP, `attachment` for documents
- [x] Spreadsheet import: patched SheetJS, formulas disabled, row cap, type check
- [ ] Uploads directory on a volume that is backed up and not executable; consider malware scanning

## Network, CORS, headers
- [x] Helmet security headers; `x-powered-by` removed; `Cache-Control: no-store` on the API
- [x] CORS and Socket.IO limited to `CLIENT_URL` + `CORS_ORIGINS`
- [ ] HTTPS everywhere (TLS terminated by Nginx/PaaS); HSTS enabled at the proxy
- [ ] `TRUST_PROXY=1` when behind a proxy
- [ ] CSP header on the frontend host (example in README, Deployment)
- [ ] MongoDB not exposed to the internet; authentication on; IP allow-list (Atlas) or private network

## Payments
- [x] Prices computed only on the server; the client sends no amount
- [x] Payment success is decided by the gateway's server API / signed webhook, never by the browser
- [x] Amount and currency re-checked, atomic settlement, unique index on gateway transaction ids (no double credit)
- [x] Discount reservation/release, per-user payment rate limit, raw gateway payload never shown to users
- [ ] Webhook URLs registered in the Paystack/Flutterwave dashboards; `FLUTTERWAVE_SECRET_HASH` set; **test keys** until a full sandbox run passes

## Real-time
- [x] Socket.IO handshake requires a valid access token (classroom namespace: a signed single-class join token)
- [x] Payload validation, rate limits, room-membership checks, teacher-only controls enforced on the server

## Secrets
- [x] `.env`, uploads, backups and signatures are git-ignored; no secret is sent to the browser
- [x] Password hashes, tokens and reset/verification secrets never serialised (schema `select:false` plus a `toJSON` transform)
- [ ] Rotate any secret that has ever been committed, pasted into chat or shared by e-mail

## Operations
- [ ] `NODE_ENV=production`, process manager (PM2/systemd/Docker) with restart on failure
- [ ] Log retention and monitoring; alerts on 5xx spikes and repeated 401/429
- [ ] Regular `npm audit --omit=dev`; dependency updates
- [ ] Database backups (`/api/admin/backups` or Atlas snapshots) and a tested restore
- [ ] Run `npm run test:all` and the manual checks in [TESTING.md](TESTING.md) before every release
