"""Compile the production updater against minimal Android stubs and test disabled behavior.
Usage: python tests/check_updater_disabled.py PATH_TO_JDK
The stubs model API boundaries, not Android runtime or installation behavior.
"""
from pathlib import Path
import subprocess
import sys
import tempfile

stubs = {
'android/content/Context.java': '''package android.content; public class Context { public static final String JOB_SCHEDULER_SERVICE="jobscheduler", NOTIFICATION_SERVICE="notification"; public Object getSystemService(String s){return null;} }''',
'android/content/Intent.java': '''package android.content; public class Intent { public Intent(Context c, Class<?> t){} }''',
'android/app/Activity.java': '''package android.app; public class Activity extends android.content.Context { public void finish(){} }''',
'android/os/Bundle.java': '''package android.os; public class Bundle {}''',
'android/os/Build.java': '''package android.os; public class Build { public static class VERSION { public static int SDK_INT=30; } }''',
'android/app/NotificationManager.java': '''package android.app; public class NotificationManager { public void deleteNotificationChannel(String s){} }''',
'android/app/job/JobScheduler.java': '''package android.app.job; public class JobScheduler { public void cancel(int id){} }''',
'android/app/job/JobParameters.java': '''package android.app.job; public class JobParameters {}''',
'android/app/job/JobService.java': '''package android.app.job; public abstract class JobService extends android.content.Context { public abstract boolean onStartJob(JobParameters p); public abstract boolean onStopJob(JobParameters p); }''',
'androidx/appcompat/app/AppCompatActivity.java': '''package androidx.appcompat.app; public class AppCompatActivity extends android.app.Activity { protected void onCreate(android.os.Bundle b){} }''',
'tv/twitch/android/feature/viewer/main/navigation/PersistentBannerPresenter.java': '''package tv.twitch.android.feature.viewer.main.navigation; public class PersistentBannerPresenter { public void setShouldShowUpdateBanner(boolean b){} }''',
}

repo = Path(__file__).resolve().parent.parent
jdk = Path(sys.argv[1]) / "bin"
scratch = repo / ".tmp"
scratch.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix="bttv-updater-test-", dir=scratch) as temp:
    root = Path(temp)
    sources = []
    for name, text in stubs.items():
        p = root / "stubs" / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        sources.append(str(p))
    classes = root / "classes"
    classes.mkdir()
    sources += [str(repo / "mod/app/src/main/java/bttv/updater" / (name + ".java"))
                for name in ("Updater", "UpdaterActivity", "UpdaterJobService")]
    sources.append(str(repo / "tests/updater/UpdaterDisabledTest.java"))
    subprocess.run([str(jdk / "javac"), "--release", "8", "-d", str(classes), *sources], check=True)
    subprocess.run([str(jdk / "java"), "-ea", "-cp", str(classes), "UpdaterDisabledTest"], check=True)
