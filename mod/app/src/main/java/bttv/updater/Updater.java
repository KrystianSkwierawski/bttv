package bttv.updater;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import tv.twitch.android.feature.viewer.main.navigation.PersistentBannerPresenter;

/** Compatibility entry points. This build is updated only by installing an APK manually. */
public class Updater {
    public static void manuallyCheckForUpdates(Activity activity) {
        UpdaterJobService.schedule(activity);
    }

    public static void checkForUpdates(Activity activity, PersistentBannerPresenter presenter) {
        UpdaterJobService.schedule(activity);
        presenter.setShouldShowUpdateBanner(false);
    }

    public static void checkForUpdates(Context context, UpdateCallbackListener listener, boolean manual) {
        UpdaterJobService.schedule(context);
        listener.onNoUpdate();
    }

    public static Intent updateActivityIndent(Context context, String version, String body, String url) {
        return new Intent(context, UpdaterActivity.class);
    }

    public interface UpdateCallbackListener {
        void onNoUpdate();
        void onUpdate(String version, String body, String url, String htmlUrl);
        void onError(Throwable error);
    }
}
