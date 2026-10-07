# 11. Änderungsprotokoll

[← Offene Punkte](10-Offene-Punkte.md) · [Start](README.md)

Kurzfassung von `vendor/viseos/NOTES.md`. Dort steht zu jeder Änderung Datei, Inhalt und Grund.

## Vor dem 6. Oktober 2026 (vorgefundener Stand)

- Produkt `viseos_tegu` angelegt (`vendor/viseos/products/tegu`). Es erbt `aosp_tegu.mk`,
  `config/common.mk`, `rust-blobs.mk` und die Blobs.
- `build.sh` als einziger Build-Einstieg (`lunch viseos_tegu-cp2a-userdebug`, Log nach `out/`).
- Blob-Nacharbeit: `prepare-blobs.sh` mit `fix-blobs.py` (Rust-Prebuilts → `cc_prebuilt`),
  `add-stock-libs.py libjson` und `filter-rust-blobs.py` + `rust-from-source.txt`.
- System-Apps ViseOSLauncher, ViseCall (ersetzt Dialer, 2 Overlays), ViseSetup (ersetzt
  Provision) und SMWAppStore eingebunden.

## 6. Oktober 2026

- `filter-rust-blobs.py` entfernt zusätzlich die doppelten `viseos_rust_*`-Module aus
  `vendor/google/tegu/Android.bp`, weil Kati an doppelten Install-Regeln abbrach
  (`libaho_corasick.dylib.so`).
- **Kernel:** `prepare-kernel.py` erzeugt Prebuilts aus dem CP2A-Factory-Image (GKI 6.1.157,
  328 Module, dtbo, dtb). `TARGET_KERNEL_DIR` zeigt im Produkt darauf.
- `device/google/tegu/device-tegu.mk`: `TARGET_KERNEL_DIR :=` → `?=`.
- `device/google/zumapro/common.mk`: Lineage-Health und Lineage-Touch entfernt, weil der
  SEPolicy-Fehler `unknown type hal_lineage_health_default` den Build bei 66 % stoppte.
- **Erster voller Build erfolgreich** (13:09). `boot.img`/`dtbo.img` sind im Inhalt identisch zu
  Stock, keine Firmware-Images.
- ViseReport (+ Konfigurations-Overlay) und ViseBackup (`packages/apps/ViseBackup`) eingebunden.

## 7. Oktober 2026

- Launcher-Allowlist um `BIND_APPWIDGET` ergänzt (Widgets). Die doppelte Launcher-Lieferung per
  `.find-ignore` ausgeblendet.
- **Voller Build erfolgreich** (01:45, 1 h 23 min).
- Abgleich der Vise-Apps mit GitHub: ViseReport `0c0d385`, ViseBackup `48694a7`, Launcher
  `649ca25` (Home-Seiten, Widgets, Drag & Drop) sind im Build. Prüfsumme der Launcher-APK
  aktualisiert.
- **`vise-app.sh`**: Apps per `-addorupdate <repo> <true|false>` aus GitHub holen und einbinden.
  Erstlauf für alle drei Apps. Neu: `vendor/viseos/config/vise-apps.mk`.
- **ViseUpdate** (OTA-Client, `bc24404`) nach `packages/apps/ViseUpdate`, eingebunden über
  `vise-apps.mk`. Server-URL `https://ota.smwforge.global/api/v1/{device}/{channel}.json` in
  `common.mk`. Geprüft: App und SEPolicy bauen, URL steht in der build.prop.
- **OTA-Server** `viseupdate-server` als Debian-Paket (systemd + nginx + `viseupdate-publish`),
  41 Tests grün.
- **Firmware aus Build und OTA entfernt** (`strip-firmware.py`, läuft in `prepare-blobs.sh`).
  Vorher hätten Bootloader und Modem in jedem OTA gesteckt.
- **`build_and_update.sh`**: bauen → prüfen → OTA → veröffentlichen → archivieren. Mit
  eindeutiger `BUILD_NUMBER` und inkrementellen Paketen. Getestet: volles OTA 1,3 GB, Delta 188 KB.
- **Release-Signatur:** `make-release-keys.sh` erzeugt eigene Schlüssel (RSA-4096, inkl. 41
  APEX-Schlüsselpaare und AVB-Schlüssel). `build_and_update.sh` signiert mit
  `sign_target_files_apks -o` und prüft das Ergebnis. Testschlüssel nur noch mit `--test-keys`.
  Beim Erproben gefunden und behoben:
  - Ohne `-o` behält `otacerts.zip` den testkey.
  - `META/apkcerts.txt` taugt nicht zur Prüfung. Geprüft wird jetzt an den echten Signaturen.
  - Das Archiv unterscheidet Builds jetzt auch nach Schlüsseln. Vorher hätte eine testsignierte
    Fassung als Basis für Deltas dienen können.
- Dieses Wiki angelegt.
