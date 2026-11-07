from pathlib import Path
import re

base = Path("android/app/src/main/java/com/kvkhub/voice")
base.mkdir(parents=True, exist_ok=True)

plugin = r'''package com.kvkhub.voice;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Build;
import androidx.core.content.ContextCompat;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.annotation.Permission;
import com.getcapacitor.annotation.PermissionCallback;

@CapacitorPlugin(name = "KvkCall", permissions = {
    @Permission(alias = "notifications", strings = { Manifest.permission.POST_NOTIFICATIONS })
})
public class KvkCallPlugin extends Plugin {
    private static volatile KvkCallPlugin instance;

    @Override
    public void load() {
        instance = this;
    }

    @Override
    protected void handleOnDestroy() {
        if (instance == this) instance = null;
        super.handleOnDestroy();
    }

    @PluginMethod
    public void requestNotificationPermission(PluginCall call) {
        if (Build.VERSION.SDK_INT < 33 ||
            getPermissionState("notifications") == com.getcapacitor.PermissionState.GRANTED) {
            JSObject result = new JSObject();
            result.put("granted", true);
            call.resolve(result);
            return;
        }
        requestPermissionForAlias("notifications", call, "notificationPermissionCallback");
    }

    @PermissionCallback
    private void notificationPermissionCallback(PluginCall call) {
        JSObject result = new JSObject();
        result.put("granted", getPermissionState("notifications") ==
            com.getcapacitor.PermissionState.GRANTED);
        call.resolve(result);
    }

    @PluginMethod
    public void start(PluginCall call) {
        String roomName = call.getString("roomName", "Voice Room");
        boolean micEnabled = call.getBoolean("micEnabled", false);
        Intent intent = new Intent(getContext(), KvkVoiceService.class);
        intent.setAction(KvkVoiceService.ACTION_START);
        intent.putExtra("roomName", roomName);
        intent.putExtra("micEnabled", micEnabled);
        ContextCompat.startForegroundService(getContext(), intent);
        call.resolve();
    }

    @PluginMethod
    public void update(PluginCall call) {
        Intent intent = new Intent(getContext(), KvkVoiceService.class);
        intent.setAction(KvkVoiceService.ACTION_UPDATE);
        intent.putExtra("roomName", call.getString("roomName", "Voice Room"));
        intent.putExtra("micEnabled", call.getBoolean("micEnabled", false));
        getContext().startService(intent);
        call.resolve();
    }

    @PluginMethod
    public void stop(PluginCall call) {
        getContext().stopService(new Intent(getContext(), KvkVoiceService.class));
        call.resolve();
    }

    @Override
    public void handleOnNewIntent(Intent intent) {
        super.handleOnNewIntent(intent);
        handleNotificationIntent(intent);
    }

    static void handleNotificationIntent(Intent intent) {
        if (intent == null) return;
        String action = intent.getStringExtra("kvkNotificationAction");
        if ("com.kvkhub.voice.action.MUTE".equals(action)) {
            dispatchNotificationAction("MUTE");
            intent.removeExtra("kvkNotificationAction");
        } else if ("com.kvkhub.voice.action.UNMUTE".equals(action)) {
            dispatchNotificationAction("UNMUTE");
            intent.removeExtra("kvkNotificationAction");
        }
    }

    static void dispatchNotificationAction(String action) {
        KvkCallPlugin plugin = instance;
        if (plugin == null) return;
        JSObject data = new JSObject();
        data.put("action", action);
        plugin.notifyListeners("notificationAction", data, true);
    }
}
'''

service = r'''package com.kvkhub.voice;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.content.pm.ServiceInfo;
import android.os.Build;
import android.os.IBinder;
import androidx.core.app.NotificationCompat;
import androidx.core.app.ServiceCompat;

public class KvkVoiceService extends Service {
    static final String ACTION_START = "com.kvkhub.voice.action.START";
    static final String ACTION_UPDATE = "com.kvkhub.voice.action.UPDATE";
    static final String ACTION_TOGGLE_MIC = "com.kvkhub.voice.action.TOGGLE_MIC";
    static final String ACTION_MUTE = "com.kvkhub.voice.action.MUTE";
    static final String ACTION_UNMUTE = "com.kvkhub.voice.action.UNMUTE";
    static final String ACTION_DISCONNECT = "com.kvkhub.voice.action.DISCONNECT";
    private static final String CHANNEL_ID = "kvk_voice_session";
    private static final int NOTIFICATION_ID = 7401;
    private String roomName = "Voice Room";
    private boolean micEnabled = false;

    @Override
    public void onCreate() {
        super.onCreate();
        NotificationManager manager = getSystemService(NotificationManager.class);
        if (manager != null && Build.VERSION.SDK_INT >= 26) {
            NotificationChannel channel = new NotificationChannel(
                CHANNEL_ID, "KVK HUB voice session", NotificationManager.IMPORTANCE_LOW);
            channel.setDescription("Keeps your KVK HUB voice room connected");
            channel.setShowBadge(false);
            manager.createNotificationChannel(channel);
        }
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null) {
            String action = intent.getAction();
            if (ACTION_TOGGLE_MIC.equals(action)) {
                KvkCallPlugin.dispatchNotificationAction("TOGGLE_MIC");
                return START_STICKY;
            }
            if (ACTION_DISCONNECT.equals(action)) {
                KvkCallPlugin.dispatchNotificationAction("DISCONNECT");
                return START_STICKY;
            }
            roomName = intent.getStringExtra("roomName") == null
                ? roomName : intent.getStringExtra("roomName");
            micEnabled = intent.getBooleanExtra("micEnabled", micEnabled);
        }
        Notification notification = buildNotification();
        int types = 0;
        if (Build.VERSION.SDK_INT >= 29) {
            types = ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PLAYBACK;
            if (micEnabled) types |= ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE;
            ServiceCompat.startForeground(this, NOTIFICATION_ID, notification, types);
        } else {
            startForeground(NOTIFICATION_ID, notification);
        }
        return START_STICKY;
    }

    private Notification buildNotification() {
        Intent openIntent = getPackageManager().getLaunchIntentForPackage(getPackageName());
        PendingIntent contentPending = openIntent == null ? null :
            PendingIntent.getActivity(this, 1, openIntent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);

        // Launch the Activity directly from the notification action. Android allows
        // this user-initiated Activity launch; routing through a BroadcastReceiver and
        // calling startActivity() from its background context can be blocked on Android 10+.
        Intent muteIntent = getPackageManager().getLaunchIntentForPackage(getPackageName());
        PendingIntent mutePending = null;
        if (muteIntent != null) {
            muteIntent.setAction("com.kvkhub.voice.NOTIFICATION_MUTE");
            muteIntent.putExtra("kvkNotificationAction", ACTION_MUTE);
            muteIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_SINGLE_TOP);
            mutePending = PendingIntent.getActivity(this, 2, muteIntent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        }

        Intent unmuteIntent = getPackageManager().getLaunchIntentForPackage(getPackageName());
        PendingIntent unmutePending = null;
        if (unmuteIntent != null) {
            unmuteIntent.setAction("com.kvkhub.voice.NOTIFICATION_UNMUTE");
            unmuteIntent.putExtra("kvkNotificationAction", ACTION_UNMUTE);
            unmuteIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_SINGLE_TOP);
            unmutePending = PendingIntent.getActivity(this, 4, unmuteIntent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        }

        Intent disconnectIntent = new Intent(this, KvkVoiceActionReceiver.class);
        disconnectIntent.setAction(ACTION_DISCONNECT);
        PendingIntent disconnectPending = PendingIntent.getBroadcast(this, 3, disconnectIntent,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);

        NotificationCompat.Builder builder = new NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(getApplicationInfo().icon)
            .setContentTitle("KVK HUB • Voice room")
            .setContentText(roomName + (micEnabled ? " • Microphone ON" : " • Microphone OFF"))
            .setCategory(NotificationCompat.CATEGORY_CALL)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setOngoing(true)
            .setOnlyAlertOnce(true)
            .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
            .addAction(0, "Mute", mutePending)
            .addAction(0, "Unmute", unmutePending)
            .addAction(0, "Disconnect", disconnectPending);
        if (contentPending != null) builder.setContentIntent(contentPending);
        return builder.build();
    }

    @Override
    public void onDestroy() {
        ServiceCompat.stopForeground(this, ServiceCompat.STOP_FOREGROUND_REMOVE);
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) { return null; }
}
'''

receiver = r'''package com.kvkhub.voice;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public class KvkVoiceActionReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent == null) return;
        String action = intent.getAction();
        if (KvkVoiceService.ACTION_MUTE.equals(action)
                || KvkVoiceService.ACTION_UNMUTE.equals(action)) {
            Intent launch = context.getPackageManager().getLaunchIntentForPackage(context.getPackageName());
            if (launch != null) {
                launch.putExtra("kvkNotificationAction", action);
                launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_SINGLE_TOP);
                context.startActivity(launch);
            }
        } else if (KvkVoiceService.ACTION_DISCONNECT.equals(action)) {
            KvkCallPlugin.dispatchNotificationAction("DISCONNECT");
        }
    }
}
'''

(base / "KvkCallPlugin.java").write_text(plugin)
(base / "KvkVoiceService.java").write_text(service)
(base / "KvkVoiceActionReceiver.java").write_text(receiver)

manifest = Path("android/app/src/main/AndroidManifest.xml")
text = manifest.read_text()
permissions = [
    '    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />',
    '    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_MEDIA_PLAYBACK" />',
    '    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_MICROPHONE" />',
    '    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />',
]
for permission in permissions:
    if permission not in text:
        text = text.replace("</manifest>", permission + "\n</manifest>")
service_decl = '''        <service
            android:name="com.kvkhub.voice.KvkVoiceService"
            android:exported="false"
            android:foregroundServiceType="mediaPlayback|microphone" />
        <receiver
            android:name="com.kvkhub.voice.KvkVoiceActionReceiver"
            android:enabled="true"
            android:exported="false" />'''
if "KvkVoiceService" not in text:
    text = text.replace("</application>", service_decl + "\n    </application>")
manifest.write_text(text)

activities = list(Path("android/app/src/main/java").rglob("MainActivity.java"))
if len(activities) != 1:
    raise SystemExit(f"Expected one MainActivity.java, found {len(activities)}")
activity = activities[0]
source = activity.read_text()
if "KvkCallPlugin" not in source:
    package_end = source.find("\n")
    source = source[:package_end + 1] + "\nimport com.kvkhub.voice.KvkCallPlugin;\n" + source[package_end + 1:]
    source, count = re.subn(
        r"(public class MainActivity extends BridgeActivity\s*\{)",
        r'\1\n    @Override\n    public void onCreate(android.os.Bundle savedInstanceState) {\n        registerPlugin(KvkCallPlugin.class);\n        super.onCreate(savedInstanceState);\n        KvkCallPlugin.handleNotificationIntent(getIntent());\n    }\n',
        source, count=1)
    if count != 1:
        raise SystemExit("Could not register KvkCallPlugin in MainActivity")
if "onNewIntent(android.content.Intent intent)" not in source:
    source = source.replace(
        "    @Override\n    public void onCreate(android.os.Bundle savedInstanceState) {",
        "    @Override\n    public void onNewIntent(android.content.Intent intent) {\n        super.onNewIntent(intent);\n        setIntent(intent);\n        KvkCallPlugin.handleNotificationIntent(intent);\n    }\n\n    @Override\n    public void onCreate(android.os.Bundle savedInstanceState) {"
    )
    if "onNewIntent(android.content.Intent intent)" not in source:
        raise SystemExit("Could not add MainActivity onNewIntent handler")
    if "KvkCallPlugin.handleNotificationIntent(getIntent());" not in source:
        source=source.replace("super.onCreate(savedInstanceState);","super.onCreate(savedInstanceState);\n        KvkCallPlugin.handleNotificationIntent(getIntent());",1)
activity.write_text(source)

print("Added KVK HUB Android foreground voice service, notification actions, and Capacitor bridge.")
