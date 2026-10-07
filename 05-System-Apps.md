# 5. System-Apps

[← Blobs](04-Blobs.md) · [Weiter: Werkzeuge →](06-Werkzeuge.md)

## Übersicht

| App | Paket | Ablage im Image | Signatur | Ersetzt | Quelle / Einbindung |
|---|---|---|---|---|---|
| [ViseOSLauncher](#viseoslauncher) | `com.smwforge.viseoslauncher` | `/system_ext/priv-app` | Platform | – (neben Launcher3QuickStep) | GitHub `The_ViseOS_Launcher`, Prebuilt in `vendor/viseos/apps/ViseOSLauncher` |
| [ViseCall](#visecall) | `com.smwforge.visecall` | `/system_ext/priv-app` | Platform | **Dialer** | Prebuilt in `vendor/viseos/apps/ViseCall` |
| [ViseSetup](#visesetup) | `com.smwforge.visesetup` | `/system_ext/priv-app` | Platform | **Provision, SdkSetup** | Prebuilt in `vendor/viseos/apps/ViseSetup` |
| [ViseReport](#visereport) | `com.smwforge.visereport` | `/system_ext/priv-app` | Platform | – | GitHub `ViseReport`, Prebuilt in `vendor/viseos/apps/ViseReport` |
| [ViseBackup](#visebackup) | `com.smwforge.visebackup` | `/system_ext/priv-app` | Platform | – | GitHub `ViseBackup`, Quellcode in `packages/apps/ViseBackup` |
| [ViseUpdate](#viseupdate) | `com.smwforge.viseupdate` | `/system_ext/priv-app` | Platform | – | GitHub `ViseUpdate`, Quellcode in `packages/apps/ViseUpdate` |
| [SMWAppStore](#smwappstore) | `com.smwforge.smw_app_store` | `/product/app` | vorsigniert | – | `vendor/smwforge/smwappstore` |

„Platform“ heißt: Der Build signiert die App mit dem Platform-Schlüssel neu. Im Release ist das
der ViseOS-Platform-Schlüssel, siehe [Signierung](08-Signierung.md). Erst dadurch bekommt die App
Signature-Rechte und darf versteckte APIs nutzen. Privilegierte Rechte
(`signature|privileged`) brauchen zusätzlich eine **Privapp-Allowlist** unter
`/system_ext/etc/permissions`. Fehlt dort ein Eintrag, bootet ein Gerät mit
`ro.control_privapp_permissions=enforce` nicht.

## ViseOSLauncher

Startbildschirm von ViseOS (Kotlin, Jetpack Compose):

- **Startbildschirm:** mehrere Seiten mit Raster von 4–6 × 4–7.
- **Drag & Drop:** Apps und Widgets frei verschieben.
- **Widgets:** alle Android-Widgets plus eigene ViseOS-Widgets (Reaktor-Uhr, Digitaluhr,
  Suchleiste).
- **Dock** mit bis zu 5 Apps.
- **Hintergrund:** animiertes Cyber-Grid.

| | |
|---|---|
| Privapp-Rechte | `DEVICE_POWER` (Bildschirm aus), `BIND_APPWIDGET` (Widgets) |
| Besonderheiten | `optional_uses_libs: androidx.window.extensions, androidx.window.sidecar`, sonst scheitert die uses-library-Prüfung beim dexpreopt |
| Makefile | `vendor/viseos/apps/ViseOSLauncher/viseoslauncher.mk` |
| Aktualisieren | `vise-app.sh -addorupdate The_ViseOS_Launcher true` |

Launcher3QuickStep bleibt im Image, weil es „Letzte Apps“ und die Gestennavigation liefert.

## ViseCall

Telefon-App von ViseOS. Sie **ersetzt den AOSP-Dialer** (`overrides: ["Dialer"]`).

| | |
|---|---|
| Privapp-Rechte | `CALL_PRIVILEGED`, `MODIFY_PHONE_STATE`, `READ_PRIVILEGED_PHONE_STATE`, `CAPTURE_AUDIO_OUTPUT`, `CALL_AUDIO_INTERCEPTION` (Anrufaufnahme) |
| Ab Werk erteilt | Telefon, Rufnummern, Anrufliste (lesen/schreiben), Kontakte (lesen/schreiben), Mikrofon, SMS senden, Benachrichtigungen |
| Overlay `ViseCallFrameworkOverlay` | `config_defaultDialer = com.smwforge.visecall`, damit hält ViseCall ab Werk die DIALER-Rolle |
| Overlay `ViseCallTelecomOverlay` | `incall_default_class` und `dialer_default_class` zeigen auf ViseCall, damit Telecom bei Notrufen den richtigen Fallback nutzt. Ziel ist `com.android.server.telecom.resources` im APEX. |
| Makefile | `vendor/viseos/apps/ViseCall/visecall.mk` (enthält auch den ViseReport-Block) |

## ViseSetup

Einrichtungsassistent beim ersten Start. **Ersetzt Provision und SdkSetup**
(`overrides: ["Provision", "SdkSetup"]`). Er setzt `DEVICE_PROVISIONED` und
`USER_SETUP_COMPLETE` und deaktiviert sich danach selbst.

| | |
|---|---|
| Privapp-Rechte | `WRITE_SECURE_SETTINGS`, `STATUS_BAR`, `CHANGE_CONFIGURATION`, `SET_TIME`, `SET_TIME_ZONE` |
| Signature-Rechte (Platform-Key) | `NETWORK_SETTINGS`, `MANAGE_ROLE_HOLDERS`, `SET_PREFERRED_APPLICATIONS`, versteckte APIs (StatusBarManager, WifiManager#connect, LocaleManager) |
| Makefile | `vendor/viseos/apps/ViseSetup/visesetup.mk` |

## ViseReport

Fehlerberichte:

- **Erkennt** Abstürze von Apps und System über die DropBox.
- **Anonymisiert** die Berichte auf dem Gerät.
- **Sendet** sie nur mit Einwilligung an den ViseReport-Server.

Kotlin, ohne AndroidX.

| | |
|---|---|
| Privapp-Rechte | `READ_LOGS`, `READ_DROPBOX_DATA`, `PACKAGE_USAGE_STATS`, `DUMP` |
| Ab Werk erteilt | Benachrichtigungen (widerrufbar) |
| Konfiguration | RRO `ViseReportConfigOverlay` (`vendor/viseos/apps/ViseReportConfig`) mit `config_server_url = https://reports.smwforge.global` und `config_upload_key` |
| Einbindung | Block in `visecall.mk` (`PRODUCT_PACKAGES += ViseReport ViseReportConfigOverlay`) |
| Aktualisieren | `vise-app.sh -addorupdate ViseReport true` (das bestehende Overlay bleibt erhalten) |

> Der Upload-Key im Overlay ist derzeit nur ein Platzhalter, siehe [Offene Punkte](10-Offene-Punkte.md).

## ViseBackup

Vollständige Sicherung ohne Google:

- **Was:** Apps, App-Daten (über einen eigenen **BackupTransport** wie Seedvault), SMS/MMS,
  Anrufliste, Kontakte und Dateien (dedupliziert).
- **Wohin:** auf USB-Stick, PC oder eigenen Server.
- **Optional verschlüsselt** mit AES-256-GCM.
- **Automatik** per Zeitplan oder beim Einstecken eines USB-Sticks.

| | |
|---|---|
| Bau | aus Quellcode (`android_app`, `platform_apis: true`), `packages/apps/ViseBackup` |
| Privapp-Rechte | `BACKUP`, `INSTALL_PACKAGES`, `MANAGE_APP_OPS_MODES`, `WRITE_MEDIA_STORAGE`, `START_FOREGROUND_SERVICES_FROM_BACKGROUND` |
| Ab Werk erteilt | SMS lesen, Anrufliste, Kontakte, Konten, Benachrichtigungen |
| Sysconfig | `sysconfig-visebackup.xml`: Freigabe als Backup-Transport + Hintergrund-Ausnahmen |
| Einbindung | `$(call inherit-product, packages/apps/ViseBackup/visebackup.mk)` in `viseos_tegu.mk` |
| Server | `packages/apps/ViseBackup/server/visebackup-server.py` (WebDAV-Teilmenge, systemd-Unit dabei) |
| Hinweis | `ro.backup.disable` darf nicht `true` sein |

## ViseUpdate

OTA-Client für A/B-Updates über `update_engine`. Er erscheint unter
*Einstellungen → System → Systemupdate*. Details auf der Seite [OTA-Updates](07-OTA-Updates.md).

| | |
|---|---|
| Bau | aus Quellcode, `packages/apps/ViseUpdate`, läuft als `android.uid.system` |
| Privapp-Rechte | `REBOOT` |
| SEPolicy | `packages/apps/ViseUpdate/sepolicy`: `system_app` darf `/data/ota_package` schreiben und mit `update_engine` sprechen |
| Server | `ro.viseupdate.server_url=https://ota.smwforge.global/api/v1/{device}/{channel}.json` |
| Einbindung | `vendor/viseos/config/vise-apps.mk` → `packages/apps/ViseUpdate/viseupdate.mk` |

## SMWAppStore

App-Store von SMWForge.

| | |
|---|---|
| Ablage | `/product/app/SMWAppStore` (keine privilegierte App) |
| Signatur | vorsigniert (`presigned: true`, `preprocessed: true`, native Libs unkomprimiert) |
| Sonderrecht | Das init-Script `smw_appops.rc` setzt bei jedem Boot (`sys.boot_completed=1`) das App-Op `REQUEST_INSTALL_PACKAGES allow`. Damit darf der Store ohne Rückfrage Apps installieren. |
| Makefile | `vendor/smwforge/smwappstore/smwappstore.mk` |

## Neue Apps hinzufügen

Mit [`vise-app.sh`](06-Werkzeuge.md#vise-appsh):

```bash
/root/aosp-tools/vise-app.sh -addorupdate <GitHub-Repo> true    # privilegierte System-App
/root/aosp-tools/vise-app.sh -addorupdate <GitHub-Repo> false   # normale vorinstallierte App
```
