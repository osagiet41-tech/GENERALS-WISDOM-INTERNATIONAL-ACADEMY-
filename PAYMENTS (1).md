# Subscriptions & Payments

Paystack + Flutterwave, MongoDB, server-verified. Nothing the browser sends can mark a payment as paid.

## 1. How a payment flows

```
Student UI                    Your API                              Gateway
   | POST /api/billing/checkout   |                                     |
   |  {purpose, courseId|planCode,|  server computes the price          |
   |   currency?, discountCode?}  |  (no amount is ever accepted)       |
   |----------------------------->|  Payment(status=pending, reference) |
   |                              |  initialize(reference, amount) ---->|
   |<-- {checkoutUrl, reference} -|<------------- checkout url ---------|
   | redirect to checkoutUrl ------------------------------------------>|
   |                              |<--- webhook (signed) ---------------|  (A)
   |                              |  verify signature, de-dupe event    |
   |                              |  GET verify(reference) ------------>|  server-to-server
   |                              |<-- status, amount, currency --------|
   |                              |  amount+currency == our record?     |
   |                              |  claim pending->completed (atomic)  |
   |                              |  grant access, receipt, email       |
   | browser returns to /payment/callback?reference=...                 |
   | POST /api/billing/payments/:reference/verify ---------------------->|  (B) same verify path
   |<-- {paid, accessGranted} ----|                                     |
   (C) background job re-verifies pending payments if A and B never happened
```
A, B and C all call the same `paymentService.confirmPayment()`. It is safe for all three to fire for one payment.

**Frontend callback page** (`PAYMENT_CALLBACK_PATH`, default `/payment/callback`): read `reference` (Paystack also adds `trxref`, Flutterwave adds `tx_ref`), call `POST /api/billing/payments/:reference/verify`, and show the result. Ignore `status=successful` in the URL: it proves nothing. If `paid` is true but `accessGranted` is false, retry the call after a couple of seconds.

## 2. Why it can't be cheated or double-processed

| Threat | Defence |
|---|---|
| Browser claims "paid" | No endpoint accepts a status. Success only comes from `provider.verify()` (server → gateway API with your secret key). |
| Forged webhook | Paystack: HMAC-SHA512 of the **raw** body (`x-paystack-signature`). Flutterwave: `verif-hash` header equals your secret hash. Constant-time compare. Even a valid webhook is only a trigger; the API call decides. |
| Client changes the price | Request has no amount field. Price comes from `Course.price/prices` or `Plan.prices`, discount recomputed server-side. |
| Pay ₦100, claim a ₦5,000 item | Gateway-reported `amountMinor` and `currency` must equal what we recorded, else the payment is marked failed + `needsReview`. |
| Replaying someone else's successful transaction id | Flutterwave: response `tx_ref` must equal our reference. Paystack: lookup is by our reference. Plus unique index on `{provider, providerReference}`. |
| Same webhook delivered 5 times | `WebhookEvent` unique `{provider, eventKey}`. |
| Webhook + browser verify + job racing | Atomic claim `findOneAndUpdate({status in [pending, failed]}) -> completed`: one winner. Fulfilment has its own lock, and every grant is idempotent per payment id (unique `CourseAccess.paymentId`, `Subscription.paymentIds` compare-and-swap). |
| Crash after "completed" but before access granted | `fulfillment.status` stays `pending`; the job retries every 5 min. |
| Two buyers, last discount slot | Atomic `$expr` increment on `redeemedCount`. Reservations are released if the payment fails/abandons. |
| Double-click on "Pay" | A recent identical pending checkout (same user, target, amount, code, provider) is reused. |
| Admin accidentally marks a card payment paid | Blocked for gateway payments: use **Verify**. Manual "mark received" only exists for offline payments. |

## 3. Access rules (automatic restriction)

`accessService.getCourseAccess(user, course)`:
1. Free course (price 0 and no priced currency overrides) → allowed.
2. Active `CourseAccess` (purchase / admin grant / grandfathered) → allowed.
3. Live subscription or trial (`status active|trialing` **and** `endDate > now`) and `course.includedInSubscription !== false` → allowed.
4. Otherwise `402` with `details.code` = `PAYMENT_REQUIRED` or `SUBSCRIPTION_EXPIRED`.

It is enforced in `verifyEnrollment` / `verifyResourceAccess` (all student lesson, quiz, exam, assignment, live-class, module, progress routes) and in enrollment. Because it checks `endDate`, access stops at the exact expiry moment; the job only updates labels and sends notifications. Expired students stay enrolled with their progress and regain access the moment they renew.

Set `PAYMENTS_ENFORCE_ACCESS=false` to switch gating off (checkout still works) for a staged rollout.

## 4. API

Student (`Authorization: Bearer`), base `/api/billing`
- `GET /plans` (public) plans, prices per currency, enabled providers
- `GET /courses/:courseId/access` access status + purchase options (for paywalls)
- `POST /discounts/validate` `{code, purpose, courseId|planCode, currency?}` preview only
- `POST /checkout` `{purpose: "course"|"subscription", courseId|planCode, currency?, provider?, discountCode?}` → `{reference, checkoutUrl}`; if the total is 0 (100% code) access is granted immediately and `free: true`
- `POST /payments/:reference/verify` `{transactionId?}` (hint only)
- `GET /payments`, `GET /payments/:id` history
- `GET /payments/:id/receipt` JSON, `GET /payments/:id/receipt.pdf`
- `GET /subscription` current subscription + trial eligibility
- `POST /trial` `{planCode}`

Webhooks (configure in each gateway dashboard)
- `POST /api/webhooks/paystack`
- `POST /api/webhooks/flutterwave`

Admin (`/api/admin`): `GET/POST/PUT /plans`, `GET/POST/PUT /discount-codes`, `POST /payments/:id/verify`, `GET /payments/:id/receipt.pdf`, plus the existing payments/subscriptions endpoints (now with provider/purpose/needsReview filters).

## 5. Data (MongoDB)

`Payment`, `Subscription` (extended, backward compatible), `Plan`, `DiscountCode`, `DiscountRedemption`, `CourseAccess`, `WebhookEvent` (180-day TTL), `Counter` (receipt numbers `RCT-YYYYMM-000001`). Money is stored as integer minor units (`amountMinor`); `amount` (major units) is kept for your existing dashboards.

Unique indexes are created at boot by `ensureBillingIndexes()` (production runs with `autoIndex` off). The server refuses to start if the Payment/Webhook/Access indexes can't be built.

## 6. Setup

1. `.env`: add the Payments block from `.env.example`.
2. Gateway dashboards:
   - **Paystack** Settings → API & Webhooks: webhook URL `https://YOUR-API/api/webhooks/paystack`. Uses your secret key for signing; no extra secret.
   - **Flutterwave** Settings → Webhooks: URL `https://YOUR-API/api/webhooks/flutterwave`, set a **Secret hash**, put the same value in `FLUTTERWAVE_SECRET_HASH`.
3. `npm run seed:plans` (monthly + annual starter plans; edit prices in the dashboard afterwards).
4. **Existing platform?** Run `npm run billing:grandfather` (dry run) then `-- --apply` **before** enabling enforcement, so students already enrolled in priced courses aren't locked out.
5. Set course prices: `price` (+ `currency`, optional `prices: [{currency, amount}]` for international buyers, `includedInSubscription`).
6. `npm test` (unit tests: money, signatures, discount math, provider adapters).

## 7. Go-live checklist (do these in the gateways' TEST mode first)

- [ ] Paystack test card: pay → webhook arrives → payment `completed`, access granted, receipt emailed.
- [ ] Same with Flutterwave test card.
- [ ] Close the browser right after paying: access still arrives (webhook / job).
- [ ] Kill your server during a payment, restart: pending payment settles via the job.
- [ ] Replay the same webhook (re-send from gateway dashboard): nothing changes (`outcome: duplicate`).
- [ ] Send a webhook with a wrong signature: `401`.
- [ ] Let a monthly subscription pass its `endDate` (edit it in Mongo): lessons return `402 SUBSCRIPTION_EXPIRED` immediately.
- [ ] Use a discount code at its `maxRedemptions` limit from two accounts at once.
- [ ] Reverse proxy passes the raw body unchanged to `/api/webhooks/*` (no body re-encoding), and your API is HTTPS.
- [ ] Rotate to live keys; confirm `FLUTTERWAVE_SECRET_HASH` is a long random value.

## 8. Known limits / next steps

- **No automatic recurring charge.** Each month/year is a prepaid period the student pays for again; renewals stack on remaining time. Card-on-file auto-renew (Paystack `charge_authorization`, Flutterwave tokenised charge) fits as a new job calling the same adapters.
- **No provider-initiated refunds.** "Record refund" marks the payment refunded and revokes access; send the money back in the gateway dashboard. A `refund.processed` Paystack webhook is handled the same way.
- **No currency conversion.** A course/plan is sold only in currencies you price explicitly.
- Dashboard "revenue" cards sum `amount` across currencies (existing behaviour); with NGN and USD both in use, report per currency.
- Forum and messaging access are not gated by payment (lesson/quiz/exam/assignment/live-class content is).
- Trials need a verified email; stopping multi-account trial abuse needs more (e.g. card-on-file).
- Flutterwave: built for API **v3** (secret-key bearer). If your account is on Flutterwave v4 (OAuth), only `flutterwave.provider.js` changes.
