# SnickyLink Android + iOS build notes

The `frontend` directory is a single Flutter application source tree intended for both Android and iOS.

The environment used to assemble this ZIP does not include the Flutter SDK, so native `android/` and `ios/` generated folders and signed binaries are intentionally not fabricated. On a Flutter-enabled machine, run:

```bash
cd frontend
flutter create --org com.snickylink .
flutter pub get
flutter build apk --release
flutter build appbundle --release
# macOS only:
flutter build ipa --release
```

Then configure Apple/Google signing, bundle/application identifiers, APNs/FCM, privacy manifests, and store metadata.
