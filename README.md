# Generals Wisdom International Academy: web frontend

Plain HTML5, CSS3 and vanilla JavaScript (ES modules). No build step, no dependencies.

## Run it
1. Edit `config.js`: set `apiBase` and `socketUrl` to your backend.
2. In the backend `.env` set `CLIENT_URL` to the exact origin that serves this folder (CORS is locked to it), and
   `PAYMENT_CALLBACK_PATH=/payment-callback.html`.
3. Serve this folder with any static server, e.g. `npx serve .` or `python3 -m http.server 8080`.
   Open `index.html`. Live classroom camera/mic need HTTPS (or localhost).

## Pages
| File | Interface |
|---|---|
| `index.html`, `auth.html`, `verify.html` | Public website, sign in / register / reset, certificate verification |
| `student.html` | Student dashboard: overview, courses, assignments & exams, live classes, progress, certificates, billing |
| `teacher.html` | Teacher dashboard: courses, live classes, assessments & grading, question bank, announcements, signature |
| `admin.html` | Administrator dashboard: users, courses, payments, plans & discounts, subscriptions, certificates, reports, audit log, settings, backups |
| `classroom.html` | Live classroom (Socket.IO + WebRTC mesh) |
| `ai.html` | AI study / teaching assistant |
| `messages.html` | Messaging (REST + Socket.IO) |
| `learn.html` | Course learning interface |
| `exam.html` | Examination interface (timer, auto-save, palette, mark for review) |
| `payment-callback.html` | Where Paystack/Flutterwave return; the server re-verifies the payment |

## Structure
```
css/        base (tokens, forms, buttons) · layout (shell, public site) · components
js/core/    config, http (auth header, one token refresh, errors), session, theme, dom, format
js/ui/      shell, router, modal, toast, table, pagination, search, form, tabs, states, socket, markdown
js/api/     one thin module per backend area: the only place endpoints are written
js/pages/   one entry module per HTML page; views under student/ teacher/ admin/ shared/
```
HTML files contain markup only. All data comes through `js/api/*`; rendering uses `h()` which sets text nodes, so API data is never parsed as HTML.

## Things to know
* **No course catalogue endpoint.** The backend has no public or student "browse courses" route; students enrol by
  Course ID (teachers can copy it from *My courses*). The public site therefore shows plans, not a course list.
  Add e.g. `GET /api/courses/catalog` (published courses only) and a student view can use it.
* Tokens are kept in `localStorage`. That is simple and survives reloads, but any XSS could read them; the UI avoids
  `innerHTML`, and you should keep a strict CSP on the host serving this folder.
* Some admin/report screens render whatever columns the backend returns, so they adapt to your data.
* Live video is peer-to-peer (mesh), fine for small classes. For large classes use the SFU adapter on the server;
  add a TURN server to `iceServers` in `config.js` for students on strict networks.
* Browser-tested with Playwright (Chromium) against a mocked API: every page loads with no console errors, plus login,
  certificate verification, exam answer/submit, theme toggle, mobile drawer and form validation. It has not been run
  against your live server.
