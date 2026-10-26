# Testing strategy

Three layers, from fastest to broadest. Everything is plain `node:test`; no test framework to learn.

| Layer | What it proves | Needs | Command |
|---|---|---|---|
| **Static checks** | Routes, imports, PWA files and env docs are consistent | Node only (no install, no database) | `npm test` (root) |
| **Unit tests** | Security utilities, token rules, upload signatures, signed URLs, pricing/discounts, payment gateways, certificates | `npm install` for the JWT tests only | `npm run test:unit` |
| **API integration tests** | Real Express app + in-memory MongoDB: auth, authorization, IDOR, uploads, payments, admin | `npm install` + dev dependencies (below) | `npm run test:integration` |

## Commands

```bash
# one-time
npm run install:all                                   # root + backend dependencies
npm --prefix backend i -D supertest mongodb-memory-server   # already listed in devDependencies; first run downloads a MongoDB binary (~100 MB)

# everyday
npm test                    # unit + static checks (fast, no database)
npm run test:integration    # API tests against an in-memory MongoDB
npm run test:all            # everything
npm run check:routes        # every frontend API call matches a backend route + method
npm run check:imports       # every backend require() and destructured import resolves
npm run check:pwa           # manifest, icons, service worker precache, pages wired
npm run check:env           # every env variable the code reads is documented
npm run audit               # npm audit for known vulnerable dependencies
node backend/scripts/route-inventory.js     # table of all routes, auth and roles
```

Integration tests skip themselves with a clear message when `supertest` / `mongodb-memory-server` are missing, so `npm test` never fails for the wrong reason.

## Coverage by feature area

"Auto" means an automated test exists in this repository. "Auth matrix" means the generated test that calls **every** route of the area without a token (must be 401) and with the wrong role (must be 403) (`authorization-matrix.test.js`). Anything marked **manual** has no automated functional test yet, use the checklist below.

| Area | Automated coverage | Still manual |
|---|---|---|
| Registration | Auto: creates pending student, no secrets in response, teacher/admin role escalation blocked, weak/over-long/non-string passwords rejected | E-mail delivery |
| Login | Auto: generic errors (no enumeration), lock-out, NoSQL operator payloads, pending/suspended blocked | Real SMTP |
| Authentication (JWT, refresh, reset) | Auto: refresh-as-access rejected, `alg:none`/tampered tokens, rotation + reuse detection, hashed storage, reset/verify injection, password change invalidation, token unit tests (need install) | |
| Authorization | Auto: route allow-list test, admin/student prefix test, **generated 401/403 matrix over all 254 routes** | |
| Courses | Auto: IDOR (other teacher, student writes), enrolment, draft invisibility, paid content 402 | Create/edit happy path through UI |
| Lessons | Auto: enrolment and draft rules, upload by students refused, auth matrix | Create/reorder/complete flow, video progress |
| Assignments | Auto: auth matrix, submission IDOR | Submit with file, due-date behaviour |
| Quizzes / Examinations | Auto: auth matrix | Timer, auto-save, auto-submit, shuffled questions, answer leakage (see checklist) |
| Grading | Auto: only the owning teacher/admin can open or grade a submission | Score validation, "return to student" |
| Messaging | Auto: outsiders cannot read/post, student-to-student blocked | Real-time delivery, read receipts |
| Notifications | Auto: cannot mark someone else's notification | Delivery, bell counter |
| AI assistant | Auto: role scoping of all 21 AI routes (matrix + route test) | Needs `AI_API_KEY`; quotas and answers |
| Payments | Auto (unit): pricing, discounts, money maths, Paystack/Flutterwave signature + verify logic. Auto (API): IDOR on payments/receipts/verify, price tampering, unsigned webhooks refused, no raw payload exposure | Full sandbox checkout (see below) |
| Certificates | Auto (unit): rendering, eligibility, service logic. Auto (API): public verify 404 and no data leak, cross-student download blocked | Issue on completion, PDF download, QR scan |
| File uploads | Auto: disguised HTML-as-PNG rejected, disallowed types, server-chosen names, size limit, students refused, signed URL rules, traversal | Large video upload on a slow link |
| Live classroom | Auto: auth matrix (join token endpoints) | Camera/mic, multi-user signalling, teacher controls (needs 2+ browsers) |
| Admin functions | Auto: teacher provisioning, self-suspension/role guards, suspended users locked out immediately, no secrets in listings, capped page size | Reports export, backups, settings |

## Manual checklist (30 minutes, before each release)

1. **Sign-up and e-mail**: register, open the e-mail link (lands on `auth.html?mode=verify-email`), sign in. Forgot password, open the link, set a new password, old session is signed out.
2. **Roles**: admin > Users > Add user (teacher); teacher receives the set-password e-mail and can sign in; a student cannot open `teacher.html` or `admin.html` content (redirected) and the API returns 403 for their token.
3. **Teaching flow**: teacher creates course > subject > module > lesson (text, PDF, video, image), publishes; student enrols, opens the lesson, media plays (signed links), marks complete.
4. **Assessment flow**: teacher creates assignment, quiz and exam (question bank); student submits assignment with a file, takes the quiz and exam; check that the exam page never exposes correct answers in the network tab; teacher grades; student sees the result.
5. **Certificates**: complete a course with certificate enabled; download the PDF; scan the QR code or open the printed link: `verify.html?id=` shows the details; revoke from admin and re-check.
6. **Payments (gateway sandbox, test keys)**: paid course checkout > pay with a test card > return page shows "confirmed" > course unlocks. Repeat with a discount code, an abandoned payment, and by calling the webhook twice (no double access). Confirm that changing the amount in the browser dev tools changes nothing.
7. **Live class**: teacher starts a class, two students join from different devices (camera, mic, chat, hand raise, teacher mute); students on mobile data also connect (add a TURN server if not).
8. **Messaging and notifications**: two users exchange messages in real time; unread counters update; a notification appears in the bell.
9. **PWA**: Chrome > DevTools > Application > Manifest and Service Workers show no errors; Lighthouse "Installable" passes; turn on Offline: previously opened pages load, `offline.html` shows for new ones, banner says "You are offline".
10. **Android**: install the APK, sign in, open a lesson, switch to airplane mode (app shell still opens), receive a push notification.

## Writing new tests

* Pure logic: add `backend/test/unit/<name>.test.js` (no database, no network).
* API behaviour: add `backend/test/integration/<name>.test.js` and use the helpers (`boot()`, `actor('student')`, `itest(test, ...)`).
* New endpoint: nothing to do for authorization, the matrix and the public-route allow-list pick it up automatically. A route that is public on purpose must be added to `PUBLIC_ALLOW_LIST` in `route-security.test.js` (a reviewed decision).
