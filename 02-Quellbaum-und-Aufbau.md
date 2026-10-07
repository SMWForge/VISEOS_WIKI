# 2. Quellbaum und Aufbau

[← Überblick](01-Ueberblick.md) · [Weiter: Gerät tegu →](03-Geraet-tegu.md)

## Repos

Der Baum liegt auf dem Build-Rechner unter `/root/aosp`: AOSP Android 17 plus ein Local Manifest
`.repo/local_manifests/viseos_tegu.xml` mit den Gerätebäumen von LineageOS (`lineage-24.0`).

| Pfad | Quelle | Zweck |
|---|---|---|
| `device/google/tegu` | LineageOS `android_device_google_tegu` | Gerätebaum Pixel 9a |
| `device/google/zumapro` | LineageOS `android_device_google_zumapro` | Plattform Tensor G4 (BoardConfig, SEPolicy, HAL-Konfiguration) |
| `device/google/tegu-kernels` | LineageOS `android_device_google_tegu-kernels` | nur Ladelisten, wird für ViseOS **nicht** genutzt (siehe [Kernel](03-Geraet-tegu.md#kernel)) |
| `hardware/google/pixel` | LineageOS `android_hardware_google_pixel` | Pixel-HALs |
| `hardware/google/pixel-sepolicy` | LineageOS `android_hardware_google_pixel-sepolicy` | Pixel-SEPolicy |
| `tools/extract-utils`, `prebuilts/extract-tools`, `lineage/scripts` | LineageOS | nur für die Blob-Extraktion |
| `vendor/google/tegu` | extrahiert aus `CP2A.260805.005` | proprietäre Blobs (siehe [Blobs](04-Blobs.md)) |
| `vendor/viseos` | eigenes Repo | alles ViseOS-Spezifische |
| `vendor/smwforge/smwappstore` | eigenes Repo | SMWAppStore |
| `packages/apps/ViseBackup` | GitHub `SMWForge/ViseBackup` | Backup-App (Soong-Quellprojekt) |
| `packages/apps/ViseUpdate` | GitHub `SMWForge/ViseUpdate` | OTA-Client (Soong-Quellprojekt) |

Die Gradle-Projekte ViseReport, The_ViseOS_Launcher, ViseCall und ViseSetup werden außerhalb des
Baums gebaut. Als fertige APK kommen sie per `android_app_import` nach `vendor/viseos/apps/`.
Für Report und Launcher erledigt das [`vise-app.sh`](06-Werkzeuge.md#vise-appsh).

### Ausgeblendete Verzeichnisse (`.find-ignore`)

| Verzeichnis | Warum |
|---|---|
| `hardware/google/pixel/touch` | Lineage-Touch-HAL, braucht `hardware/lineage` |
| `device/google/zumapro/parts` | LineagePARTS, braucht das Lineage-SDK |
| `vendor/viseos/apps/ViseOSLauncher/aosp` | doppelte Launcher-Lieferung (würde Module zweimal definieren) |

## `vendor/viseos`

```
vendor/viseos/
├── NOTES.md                    Änderungsprotokoll (Datei – was – warum)
├── config/
│   ├── common.mk               gemeinsame Basis aller ViseOS-Produkte (Apps, OTA-URL)
│   └── vise-apps.mk            von vise-app.sh verwaltete Apps (derzeit ViseUpdate)
├── products/tegu/
│   ├── AndroidProducts.mk      PRODUCT_MAKEFILES := viseos_tegu.mk
│   ├── viseos_tegu.mk          Produkt viseos_tegu
│   └── rust-blobs.mk           (generiert) Rust-Laufzeit der Blobs
├── apps/
│   ├── ViseOSLauncher/         Launcher (Prebuilt-APK)
│   ├── ViseCall/               Telefon (Prebuilt-APK + 2 Overlays)
│   ├── ViseSetup/              Einrichtungsassistent (Prebuilt-APK)
│   ├── ViseReport/             Fehlerberichte (Prebuilt-APK)
│   └── ViseReportConfig/       RRO mit Server-URL/Upload-Key für ViseReport
├── prebuilts/kernel/tegu/6.1/  Stock-Kernel + Module (generiert, ~137 MB)
└── scripts/
    ├── build.sh                einziger Einstieg zum Bauen
    ├── prepare-blobs.sh        Nacharbeit nach jeder Blob-Extraktion
    ├── fix-blobs.py            Rust-Prebuilts -> cc_prebuilt, Rust-Laufzeit aus Stock
    ├── add-stock-libs.py       fehlende Vendor-Libs 1:1 aus Stock-vendor.img
    ├── filter-rust-blobs.py    Rust-Libs, die AOSP selbst baut, nicht doppelt installieren
    ├── rust-from-source.txt    Liste dafür
    ├── strip-firmware.py       Bootloader/Radio aus Build und OTA heraushalten
    └── prepare-kernel.py       Kernel-Prebuilts aus dem Factory-Image erzeugen
```

## Produktvererbung

```
viseos_tegu.mk
├── device/google/tegu/aosp_tegu.mk          Gerät (AOSP-Variante des Lineage-Baums)
├── vendor/viseos/config/common.mk           ViseOS-Basis
│   ├── vendor/smwforge/smwappstore/smwappstore.mk
│   ├── vendor/viseos/apps/ViseOSLauncher/viseoslauncher.mk
│   ├── vendor/viseos/apps/ViseCall/visecall.mk        (+ ViseReport, ViseReportConfigOverlay)
│   ├── vendor/viseos/apps/ViseSetup/visesetup.mk
│   ├── VISEUPDATE_SERVER_URL := https://ota.smwforge.global/api/v1/{device}/{channel}.json
│   └── vendor/viseos/config/vise-apps.mk
│       └── packages/apps/ViseUpdate/viseupdate.mk
├── vendor/viseos/products/tegu/rust-blobs.mk
├── vendor/google/tegu/tegu-vendor.mk         Blobs (muss nach allen anderen kommen)
└── packages/apps/ViseBackup/visebackup.mk
```

Wichtige Einstellungen in `viseos_tegu.mk`:

```make
TARGET_KERNEL_DIR := vendor/viseos/prebuilts/kernel/tegu/6.1
PRODUCT_NAME := viseos_tegu
PRODUCT_BRAND := ViseOS
PRODUCT_MODEL := ViseOS on Pixel 9a
PRODUCT_MANUFACTURER := SMWForge
```

`common.mk` ist für alle ViseOS-Produkte gedacht (auch Cuttlefish/GSI). Gerätespezifisches gehört
nach `products/<gerät>/`.
