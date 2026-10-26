# Android app (APK) with Capacitor

The Android app is the same web app (`frontend/`) wrapped in a native WebView by [Capacitor](https://capacitorjs.com), so there is one code base.
**What was and was not verified:** the Capacitor configuration, icons, splash sources and Android patch script are in the repository. The sandbox that produced this
project has no network, so `npx cap add android` and the Gradle build were **not** run here; the commands below are the standard Capacitor 6 flow, run them on your machine.

## 0. Prerequisites (your computer)

| Tool | Version | Notes |
|---|---|---|
| Node.js | 18 or newer | https://nodejs.org |
| JDK | 17 | Android Gradle Plugin 8 needs 17 (`java -version`) |
| Android Studio | current | installs the Android SDK; open it once and accept licences. Set `ANDROID_HOME` (e.g. `~/Android/Sdk`) |
| A deployed HTTPS backend | | The app talks to your API over the internet, see step 1 |

## 1. Point the app at your production API

Edit `frontend/config.js`:

```js
window.APP_CONFIG = {
  apiBase: 'https://api.yourschool.org/api',      // MUST be an absolute https URL in the APK
  socketUrl: 'https://api.yourschool.org',
  ...
};
```

On the server (`backend/.env`):

```
CORS_ORIGINS=https://localhost          # the origin of the Capacitor Android WebView (androidScheme: https)
CLIENT_URL=https://app.yourschool.org   # your website, used in e-mail links and as the payment return page
```

## 2. Install and add the Android project

```bash
npm install                  # from the project root (installs Capacitor)
npm run build                # regenerates the service worker for the current files
npm run cap:assets           # generates all Android icons + splash screens from resources/*.png
npm run cap:add              # = npx cap add android + patches AndroidManifest.xml
```

`tools/android-setup.js` (run by `cap:add` and `cap:sync`) adds the permissions the app needs
(INTERNET, CAMERA, RECORD_AUDIO, MODIFY_AUDIO_SETTINGS, POST_NOTIFICATIONS, VIBRATE, camera and microphone declared optional),
turns cleartext HTTP off and disables Android backups of app data.

Change the app id (`ng.gwia.academy`) and name in `capacitor.config.json` **before** the first `cap add`. The id can never change after publishing on Google Play.

## 3. Build

```bash
# Debug APK (for testing on your phone; installable directly)
npm run apk:debug
# -> android/app/build/outputs/apk/debug/app-debug.apk

# Open in Android Studio (run on emulator/device, inspect logs)
npm run cap:open
```

Install the debug APK: enable *Install unknown apps* on the phone, copy the file over, open it. Or `adb install android/app/build/outputs/apk/debug/app-debug.apk`.

## 4. Signed release APK / App Bundle

Create a keystore **once** and back it up safely. If you lose it you cannot update your app on Google Play.

```bash
keytool -genkey -v -keystore gwia-release.jks -alias gwia -keyalg RSA -keysize 2048 -validity 10000
```

Create `android/keystore.properties` (never commit it, it is git-ignored below):

```
storeFile=../../gwia-release.jks
storePassword=YOUR_STORE_PASSWORD
keyAlias=gwia
keyPassword=YOUR_KEY_PASSWORD
```

Add to `android/app/build.gradle` (inside `android { ... }`, adjust to your generated file):

```groovy
def keystoreProps = new Properties()
def keystoreFile = rootProject.file("keystore.properties")
if (keystoreFile.exists()) { keystoreProps.load(new FileInputStream(keystoreFile)) }

signingConfigs {
    release {
        if (keystoreFile.exists()) {
            storeFile file(keystoreProps['storeFile'])
            storePassword keystoreProps['storePassword']
            keyAlias keystoreProps['keyAlias']
            keyPassword keystoreProps['keyPassword']
        }
    }
}
buildTypes {
    release {
        signingConfig signingConfigs.release
        minifyEnabled true
        shrinkResources true
        proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
    }
}
```

```bash
npm run apk:release     # android/app/build/outputs/apk/release/app-release.apk   (side-loading, WhatsApp, your website)
npm run aab:release     # android/app/build/outputs/bundle/release/app-release.aab (upload to Google Play)
```

Add `android/keystore.properties`, `*.jks` and `*.keystore` to `.gitignore` (already included in this repository's `.gitignore`).

## 5. Updating the app

Changes to HTML/CSS/JS: `npm run cap:sync` then rebuild. Because the web files are bundled in the APK, users get web changes only when they update the app; if you prefer instant updates, host the frontend and set `server.url` in `capacitor.config.json` (the APK then loads your site; keep `androidScheme: https` and CORS as above).
Bump `versionCode` / `versionName` in `android/app/build.gradle` for every Play Store upload.

## 6. Android-specific behaviour and limits

* **Low-end phones.** No framework runtime, ES modules loaded on demand, service-worker cache of the shell, signed media streamed (not downloaded), live classes use peer-to-peer mesh (best for up to ~10 video participants; on a weak phone students can join with camera off).
* **Slow networks.** Pages open from cache first, API calls have clear offline/error states, uploads are limited per type, JSON responses are gzip-compressed by the server.
* **Live classroom** needs camera/microphone permission (prompted on first use) and a TURN server for students behind strict mobile carriers (`iceServers` in `frontend/config.js`).
* **Payments** open the gateway's page. After paying, the server confirms through the gateway webhook, so access is granted even if the user never returns to the app; the return page opens on your website (`CLIENT_URL`). A deep link back into the app is not configured.
* **Push notifications** in the APK use Firebase (FCM), not the browser push API, see [PUSH.md](PUSH.md). Without it the app still shows in-app notifications in real time.
* **Debugging**: `chrome://inspect` lists the running WebView; `webContentsDebuggingEnabled` is off in `capacitor.config.json` for release.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Login works in browser but the app shows "Cannot reach the server" | `apiBase` is `http://localhost...` or HTTP; use the public **https** API URL |
| Network error only inside the app, CORS in the server log | `CORS_ORIGINS=https://localhost` missing |
| `SDK location not found` | Set `ANDROID_HOME` or create `android/local.properties` with `sdk.dir=...` |
| `Unsupported class file major version` | Wrong JDK; use 17 |
| Blank white screen | Run `npm run cap:sync`; check `chrome://inspect` console |
| Camera/mic denied in live class | Android Settings > Apps > GWIA > Permissions |
