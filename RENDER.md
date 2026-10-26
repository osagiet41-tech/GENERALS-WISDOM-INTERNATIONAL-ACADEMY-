# Deploy: GitHub + Render + MongoDB Atlas

## 1. MongoDB Atlas
1. Create a free/M10 cluster, then **Database Access** > add a user with a strong password (read/write on `gwia`).
2. **Network Access** > allow `0.0.0.0/0` (Render outbound IPs are not fixed; the password protects the DB), or use Render's static outbound IPs on paid plans.
3. **Connect > Drivers**: copy the string and add the DB name:
   `mongodb+srv://USER:PASSWORD@cluster0.xxxx.mongodb.net/gwia?retryWrites=true&w=majority`
   (URL-encode special characters in the password).

## 2. GitHub
```bash
cd gwia-platform
git init -b main
git add . && git status          # confirm no .env, uploads or node_modules are listed
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USER/gwia-platform.git
git push -u origin main
```
Use a **private** repo. Run `npm run install:all` first and commit the generated `package-lock.json` files.

## 3. Render
1. **New > Blueprint**, pick the repo. Render reads `render.yaml` and creates `gwia-api` (Docker web service + 10 GB disk) and `gwia-web` (static site).
2. Fill the prompted values. `JWT_SECRET` and `JWT_REFRESH_SECRET` are generated for you.
3. After both services exist, set:
   - `gwia-web` > `API_URL` = the `gwia-api` URL (e.g. `https://gwia-api.onrender.com`), then redeploy.
   - `gwia-api` > `CLIENT_URL` = the `gwia-web` URL (exact, no trailing slash), then redeploy.
   If you rename services, the URLs change accordingly.
4. In `gwia-api` > **Shell**: `node seed/admin.seed.js` and `node seed/plans.seed.js`.
5. Payment webhooks: set Paystack and Flutterwave webhook URLs to `https://<api-url>/api/webhooks/...` (see docs/PAYMENTS.md).
6. Verify: `https://<api-url>/api/health` returns OK; open the web URL, sign in, upload a file, restart the API and confirm the file is still there.

## Notes
- The disk is mounted at `/data`; the container entrypoint links uploads, backups and certificate signatures onto it, so nothing in the code changes.
- A disk means one instance only (no horizontal scaling); fine for Socket.IO since sessions stay on one server.
- Free tier sleeps after inactivity and has no disk, so use `starter` for production.
- Custom domain: add it on both services, then update `CLIENT_URL` and `API_URL`.
- Android app: build with `API_URL` pointing at the same API; `CORS_ORIGINS` already includes `https://localhost`.
