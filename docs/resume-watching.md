# Resume watching: VOD cache offset

Related report: https://github.com/bttv-android/bttv/issues/631

The report describes intermittent starts at zero from Continue Watching or a
channel's VOD list. It does not provide the saved position or a reproduction
trace. The following is a verified defect in the supplied BTTV 0.43.2-beta APK
(Twitch 19.0.1), not proof that every instance of that report has this cause.

`VodPlayerPresenter` caches VOD progress in seconds. However,
`ResumeWatchingFetcher.getLastWatchedPositionInSecondsForVod` subtracts
`LIVE_STREAM_WATCHED_POS_OFFSET_SECONDS` (30) from every cached position before
clamping to zero. Thus a VOD cached at 15 seconds resumes at zero, and one cached
at 3600 resumes at 3570. Reopening without advancing can subtract time again.

The patch moves the subtraction to `putLastWatchedPositionForVideo`, and only
applies it to the local cache when its live flag is true. Direct VOD progress
updates and VOD writes retain the exact position. The original position is still
sent to the API. Reads retain their zero clamp and server-history fallback.
Explicit starting offsets and the absence of cached/server history are unchanged.
No maximum-of-history rule is introduced, so intentional rewinds remain valid.

## Verification

`tests/check_resume_watching.py` executes the relevant actual smali methods with
a small instruction runner and mocked external boundaries. It tests VOD positions
0/1/15/29/30/31/300/3600/86400, live offsets, unchanged API payloads, rewinds,
server fallback, missing history, signed-out and invalid-ID guards.

```sh
python tests/check_resume_watching.py .tmp/vod-smali/smali_classes8/tv/twitch/android/shared/viewer/network/resumewatching/ResumeWatchingFetcher.smali
```

The original method fails the regression at cached position 1 (returns 0).
The patched methods pass. Apktool assembly, zip alignment and v1/v2/v3 signing
verification also pass. These checks do not execute Android UI, networking or
the player; an authenticated device test is still required, particularly for
position loss after app restart or network failure. This patch does not introduce
durable local history or change asynchronous server-save behavior.

The combined test APK is
`dist/vod-resume/bttv-vod-resume-aligned-debugSigned.apk`. It also includes the
earlier experimental ExoPlayer VOD workaround documented in `vod-sync.md`.
Emote/chat implementation is unchanged. The new patch is independent of that
workaround and works with either backend.

Test on device by watching a VOD to 15 seconds and reopening it, then repeat at a
longer position and after deliberately seeking backwards. Check both Continue
Watching and channel entry points, then test after restarting the app. Record
any remaining reset separately; it may involve persistence rather than this
offset defect.

The test APK uses the same local debug signing identity as the earlier test APK,
but cannot update an upstream-signed BTTV installation. Do not remove the existing
app without accounting for loss of local settings and login state.
