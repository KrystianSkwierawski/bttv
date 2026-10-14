# VOD timeline investigation (Twitch 19.0.1 / BTTV 0.43.2-beta)

Status: experimental backend workaround; device playback validation is pending.
This is not a confirmed root-cause fix.

## Evidence

The reported symptom is that the VOD counter/chat runs ahead of the audiovisual
content, while audio remains synchronized with video. Seeking back to the same
displayed time produces different content. Reference VOD: 2896096040.

Inspection of the supplied APK shows:

- `VodPlayerPresenter.startVideoTimeFlowable` polls `getCurrentPositionInMs`
  every 500 ms. It does not advance a separate wall-clock counter.
- `VodPresenter` converts that position from milliseconds to seconds for replay
  chat. The counter and chat therefore depend on the player's reported position.
- The Core backend ultimately reads position through the native IVS
  `CorePlayerImpl.getPosition`. Java inspection alone cannot establish why that
  position would diverge from content on the reporting device.
- The APK already contains `TwitchExoPlayer2`, which uses ExoPlayer's position and
  seek methods. `PlayerConfiguration` supports selecting this backend.

## Change

The patch in `patches/vod-sync` sets `forceExoPlayer=true` only when constructing
`VodPlayerPresenter`. The Kotlin default-argument mask must also be cleared;
otherwise Kotlin overwrites the flag with `false`.

This changes the playback backend rather than introducing an arbitrary chat/time
offset. Live and clip presenter configurations are untouched. DRM content still
uses Core because the existing DRM check takes precedence over the flag.
Player pooling checks the requested backend before reusing a player.

The normal repository `patch` script includes this patch automatically. For an
already modified BTTV APK, apply only the new patch, not all existing patches.
Do not commit extracted application code, downloaded tools, signing keys or APKs.

## Required device validation

Local verification completed on 2026-10-11:

- Patch application and reverse-application checks passed against the supplied APK.
- Apktool 2.11.1 assembled the patched application successfully.
- Inspection of the assembled DEX confirmed `forceExoPlayer=true`, default mask
  `0`, and a null marker at the VOD configuration call.
- The test APK passed zip alignment and v1/v2/v3 signature verification.
- Manifest, resources, assets and native libraries match the input APK byte for
  byte. Signing metadata, including the old source stamp, was excluded from this
  comparison because the test APK is signed with a different key.
- No Android device/emulator playback test was performed. The reported drift
  has not been reproduced locally or confirmed resolved.

Compare the original APK and the test APK on the same device and VOD:

1. Play for at least as long as it normally takes for the drift to appear. Record
   a distinctive audiovisual event and its displayed VOD time, then seek back to
   that time and compare the event and replay chat.
2. Seek backwards and forwards repeatedly, including while paused. Check the
   settled position after buffering, not the seek preview during a drag.
3. Pause/resume, change quality, use 0.5x/1x/2x, and switch between background
   audio and video. Check picture, audio, counter and chat after each transition.
4. Check resume watching, picture-in-picture, and one live stream. Protected VODs
   retain Core and are outside this workaround.

With Android platform tools and a connected device, capture player diagnostics:

```sh
adb logcat -v threadtime > vod-sync-log.txt
```

The existing logs include `Creating Exo2 player` and `EXO2` events; use them to
verify the active backend. Logs can include account/network data; redact before
sharing. A static build/signature check does not replace these playback checks.

A locally signed test APK cannot update an installation signed by the upstream
BTTV release key. Prefer a spare device or Android profile for testing; removing
an existing installation can remove its local settings and login state.
