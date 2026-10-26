# Generals Wisdom International Academy (GWIA)

A complete online learning platform: **REST API + real-time services** (Node.js, Express, MongoDB, Socket.IO), a **mobile-first web app / PWA** (plain HTML, CSS and JavaScript, no build step) and an **Android app** (Capacitor) from the same code.

## Contents
1. [Overview and features](#1-overview-and-features) · 2. [Technology stack](#2-technology-stack) · 3. [Folder structure](#3-folder-structure) · 4. [Installation](#4-installation) · 5. [Environment variables](#5-environment-variables) · 6. [MongoDB setup](#6-mongodb-setup) · 7. [Development](#7-development-commands) · 8. [Production](#8-production-commands) · 9. [API documentation](#9-api-documentation) · 10. [Deployment](#10-deployment) · 11. [Android APK](#11-android-apk-build) · 12. [Security](#12-security-recommendations) · 13. [Testing](#13-testing) · 14. [Status and known limits](#14-status-and-known-limits)

## 1. Overview and features

**Roles:** student, teacher, administrator.

| Area | What it does |
|---|---|
| Accounts | Registration with e-mail verification, login, refresh tokens, password reset/change, profile + photo, account lock-out, admin-provisioned teachers |
| Courses | Course > subject > module > lesson hierarchy; text, images, PDF, audio, video, attachments, external links; prerequisites; draft/published; co-teachers; thumbnails; announcements; discussion forum with moderation |
| Learning | Enrolment, progress tracking, video progress, lesson completion, learning interface |
| Assessment | Assignments with file/text submission, quizzes, timed exams (shuffle, auto-save, auto-submit, attempts), question bank with spreadsheet import, grading and feedback, results |
| Live classroom | Scheduled live classes, WebRTC video/audio (mesh), screen share, chat, hand raise, teacher controls, shared materials, attendance, recording hooks, SFU adapter stub |
| Messaging | Real-time 1:1 messaging (student/teacher), attachments, read receipts, presence, search |
| Notifications | In-app (real-time), e-mail, push (Web Push + FCM) |
| AI assistant | Teacher tools (lesson plans, quizzes, marking guides ...) and student tools (explanations, hints, practice, revision plans) with per-user quotas; the API key never leaves the server |
| Payments | Free and paid courses, monthly/annual subscriptions, free trials, discount codes, Paystack and Flutterwave, NGN and international currencies, receipts (PDF + e-mail), automatic access restriction on expiry |
| Certificates | Auto-issued on completion, PDF download, QR code, public verification page |
| Administration | Dashboards, user management, course moderation, payments/subscriptions, plans and discounts, reports (Excel export), audit log, settings, database backups |
| PWA / mobile | Installable, offline app shell, update prompt, mobile bottom navigation, push, Android APK |

## 2. Technology stack

* **Backend:** Node.js 18+, Express 4, Mongoose 8 / MongoDB 6+, Socket.IO 4, JWT (`jsonwebtoken`), bcryptjs, express-validator, helmet, express-rate-limit, multer, Nodemailer, PDFKit, SheetJS, optional `web-push` / `firebase-admin` / `qrcode`
* **Frontend:** HTML5, CSS3, vanilla JavaScript (ES modules), Service Worker, Web App Manifest
* **Mobile:** Capacitor 6 (Android WebView), Firebase Cloud Messaging for native push
* **Payments:** Paystack, Flutterwave (server-to-server verification and signed webhooks)
* **Testing:** `node:test`, supertest, mongodb-memory-server

## 3. Folder structure

```
gwia/
├── backend/
│   ├── server.js                 HTTP + Socket.IO bootstrap, cron jobs, graceful start
│   ├── src/
│   │   ├── app.js                Express app: security middleware, CORS, routes, error handling
│   │   ├── config/               env (validated), db, multer (uploads), logger
│   │   ├── middleware/           auth, roles, ownership, rate limiters, sanitiser, validation, errors
│   │   ├── models/               Mongoose schemas
│   │   ├── routes/ controllers/ services/ validators/    one set per feature (thin controllers, logic in services)
│   │   ├── sockets/              /  (messaging, notifications) and /classroom namespaces
│   │   ├── jobs/                 expiry, reconciliation, certificate evaluation
│   │   └── utils/                tokens (JWT), security helpers, file signatures, signed URLs, e-mail, money
│   ├── seed/                     admin + plans seeders
│   ├── scripts/                  test runner, route inventory, maintenance scripts
│   ├── test/                     unit/ and integration/ tests
│   ├── uploads/ storage/ backups/ logs/     runtime data (git-ignored)
│   └── .env.example              every environment variable, documented
├── frontend/
│   ├── *.html                    one page per interface (markup only)
│   ├── config.js                 API / Socket URL: the only file edited per deployment
│   ├── manifest.json sw.js sw.template.js offline.html icons/      PWA
│   ├── css/                      base, layout, components
│   └── js/ core/ api/ ui/ pages/ pwa.js
├── resources/                    icon + splash sources for the Android app
├── tools/                        build-pwa, serve-frontend, route/import/env/PWA checks, API-doc generator, android-setup
├── docs/                         SECURITY_AUDIT, SECURITY_CHECKLIST, TESTING, ANDROID, PUSH, PAYMENTS, CERTIFICATES, API_ROUTES
├── capacitor.config.json         Android app configuration
└── package.json                  project-level scripts
```

## 4. Installation

Requirements: **Node.js 18+**, **MongoDB** (local or Atlas), an SMTP account for e-mail. (Android build: see section 11.)

```bash
git clone <your-repo> gwia && cd gwia
npm run install:all                       # installs root + backend dependencies

cp backend/.env.example backend/.env      # then edit it (section 5)
node -e "console.log(require('crypto').randomBytes(48).toString('hex'))"    # run twice: JWT_SECRET and JWT_REFRESH_SECRET

# first administrator (password supplied on the command line, never hard-coded)
SEED_ADMIN_EMAIL=you@school.org SEED_ADMIN_PASSWORD='Use-A-Strong-Passw0rd!' npm --prefix backend run seed:admin
npm --prefix backend run seed:plans       # optional: example subscription plans

# frontend: edit frontend/config.js (apiBase, socketUrl) for your API address
```

Then run the app as described in section 7. Create teachers from **Admin > Users > Add user** (public sign-up creates students only).

## 5. Environment variables

All variables are documented, with defaults and examples, in [`backend/.env.example`](backend/.env.example) (a check, `npm run check:env`, fails if the code reads one that is not listed). The essentials:

| Variable | Required | Meaning |
|---|---|---|
| `MONGODB_URI` | yes | MongoDB connection string |
| `JWT_SECRET`, `JWT_REFRESH_SECRET` | yes | 32+ random characters each, **different**. Production refuses to start otherwise |
| `CLIENT_URL` | yes | Exact origin of the frontend (CORS, e-mail links) |
| `CORS_ORIGINS` | Android | Extra allowed origins, e.g. `https://localhost` for the APK |
| `EMAIL_HOST/PORT/USER/PASSWORD/FROM` | yes | SMTP for verification, reset, receipts |
| `TRUST_PROXY` | behind a proxy | `1` when behind Nginx / a PaaS |
| `PAYSTACK_SECRET_KEY`, `FLUTTERWAVE_SECRET_KEY`, `FLUTTERWAVE_SECRET_HASH` | for payments | Server-side only |
| `AI_API_KEY` | for the AI assistant | Server-side only |
| `VAPID_*`, `FCM_SERVICE_ACCOUNT_FILE` | for push | See [docs/PUSH.md](docs/PUSH.md) |
| `FILE_URL_SECRET` | optional | Signs private file links (defaults to a key derived from `JWT_SECRET`) |
| `ALLOW_TEACHER_SELF_REGISTRATION` | optional | Default `false` |

The frontend has no secrets: `frontend/config.js` holds only public URLs.

## 6. MongoDB setup

**Local:** install MongoDB Community 6+, start `mongod`, use `MONGODB_URI=mongodb://localhost:27017/gwia`. `mongodump`/`mongorestore` (MongoDB Database Tools) must be on the server's `PATH` for the admin backup feature.

**Atlas (recommended for production):** create a cluster, a database user with *readWrite* on `gwia`, add your server's IP to the Network Access list (not `0.0.0.0/0` in production), and use the `mongodb+srv://...` string. Collections and indexes (including the unique indexes that stop duplicate payments and certificates) are created automatically on first start by Mongoose.

The message search needs a text index, created automatically. No manual schema steps are required.

## 7. Development commands

```bash
npm run dev:api          # API with auto-reload  (http://localhost:5000, health: /api/health)
npm run dev:web          # static server for the frontend (http://localhost:3000)
npm test                 # unit tests + route/import/PWA/env checks (fast, no database)
npm run test:integration # API tests against an in-memory MongoDB
npm run build            # regenerate the service worker (run after changing frontend files)
npm run docs:routes      # regenerate docs/API_ROUTES.md
node backend/scripts/route-inventory.js    # every route with its auth and roles
```

Make sure `CLIENT_URL=http://localhost:3000` in `backend/.env` and `apiBase` in `frontend/config.js` points at `http://localhost:5000/api`.

## 8. Production commands

```bash
NODE_ENV=production npm --prefix backend start          # or via PM2 / systemd / Docker
npm run build                                           # before publishing the frontend
npm --prefix backend run seed:admin                     # once
npm run audit                                           # dependency vulnerabilities
```

PM2 example: `pm2 start backend/server.js --name gwia-api --time && pm2 save && pm2 startup`.
Scale-out note: rate limits and live-class presence are held in memory; run **one** API process, or add Redis (rate-limit store + Socket.IO adapter) before running several.

## 9. API documentation

* Complete, always-current route table (254 routes, method, path, auth, roles): [`docs/API_ROUTES.md`](docs/API_ROUTES.md)
* Payments and webhooks: [`docs/PAYMENTS.md`](docs/PAYMENTS.md) · Certificates: [`docs/CERTIFICATES.md`](docs/CERTIFICATES.md) · Push: [`docs/PUSH.md`](docs/PUSH.md)

Conventions: JSON; success `{ success, message, data, meta? }`; errors `{ success:false, message, details? }`; `Authorization: Bearer <accessToken>`; `?page=&limit=` (max 100).

| Group | Base path | Highlights |
|---|---|---|
| Auth | `/api/auth` | `register`, `login`, `refresh`, `logout`, `verify-email`, `forgot-password`, `reset-password`, `change-password`, `me`, `profile` |
| Courses | `/api/courses`, `/api/lessons`, `/api/modules` | CRUD, uploads, publish, analytics, announcements, forum |
| Student | `/api/student/*` | dashboard, enrolments, lessons, progress, quizzes/exams (`start`, `attempt/save`, `attempt/submit`), assignments, live classes, certificates |
| Assessments | `/api/assignments`, `/api/quizzes`, `/api/exams`, `/api/submissions` | create, publish, grade |
| Live | `/api/live-classes`, Socket.IO `/classroom` | schedule, start/end, join token, materials |
| Messaging | `/api/messages`, Socket.IO `/` | conversations, messages, read, presence, search |
| AI | `/api/ai/teacher/*`, `/api/ai/student/*`, `/api/ai/usage` | role-scoped generators |
| Billing | `/api/billing/*`, `/api/webhooks/*` | plans, checkout, verify, history, receipts, subscription, trial |
| Certificates | `/api/certificates/verify/:id` (public), `/api/student/certificates/*` | |
| Files | `POST /api/files/sign`, `GET /uploads/...` | signed private file links |
| Push | `/api/push/*` | public key, subscribe, unsubscribe |
| Admin | `/api/admin/*` | users (create, role, suspend), courses, payments, plans, discounts, subscriptions, certificates, reports, audit logs, settings, backups |

Socket.IO: connect to the API origin with `io(url, { auth: { token: accessToken } })`; classroom: `io(url + '/classroom', { auth: { token: joinToken } })` where the join token comes from the join endpoints.

## 10. Deployment

**Topology:** `https://app.yourschool.org` (static frontend) and `https://api.yourschool.org` (API + Socket.IO), both HTTPS.

1. **API server** (VPS, Render, Railway, Fly ...): set environment variables (section 5), `NODE_ENV=production`, `TRUST_PROXY=1`, `CLIENT_URL=https://app.yourschool.org`. Persist `backend/uploads`, `backend/backups` and `backend/storage` on a disk/volume.
2. **Reverse proxy (Nginx) with WebSocket support:**
   ```nginx
   server {
     listen 443 ssl http2;
     server_name api.yourschool.org;
     # ssl_certificate ... (Let's Encrypt / certbot)
     client_max_body_size 200m;                       # largest lesson video you allow
     add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
     location / {
       proxy_pass http://127.0.0.1:5000;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "upgrade";
       proxy_set_header Host $host;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
       proxy_read_timeout 3600s;                       # long-lived WebSockets
     }
   }
   ```
3. **Frontend host** (Nginx, Netlify, Cloudflare Pages, Vercel, GitHub Pages ...): upload the `frontend/` folder after `npm run build`; edit `frontend/config.js`. Serve `sw.js` with `Cache-Control: no-cache` so updates are noticed. Recommended headers (replace the API host):
   ```
   Content-Security-Policy: default-src 'self'; script-src 'self' https://api.yourschool.org; connect-src 'self' https://api.yourschool.org wss://api.yourschool.org; img-src 'self' data: blob: https://api.yourschool.org; media-src 'self' blob: https://api.yourschool.org; frame-src https://api.yourschool.org; style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'
   X-Content-Type-Options: nosniff
   Referrer-Policy: strict-origin-when-cross-origin
   Permissions-Policy: camera=(self), microphone=(self), geolocation=()
   ```
   (`script-src https://api...` is needed because the Socket.IO client script is served by the API.)
4. **Payments:** register `https://api.yourschool.org/api/webhooks/paystack` and `/flutterwave` in the gateway dashboards; set `PAYMENT_CALLBACK_PATH=/payment-callback.html`. Use test keys first.
5. **E-mail:** use a transactional provider (SPF/DKIM configured) so verification e-mails are delivered.
6. **TURN server** (coturn or a hosted TURN) for live classes on mobile networks: add it to `iceServers` in `frontend/config.js`.
7. **Backups:** schedule Atlas snapshots or `mongodump`, and back up `uploads/`.
8. **Verify:** `https://api.yourschool.org/api/health` returns OK; run [the manual checklist](docs/TESTING.md#manual-checklist-30-minutes-before-each-release).

## 11. Android APK build

Short version (full guide with signing, troubleshooting and Play Store notes: [`docs/ANDROID.md`](docs/ANDROID.md)):

```bash
# 1. frontend/config.js -> absolute https API URLs;  backend/.env -> CORS_ORIGINS=https://localhost
npm install
npm run cap:assets          # icons + splash from resources/
npm run cap:add             # adds android/ and patches permissions
npm run apk:debug           # android/app/build/outputs/apk/debug/app-debug.apk
npm run apk:release         # signed release APK (after configuring the keystore)
npm run aab:release         # Play Store bundle
```
Requires JDK 17 and the Android SDK (Android Studio).

## 12. Security recommendations

Everything below is in [`docs/SECURITY_CHECKLIST.md`](docs/SECURITY_CHECKLIST.md); the audit findings and fixes are in [`docs/SECURITY_AUDIT.md`](docs/SECURITY_AUDIT.md).

* Generate long random JWT secrets, keep `.env` out of git, rotate any secret that was ever exposed.
* HTTPS only, HSTS, the CSP above, `TRUST_PROXY=1` behind a proxy.
* Keep MongoDB private (VPC or IP allow-list) with authentication on.
* Use gateway **test** keys until a full sandbox payment, webhook and access cycle passes; never put gateway or AI keys in the frontend.
* Create teachers only through the admin; keep `ALLOW_TEACHER_SELF_REGISTRATION=false`.
* Run `npm run audit` regularly; run the test suites before every release.
* Consider malware scanning for uploads, Redis for multi-instance rate limits, and monitoring/alerting on 5xx and 429 spikes.
* Tokens are kept in `localStorage` by the web app; the CSP and the "text nodes only" rendering rule are what protect them, so do not add `innerHTML` with API data.

## 13. Testing

`npm test` (fast), `npm run test:integration`, `npm run test:all`; strategy, coverage per feature, and the manual release checklist are in [`docs/TESTING.md`](docs/TESTING.md).

## 14. Status and known limits

Being explicit about what was and was not verified when this version was prepared (the build environment had no network or database):

* **Verified by execution:** 74 unit tests pass (50 existing + 24 new; 6 JWT tests await `npm install`); static checks pass: 254 routes inventoried, all 138 frontend API calls match a backend route and method, 208 backend imports resolve, PWA files validated, every environment variable documented.
* **Written but not yet run:** the 50 API integration tests (`npm run test:integration`), the Capacitor/Android build, FCM push, and live Paystack/Flutterwave and SMTP flows. Run them in your environment and treat failures as real findings.
* **Not in scope of the code:** the app has no public course catalogue endpoint (students enrol by course ID); large live classes need an SFU instead of the mesh adapter; single-instance assumptions are listed in section 8.
