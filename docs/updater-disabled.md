# Updater removed from local builds

Version 0.43.4-beta disables the upstream BTTV updater. Previously it compared
release tags for inequality, so upstream 0.43.2-beta was offered even when a
newer local version was installed.

The updater no longer requests release metadata, shows update banners, downloads
APKs or opens the package installer. Update settings are hidden. Compatibility
entry points remain so the existing Twitch hooks and old notification intents
are safe: the old installer activity immediately finishes, job callbacks return
without scheduling retries, and startup cancels job IDs 1873912 and 1873913.
On Android 8+ startup also deletes only the BTTV update notification channel.
Other notification channels are untouched. Existing pre-Android-8 notices may
need manual dismissal, but their installer destination no longer downloads.

The updater implementation was compiled from the changed Java sources for the
local APK; minimal API stubs were used only on the compile classpath, not packaged.
VOD patches and emote implementation are preserved. The build uses the same
local debug signing identity as 0.43.3-beta; it is not an upstream-signed release.

Regression check (JDK 17 or later):

```sh
python tests/check_updater_disabled.py PATH_TO_JDK
```

This compiles production updater classes and tests cancellation, channel cleanup,
banner suppression, manual/background callbacks, old installer intents and the
pre-Android-8 guard with mocked Android boundaries. It does not replace a device
upgrade/startup smoke test. App updates must now be installed manually.
