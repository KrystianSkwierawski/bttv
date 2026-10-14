package bttv.updater;

import android.app.NotificationManager;
import android.app.job.JobParameters;
import android.app.job.JobScheduler;
import android.app.job.JobService;
import android.content.Context;
import android.os.Build;

/** Kept registered so jobs from an earlier installation can terminate safely. */
public class UpdaterJobService extends JobService implements Updater.UpdateCallbackListener {
    static final int JOB_ID = 1873913;

    /** Called at startup by Data: cancel old jobs instead of scheduling updates. */
    public static void schedule(Context context) {
        JobScheduler scheduler = (JobScheduler) context.getSystemService(Context.JOB_SCHEDULER_SERVICE);
        if (scheduler != null) {
            cancelOld(scheduler);
            scheduler.cancel(JOB_ID);
        }
        if (Build.VERSION.SDK_INT >= 26) {
            NotificationManager notifications = (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
            if (notifications != null) {
                notifications.deleteNotificationChannel("bttv_android_updates");
            }
        }
    }

    public static void cancelOld(JobScheduler scheduler) {
        scheduler.cancel(1873912);
    }

    public static boolean isJobScheduled(JobScheduler scheduler) {
        return false;
    }

    @Override public boolean onStartJob(JobParameters params) {
        schedule(this);
        return false;
    }
    @Override public boolean onStopJob(JobParameters params) { return false; }
    @Override public void onNoUpdate() { }
    @Override public void onError(Throwable error) { }
    @Override public void onUpdate(String version, String body, String url, String htmlUrl) { }
}
