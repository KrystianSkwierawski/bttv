import bttv.updater.*;
import android.app.*;
import android.app.job.*;
import android.os.*;
import java.util.*;
import tv.twitch.android.feature.viewer.main.navigation.PersistentBannerPresenter;

public class UpdaterDisabledTest {
    static class Jobs extends JobScheduler {
        Set<Integer> cancelled = new HashSet<>();
        public void cancel(int id) { cancelled.add(id); }
    }
    static class Notices extends NotificationManager {
        String deleted;
        public void deleteNotificationChannel(String id) { deleted = id; }
    }
    static class Screen extends Activity {
        Jobs jobs = new Jobs(); Notices notices = new Notices();
        public Object getSystemService(String s) {
            return s.equals(JOB_SCHEDULER_SERVICE) ? jobs : notices;
        }
    }
    static class Banner extends PersistentBannerPresenter {
        boolean visible = true;
        public void setShouldShowUpdateBanner(boolean value) { visible = value; }
    }
    static class OldInstaller extends UpdaterActivity {
        boolean finished;
        public void finish() { finished = true; }
        void open() { onCreate(new Bundle()); }
    }
    public static void main(String[] args) {
        Screen screen = new Screen(); Banner banner = new Banner();
        Updater.checkForUpdates(screen, banner);
        assert !banner.visible;
        assert screen.jobs.cancelled.equals(new HashSet<>(Arrays.asList(1873912, 1873913)));
        assert "bttv_android_updates".equals(screen.notices.deleted);
        final int[] calls = {0};
        Updater.UpdateCallbackListener callback = new Updater.UpdateCallbackListener() {
            public void onNoUpdate() { calls[0]++; }
            public void onUpdate(String a, String b, String c, String d) { throw new AssertionError(); }
            public void onError(Throwable t) { throw new AssertionError(); }
        };
        Updater.checkForUpdates(screen, callback, false);
        Updater.checkForUpdates(screen, callback, true);
        assert calls[0] == 2;
        Updater.manuallyCheckForUpdates(screen);
        OldInstaller installer = new OldInstaller(); installer.open();
        assert installer.finished;
        UpdaterJobService service = new UpdaterJobService();
        assert !service.onStartJob(new JobParameters());
        assert !service.onStopJob(new JobParameters());
        assert !UpdaterJobService.isJobScheduled(screen.jobs);
        Build.VERSION.SDK_INT = 25;
        Screen oldAndroid = new Screen(); UpdaterJobService.schedule(oldAndroid);
        assert oldAndroid.notices.deleted == null;
        assert oldAndroid.jobs.cancelled.size() == 2;
        System.out.println("PASS: banner hidden, both jobs cancelled, update channel removed, callbacks finish without updates, stale installer closes, pre-O guard");
    }
}
