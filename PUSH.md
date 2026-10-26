# Push notification architecture

```
 event (new message, grade, announcement, payment ...)
        |
 notificationService.createNotification()
        |-- stores the Notification in MongoDB
        |-- Socket.IO  'notification:new'      -> app open: instant, in-app bell
        |-- pushService.sendToUser()           -> app closed / phone locked
                 |-- Web Push (VAPID)  ----> browser push service ----> service worker 'push' event  (installed PWA, Chrome on Android, desktop)
                 `-- FCM (firebase-admin) ---> Google Play services ----> native app (Capacitor APK)
```

Subscriptions live in the `PushSubscription` collection (`kind: webpush | fcm`). Dead subscriptions (HTTP 404/410, unregistered FCM token) are deleted automatically. Payloads carry only a title, a short text and a URL, never sensitive content: tapping opens the app, which loads the details over the authenticated API.

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/push/public-key` | `{ enabled, publicKey }` (public; the VAPID public key is meant to be public) |
| POST | `/api/push/subscribe` | `{ endpoint, keys: { p256dh, auth }, kind }` for webpush, `{ endpoint: <fcmToken>, kind: 'fcm' }` for native |
| POST | `/api/push/unsubscribe` | `{ endpoint }` |

## Enable Web Push (PWA)

```bash
npx web-push generate-vapid-keys
# put the keys in backend/.env
VAPID_PUBLIC_KEY=...
VAPID_PRIVATE_KEY=...
VAPID_SUBJECT=mailto:admin@yourschool.org
```

Restart the API. In the web app: avatar menu > **Turn on notifications**. Requires HTTPS (or localhost). On iOS, push works only for PWAs added to the Home Screen (iOS 16.4+).

## Enable native push (Android APK)

1. Firebase console > create a project > add an Android app with your `appId` (`ng.gwia.academy`) > download `google-services.json` to `android/app/`.
2. Firebase console > Project settings > Service accounts > *Generate new private key*. Store the JSON **on the server only**, outside the repository.
3. Server: `npm --prefix backend i firebase-admin` and set `FCM_SERVICE_ACCOUNT_FILE=/secure/path/firebase-service-account.json`.
4. App: `npm run cap:sync` (the PushNotifications plugin is already a dependency). In the app: avatar menu > **Turn on notifications**.

`pushService.js` is written for firebase-admin's `messaging().send()`; it could not be exercised in the build sandbox, so send a test notification before relying on it.

## Where to extend

* Which events notify: `notificationService.createNotification(userId, type, title, message, data)`. Every existing caller (grades, announcements, payments ...) already benefits.
* Per-user preferences (mute by type, quiet hours): add fields to the User profile and check them at the top of `pushService.sendToUser`.
* Scale: with many instances, move sending to a queue (BullMQ) so a slow push service never delays an API request (sending is already fire-and-forget).
