# Security audit report

Scope: the backend (`backend/`), the web frontend (`frontend/`) and their integration, reviewed by reading the source
(about 15,000 lines of backend code plus the frontend modules). Findings are rated by what an attacker could do **before** the fix.

**How this was verified.** The sandbox used for this work has no network access, so `npm install` and a live MongoDB were not
available. What was executed: the 50 original unit tests plus 30 new ones (74 of the 80 pass; the other 6, the JWT tests, are skipped until `npm install` provides `jsonwebtoken`), a static route inventory of all 254 routes,
a check that every one of the frontend's 138 API calls matches a real backend route and HTTP method, an import/export check across
208 destructured imports, PWA validation and an environment-variable documentation check. The API integration tests (`backend/test/integration/`,
50 tests) were written but **have not been run**; they need `npm install` and the first-run MongoDB download described in
[TESTING.md](TESTING.md). Please run them before going live and treat any failure as a real finding.

## Findings and fixes

| ID | Severity | Finding | Fix | Where |
|---|---|---|---|---|
| S-01 | **Critical** | **NoSQL injection in password reset and e-mail verification.** `token` was passed straight into a Mongo query. `{"token": {"$ne": null}}` (JSON) or `?token[$ne]=x` matched an arbitrary user, allowing a password reset or account verification for someone else. | Global sanitiser strips `$`/dotted keys from body, query and params; token fields must be strings of a fixed length; tokens are looked up by SHA-256 hash; `urlencoded` extended mode off. | `middleware/sanitize.middleware.js`, `validators/authValidator.js`, `services/authService.js`, `app.js` |
| S-02 | **High** | **Anyone could register as a teacher** (`role: "teacher"` was accepted on public sign-up), gaining content creation, uploads, grading and AI teacher tools. | Public sign-up always creates a student. New admin endpoints `POST /api/admin/users` and `PUT /api/admin/users/:id/role` (with UI) create teachers; the new user gets a set-password e-mail. `ALLOW_TEACHER_SELF_REGISTRATION=true` restores the old behaviour deliberately. | `authService.js`, `adminUserService.js`, `adminRoutes.js`, `frontend/js/pages/admin/users.js` |
| S-03 | **High** | **Refresh token usable as an access token.** If `JWT_REFRESH_SECRET` was unset it fell back to `JWT_SECRET`, and the access-token check never looked at the token type, so a 7-day refresh token worked as an access token. Algorithm was not pinned. | One module signs and verifies all JWTs: algorithm pinned to HS256, `type`/`aud`/`iss` required and checked, unique `jti`, separate secrets enforced (the server refuses to start in production with weak, placeholder or identical secrets). Used by REST, Socket.IO and classroom tokens. | `utils/tokens.js`, `config/env.js`, `middleware/authMiddleware.js`, `sockets/index.js`, `services/classroomAuthService.js` |
| S-04 | **High** | **Every uploaded file was public** (`express.static('uploads')`): paid lesson videos, students' assignment submissions and private chat attachments could be fetched by anyone with the URL. | Avatars and thumbnails stay public. Everything else needs a short-lived HMAC-signed link bound to the file and the user, issued by `POST /api/files/sign` only after checking enrolment, paid access, ownership or conversation membership. Frontend signs links through `js/core/files.js`. | `services/fileAccessService.js`, `routes/fileRoutes.js`, `utils/signedUrl.js`, `frontend/js/core/files.js` |
| S-05 | **High** | **Stored XSS via uploads.** The stored file extension came from the client's file name and the type from the client's header, so `page.html` sent as `image/png` was saved as `.html` and served from the API origin. | Extension derived from the validated MIME type; magic-number check of the real file bytes (the file is deleted on mismatch); only known extensions are served; `nosniff`, restrictive CSP and `Cross-Origin-Resource-Policy` on file responses; `attachment` for non-media. | `utils/fileSignature.js`, `config/multer.js`, `routes/fileRoutes.js` |
| S-06 | Medium | Refresh, e-mail-verification and password-reset tokens were stored in clear text in MongoDB (a database leak gave working tokens). No reuse detection. | Only SHA-256 hashes are stored. Reusing an already-rotated refresh token revokes all of that user's sessions. | `authService.js` |
| S-07 | Medium | A suspended account could be reactivated by clicking an old verification link; restoring an unverified user made it active. | Verification only moves `pending` to `active`; restore returns unverified users to `pending`. | `authService.js`, `adminUserService.js` |
| S-08 | Medium | Account enumeration: unknown e-mails skipped bcrypt (timing difference); the lock-out message revealed that an account exists. | Dummy bcrypt compare, identical message for wrong password and locked account. (Registration still answers "already exists", see residual risks.) | `authService.js` |
| S-09 | Medium | Users' own payment records included the raw gateway response (`providerPayload`). | Excluded from every user-facing projection. | `services/paymentService.js` |
| S-10 | Medium | Socket.IO: unvalidated payloads, no rate limits, any classroom participant could broadcast arbitrary "shared material" objects to everyone, display names were client-chosen (impersonation), typing events were relayed to rooms the sender never joined, tokens accepted in the URL query. | Strict payload validation, per-socket token buckets, teacher-only allow-listed material broadcast, display name taken from the signed join token, room-membership check, 16 KB signalling cap, 1 MB buffer cap, token only from `auth`. | `sockets/*.js` |
| S-11 | Medium | Regex injection / ReDoS in admin user and course search (`new RegExp(search)`). | Input is escaped and length-capped. | `adminUserService.js`, `adminCourseService.js` |
| S-12 | Medium | Unbounded `?limit=` allowed dumping or stalling large collections. | `limit` capped at 100, `page` normalised, for every endpoint. | `sanitize.middleware.js` |
| S-13 | Medium | User-controlled text (names, notification messages, receipt descriptions) was placed unescaped into HTML e-mails. | HTML-escaped. | `authService.js`, `notificationService.js`, `receiptService.js` |
| S-14 | Medium | Access tokens stayed valid for up to 15 minutes after a password change or reset. | `passwordChangedAt` is checked on every request and socket handshake. | `User.js`, `authMiddleware.js` |
| S-15 | Medium | Spreadsheet import used `xlsx@0.18.5`, which has known vulnerabilities (prototype pollution, ReDoS) fixed only in builds from the SheetJS CDN; any file type could be sent to the importer. | Dependency pinned to SheetJS 0.20.3 (CDN tarball), formulas/HTML/styles not parsed, 5,000-row cap, spreadsheet MIME types only, temp file always deleted. | `package.json`, `utils/excel.util.js`, `questionBankController.js` |
| S-16 | Low | CORS and Socket.IO accepted a single origin, so the Android app (`https://localhost`) could not be added; no `trust proxy` handling broke rate limiting behind Nginx or a PaaS. | Allow-list `CLIENT_URL` + `CORS_ORIGINS`; `TRUST_PROXY`. | `app.js`, `server.js`, `config/env.js` |
| S-17 | Low | No password maximum (bcrypt silently ignores bytes past 72; huge inputs are a CPU-DoS) and no common-password check. | 72-byte maximum, short blocklist, strings only. | `authValidator.js` |
| S-18 | Low | Backups ran through a shell command string; restore trusted the stored file path. | `execFile` (no shell) and the path must be inside `backups/`. | `backupService.js` |
| S-19 | Low | External lesson/meeting links accepted non-http schemes; the frontend put them straight into `href`. | `http`/`https` only on the server; `safeHref()` on the client. | validators, `frontend/js/pages/learn.js` |
| S-20 | Low | Rate limiting was per IP only; refresh, verify-email and uploads were unlimited. | Added per-IP+e-mail login limiter, refresh limiter, upload limiter. | `rateLimiter.middleware.js`, `authRoutes.js`, `app.js` |
| S-21 | Low | API responses were cacheable by browsers and proxies. | `Cache-Control: no-store` on `/api`. | `sanitize.middleware.js` |
| S-22 | Low | Profile avatar clean-up built a file path from the stored URL. | `path.basename` on a fixed folder. | `authService.js` |

## Integration defects found and fixed while auditing

| Defect | Effect | Fix |
|---|---|---|
| Verification and reset e-mails linked to `/verify-email` and `/reset-password`, pages that do not exist in the frontend | Nobody could verify an account or reset a password from the e-mail | Links now point to `auth.html?mode=verify-email` / `?mode=reset` (configurable: `EMAIL_VERIFY_PATH`, `EMAIL_RESET_PATH`) |
| Certificate QR code and printed URL used `<CLIENT_URL>/verify/<id>`; the frontend page is `verify.html?id=` | Scanning a certificate led to a 404 | Default is now `<CLIENT_URL>/verify.html?id=<id>`; base URLs ending in `?id=` are supported |
| `PAYMENT_CALLBACK_PATH` defaulted to `/payment/callback` | Gateway returned users to a missing page | Default is `/payment-callback.html` |
| Lesson images are stored as `{ url, caption }`; the frontend read `fileUrl` | Lesson images never displayed | Frontend reads `url` |
| Teachers could not open students' submitted files | Grading from the UI was impossible for file answers | File links added to the grading dialog (signed on demand) |
| Public sign-up could not produce teachers after S-02 | Nobody could teach | Admin "Add user" / "Change role" |
| 12 environment variables were read but undocumented | Misconfiguration | `.env.example` rewritten; `tools/check-env-docs.js` enforces it |

## Residual risks (not fixed, and why)

1. **Tokens in `localStorage`.** The frontend never uses `innerHTML` (all text goes through DOM text nodes), which makes XSS unlikely, but any XSS would expose
   the tokens. Mitigate with the CSP in [DEPLOYMENT](../README.md#deployment). Moving to HttpOnly cookies would need CSRF protection and same-site hosting of the API and the app, a bigger architectural change.
2. **CSRF.** Not applicable today: authentication is a `Bearer` header, no cookie authenticates a request. If you ever add cookie sessions, add CSRF tokens and `SameSite`.
3. **Rate limits and live-class presence are in memory.** Correct for one server process. For several instances use a shared store (Redis) for `express-rate-limit` and the Socket.IO adapter.
4. **Registration reveals whether an e-mail exists** (409). Removing this needs an e-mail-first sign-up flow; the login, reset and verify flows do not reveal it.
5. **No malware scanning of uploads.** Types and contents are verified, but a valid PDF/Office file can still carry malware. Add ClamAV or move uploads to object storage with scanning.
6. **Paystack/Flutterwave live behaviour** could not be exercised here (no gateway keys, no network). The payment code itself was already sound (server-side pricing, gateway re-verification, atomic settlement, duplicate-transaction index); test the whole flow in the gateways' sandbox.
7. **Native push (FCM)** is implemented but untested here; see [PUSH.md](PUSH.md).
8. **Dependencies.** Run `npm audit --omit=dev` in `backend/` after installing; the lock file was not available to audit offline.
