# ViseOS-Wiki

ViseOS ist ein freies Android von **SMWForge** auf Basis von AOSP (Android 17). Es kommt ohne
Google-Dienste aus und bringt eigene System-Apps mit: Launcher, Telefon, Einrichtung,
Fehlerberichte, Backup, Updates und App-Store. Dieses Wiki dokumentiert alles, was gegenüber AOSP
und den verwendeten LineageOS-Gerätebäumen angepasst wurde, und wie ViseOS gebaut, signiert und
per OTA verteilt wird.

Erstes Zielgerät: **Google Pixel 9a (`tegu`)**, Produkt `viseos_tegu`.

## Inhalt

| Seite | Worum es geht |
|---|---|
| [1. Überblick](01-Ueberblick.md) | Basis, Ziele, Grundregeln des Projekts |
| [2. Quellbaum und Aufbau](02-Quellbaum-und-Aufbau.md) | Repos, Local Manifest, `vendor/viseos`, Produktvererbung |
| [3. Gerät tegu: Anpassungen](03-Geraet-tegu.md) | Kernel, entfernte Lineage-Teile, Patches an Device-Trees, Firmware |
| [4. Proprietäre Blobs](04-Blobs.md) | Extraktion, Nacharbeit (Rust, fehlende Libs, Firmware) |
| [5. System-Apps](05-System-Apps.md) | ViseOSLauncher, ViseCall, ViseSetup, ViseReport, ViseBackup, ViseUpdate, SMWAppStore |
| [6. Werkzeuge](06-Werkzeuge.md) | `build.sh`, `vise-app.sh`, `build_and_update.sh`, `make-release-keys.sh` |
| [7. OTA-Updates](07-OTA-Updates.md) | ViseUpdate-Client, OTA-Server `ota.smwforge.global`, Veröffentlichen |
| [8. Signierung](08-Signierung.md) | Release-Schlüssel, Verified Boot, Bootloader wieder sperren |
| [9. Bauen und Flashen](09-Bauen.md) | Build-Ablauf, Images, Erstinstallation |
| [10. Offene Punkte](10-Offene-Punkte.md) | Bekannte Lücken, Funktionsverluste, nächste Schritte |
| [11. Änderungsprotokoll](11-Aenderungsprotokoll.md) | Chronologie aller Änderungen |

## Kurzfassung

- **Basis:** AOSP Android 17, Release `cp2a`. Die Gerätebäume für `tegu`/`zumapro` kommen von
  LineageOS `lineage-24.0`, aber ohne `vendor/lineage` und `hardware/lineage`.
- **Blobs:** Stand `CP2A.260805.005`. Rust-Prebuilts werden umgebaut, fehlende Vendor-Libs kommen
  1:1 aus dem Stock-`vendor.img`, und Bootloader/Radio-Firmware wird herausgefiltert.
- **Kernel:** Stock-GKI 6.1 aus dem CP2A-Factory-Image, als Prebuilt mit Modulen.
- **Apps:** sieben eigene Apps ersetzen bzw. ergänzen AOSP. ViseCall ersetzt den Dialer,
  ViseSetup ersetzt Provision. ViseOSLauncher kommt neben Launcher3QuickStep dazu, das die
  „Letzten Apps“ und die Gestennavigation liefert. Dazu ViseReport, ViseBackup, ViseUpdate und
  SMWAppStore.
- **Updates:** A/B-OTAs über ViseUpdate vom eigenen Server `https://ota.smwforge.global`.
- **Signierung:** eigene Release-Schlüssel (RSA-4096) und ein eigener AVB-Schlüssel. Der
  Bootloader lässt sich damit wieder sperren.

> Hinweis: Dieses Wiki enthält bewusst **keine** Schlüssel, Passwörter oder Upload-Keys. Die
> Pfade (`/root/aosp`, `/root/aosp-tools`) beziehen sich auf den Build-Rechner.
