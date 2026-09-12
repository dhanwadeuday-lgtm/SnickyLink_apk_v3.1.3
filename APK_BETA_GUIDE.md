# Getting a beta APK to ~100 testers (no paid subscription needed)

This is separate from the Cloudflare setup elsewhere in this repo.
Cloudflare Pages/Workers can only host the **Flutter web build** (a
website) -- it cannot produce an installable Android `.apk` file. For an
APK, use the path below instead.

## 1. Build the APK (free, no local Flutter install required)

A GitHub Actions workflow is included at
`.github/workflows/build-apk.yml`. It runs on GitHub's free runners:

1. Push this repo to GitHub (if not already).
2. (Optional, do this once you have a deployed backend) In the repo:
   **Settings -> Secrets and variables -> Actions -> Variables tab -> New
   repository variable**, name it `API_BASE_URL`, value = your backend's
   real URL (e.g. the Render URL for `snickylink-api`). Until you set this,
   the APK builds against a placeholder URL and the app UI will load fine,
   but API calls (login, etc.) will fail.
3. Go to the **Actions** tab -> **Build Android APK** -> **Run workflow**.
4. Wait for it to finish (a few minutes), then open the completed run and
   download the **snickylink-release-apk** artifact from the bottom of the
   page. Unzip it to get `app-release.apk`.

This APK is signed with Flutter's default debug-style signing (fine for
beta testing; not suitable for a Play Store production release).

## 2. Distribute it to ~100 testers (free -- Firebase App Distribution)

Firebase App Distribution is free (Spark plan) for up to 500 testers per
project -- no Play Console account, no $25 fee, no subscription:

1. Create a free project at https://console.firebase.google.com.
2. In the project, open **Release & Monitor -> App Distribution**, add an
   Android app (package name `com.snickylink.snickylink` if you used the
   default org from the workflow above, or whatever `--org` you chose).
3. Upload the `app-release.apk` you downloaded in step 1 directly through
   the Firebase console (drag-and-drop UI -- no CLI needed for a one-off
   upload).
4. Add your ~100 testers by email (or generate an invite link testers can
   self-register with) under **Testers & Groups**.
5. Each tester gets an email with a link; opening it on their Android phone
   lets them install the APK directly (they'll need to allow "install
   unknown apps" for the Firebase App Distribution app once).

For repeat releases as you iterate, you can later automate step 3 with the
Firebase CLI or a GitHub Action (`wzieba/Firebase-Distribution-Github-Action`),
but manual upload is perfectly fine to get started.

## Why not Google Play Console for this?

Play Console costs a one-time $25 (~₹2,100+), which is over your ₹1,000
budget, and now also requires a 12-tester closed-testing period before you
can go to production -- unnecessary overhead for a 100-person beta. Save
that step for when you're ready for a public launch.
