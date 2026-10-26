# Certificates

Certificates are issued **automatically** the moment a student satisfies the course's completion requirements,
rendered as a PDF on demand, and verifiable by anyone through a public endpoint.

## 1. What is on the certificate

Student name · course name · institution · completion date · certificate ID · instructor name(s) with signature ·
institution signatory (optional) · verification URL + QR code. Everything is frozen into the certificate at issue
time (`snapshot`), so renaming a student/course or an instructor leaving never changes a certificate already issued.

Certificate ID format: `CERT-7F3K-9QXD-M2WA` (60 random bits, Crockford base32: no I/L/O/U, so it survives being
read aloud or typed). Not sequential, so IDs can't be enumerated.

PDF: A4 landscape. Uses a bundled font (DejaVu, `assets/fonts/`) so Yoruba/Igbo/Hausa letters (ọ ẹ ṣ ń ɓ ƙ …) print
correctly; the built-in PDF fonts cannot draw them. Long names/titles wrap to two lines instead of overflowing.

## 2. When a certificate is issued

Requirements are per course (`course.certificate`), with these defaults:

| Setting | Default | Meaning |
|---|---|---|
| `enabled` | `true` | `false` = this course issues no certificates |
| `minLessonCompletionPercent` | `100` | % of **published** lessons completed |
| `minAverageScorePercent` | `50` | average of the student's **best** graded result per published assignment/quiz/exam; `null` turns the check off. Skipped if the course has no assessments |
| `requireAllAssessments` | `false` | every published/closed assignment, quiz and exam must be graded |
| `minAttendancePercent` | `null` | attendance rate (excused sessions don't count against the student) |
| `showScore` | `false` | print "Final score NN%" on the PDF |

Teachers set these in the normal course create/update API (`certificate: { ... }`).

Automatic triggers (each queues a de-duplicated background check):
lesson marked complete · video finished · teacher grades an assignment/quiz/exam · objective exam auto-graded ·
attendance saved. A 30-minute sweep re-checks anyone whose progress/grades/attendance changed in the last 3 hours
as a safety net. On issue the student gets an in-app notification and an email with the PDF attached.

One certificate per student per course, ever: enforced by a unique index, so simultaneous triggers cannot create two.

## 3. API

Student (`/api/student`, auth)
- `GET  /certificates` list · `GET /certificates/:id` details (`:id` = Mongo id **or** `CERT-…`)
- `GET  /certificates/:id/download` → PDF (`?inline=1` to view in browser). Needs the auth header, so the frontend
  must `fetch` it and save the blob (a plain `<a href>` cannot send the token).
- `GET  /courses/:courseId/certificate/eligibility` → each requirement with required vs actual and met/not met
- `POST /courses/:courseId/certificate` → trigger a check on demand (normally unnecessary). Not eligible → 400
  `details.code = CERTIFICATE_REQUIREMENTS_NOT_MET` with `details.checks`

Public, no auth
```
GET /api/certificates/verify/:certificateId
200 { success, message: "Certificate is valid", data: {
      valid: true, status: "valid", certificateId, studentName, courseTitle,
      institutionName, instructors: [..], completionDate, issuedAt } }
200 { data: { valid: false, status: "revoked", certificateId, revokedAt } }
404 { success: false, valid: false, message: "No certificate matches this ID" }
GET /verify/:certificateId        ← human-readable HTML page; this is what the QR code opens
```
Returns no email, internal ids or scores. IDs are accepted in any case, with/without hyphens, with O/0 and I/L/1
mix-ups forgiven. Rate limited (60 requests / 15 min / IP). Certificates issued by the old system (16-character
code) still verify.

Instructors (`/api/certificates/signature`, teacher/admin)
- `PUT` multipart field `signature` (PNG or JPEG, ≤ 500 KB; a transparent PNG looks best) · `DELETE` to remove
- Without an uploaded image the instructor's name is printed in italic type as the signature.
- Signatures are stored in `storage/signatures/` (not publicly served), content-addressed and never overwritten, so
  already-issued certificates keep the signature they were issued with. New signature → affects future certificates.

Admin (`/api/admin`)
- `GET /certificates?status=&courseId=&certificateId=&page=` · `POST /certificates/:id/revoke {reason}` ·
  `POST /certificates/:id/restore`. Revoked certificates verify as invalid and can no longer be downloaded.

## 4. Setup

1. `npm install` (adds `qrcode`; without it certificates still work, just without the QR).
2. `.env`: `CERTIFICATE_INSTITUTION_NAME`, `CERTIFICATE_VERIFY_BASE_URL` (see below), optional
   `CERTIFICATE_SIGNATORY_NAME/TITLE/IMAGE` for a second (e.g. Principal) signature. Put that image in `storage/signatures/`.
3. **Verification URL**: printed on every certificate and encoded in the QR. Either point it at a page in your
   frontend (`https://your-site/verify`, which calls the API above) or at this API's built-in page
   (`https://api.your-site/verify`). It must work from the public internet, because it is printed on paper.
4. Existing platform? Run `npm run certificates:backfill` (dry run) then `-- --apply`. It upgrades old certificates
   (adds the new ID + snapshot; the old code keeps working) and issues certificates students already earned.
5. Delete old files in `uploads/certificates/`. The previous version wrote PDFs there and `/uploads` is public;
   that folder is now blocked, and new certificates are never written to disk.
6. `npm test`.

## 5. Behaviour changes from the old certificate code

- Old rule: lessons×60% + (any graded assignment)×15% + (any quiz)×12.5% + (any exam)×12.5% ≥ 80. That let a student
  finish with a **0% score** (one graded submission of each type was enough) and made certificates **impossible**
  for courses with no quizzes/exams (max 60%). Replaced by the explicit per-course rules above.
- Old trigger: only when a lesson was completed. Now also on grading and attendance.
- Old PDF: plain text page, no institution/instructor/signature, stored on disk under a public path.
- Old verify: returned the raw database record. Now a minimal, purpose-built response.

## 6. Limits worth knowing

- PDFs are not cryptographically signed (PAdES). Authenticity is established by looking the ID up, not by the file.
- `Institution` is referenced by `institutionId` in your models but no Institution model exists, so the institution
  name comes from `CERTIFICATE_INSTITUTION_NAME` for every course.
- Completion date = the moment the system confirmed the requirements were met (progress doesn't store per-lesson
  completion timestamps).
- Signature files live on the server's disk (like your other uploads); with several servers use shared storage.
- Changing a course's requirements affects future evaluations only; certificates already issued are not revoked.
- Layout was verified by rendering through an approximation of pdfkit (same coordinates and fonts, see
  `test/preview/`), not by the real pdfkit and not on a printer. Look at one real PDF before going live, and scan the
  QR code with a phone.
