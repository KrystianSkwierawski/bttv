package bttv.updater;

import android.os.Bundle;
import androidx.appcompat.app.AppCompatActivity;

/** Old notification intents must never download or launch an APK installer. */
public class UpdaterActivity extends AppCompatActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        finish();
    }
}
