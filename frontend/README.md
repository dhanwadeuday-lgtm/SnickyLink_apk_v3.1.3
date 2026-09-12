# SnickyLink — Cross-platform Mobile App

This is the Flutter mobile client for SnickyLink. The same codebase targets **Android and iOS**.

## Build

Install Flutter 3.x, Android Studio/SDK for Android builds, and Xcode + CocoaPods on macOS for iOS builds.

```bash
flutter pub get
flutter run
flutter build apk --release
flutter build appbundle --release
flutter build ipa --release
```

Set the production API URL in `lib/core/network/api_client.dart` (or replace it with a compile-time environment configuration before release).

### iOS
Run `flutter create .` once if native platform folders have not been generated on your machine, then open `ios/Runner.xcworkspace` in Xcode, configure your Apple Developer Team and Bundle Identifier, enable Push Notifications/APNs as needed, and archive the Runner target.

### Android
Open the project in Android Studio or run the Flutter build commands above. Configure your application ID, signing key, Firebase/FCM credentials, and release keystore before publishing.

## Backend
The sibling `../backend` directory is the FastAPI service. Deploy it first and point the mobile API client at its HTTPS URL.

## Cloudflare Web Deployment

This is a Flutter app. Cloudflare must deploy the generated web output, not the Dart source directory. From the repository root use `npm run cf:build` and deploy `frontend/build/web`, or follow `deploy/DEPLOY_CLOUDFLARE.md`.
