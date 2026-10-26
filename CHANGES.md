# What changed (files modified or added)

Only files that needed changes were touched; the payment, certificate, course, exam, messaging and AI business logic is unchanged.

**Backend, modified:** `server.js`, `package.json`, `.env.example`, `src/app.js`, `src/config/{env,multer}.js`, `src/middleware/{authMiddleware,rateLimiter.middleware}.js`,
`src/models/User.js`, `src/services/{authService,adminUserService,adminCourseService,backupService,certificateService,classroomAuthService,notificationService,paymentService,receiptService,studentLiveClassService}.js`,
`src/controllers/{adminUserController,liveClassController,questionBankController}.js`, `src/routes/{authRoutes,adminRoutes}.js`,
`src/validators/{authValidator,adminValidator,lessonValidator,liveClassValidator}.js`, `src/sockets/{index,messaging.socket,classroom.socket}.js`, `src/utils/excel.util.js`

**Backend, added:** `src/utils/{security,tokens,fileSignature,signedUrl}.js`, `src/middleware/sanitize.middleware.js`, `src/services/{fileAccessService,pushService}.js`,
`src/routes/{fileRoutes,pushRoutes}.js`, `src/models/pushSubscription.model.js`, `src/sockets/rateLimit.js`, `scripts/{route-inventory,run-tests}.js`, `test/unit/*`, `test/integration/*`

**Frontend, modified:** all `*.html` (PWA tags), `css/layout.css`, `js/ui/shell.js` (bottom nav, install/notification menu), `js/pages/{learn,messages}.js`, `js/pages/teacher/work.js`, `js/pages/admin/users.js`, `js/api/admin.js`
**Frontend, added:** `manifest.json`, `sw.js` (generated), `sw.template.js`, `offline.html`, `icons/*`, `js/pwa.js`, `js/core/files.js`

**Project level, added:** `README.md`, `package.json`, `capacitor.config.json`, `.gitignore`, `resources/*`, `tools/*`, `docs/*`
