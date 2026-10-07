# 1. Überblick

[← Start](README.md) · [Weiter: Quellbaum →](02-Quellbaum-und-Aufbau.md)

## Was ist ViseOS?

ViseOS ist ein Android-Betriebssystem von SMWForge:

- **Basis:** AOSP (Android 17, Release `cp2a`), ohne Google-Dienste.
- **Eigene Apps:** für Startbildschirm, Telefon, Einrichtung, Fehlerberichte, Datensicherung,
  Systemupdates und Apps.
- **Updates:** verteilt der eigene OTA-Server `ota.smwforge.global`.

| | |
|---|---|
| Gerät | Google Pixel 9a, Codename `tegu` (Tensor G4, Plattform `zumapro`) |
| Produkt | `viseos_tegu`, Lunch-Ziel `viseos_tegu-cp2a-userdebug` |
| Android | 17 (SDK 37), AOSP-Release `cp2a` |
| Kernel | Stock-GKI Linux 6.1 (android14-11) aus dem Factory-Image `CP2A.260805.005` |
| Blobs | `CP2A.260805.005` (Pixel-Factory-Image) |
| Gerätebäume | LineageOS `lineage-24.0` (nur die Device-/HAL-Repos, siehe [Quellbaum](02-Quellbaum-und-Aufbau.md)) |
| Update-Verfahren | A/B (Virtual A/B) über `update_engine`, Client ViseUpdate |
| Marke im System | Brand `ViseOS`, Modell „ViseOS on Pixel 9a“, Hersteller `SMWForge` |

## Grundregeln des Projekts

Diese Regeln gelten für jede Änderung am Baum:

1. **Kein LineageOS-Unterbau.** Es gibt kein `vendor/lineage` und kein `hardware/lineage/*`.
   Lineage-Bezüge in den Gerätebäumen werden entfernt oder AOSP-tauglich ersetzt, nicht
   nachgezogen. Ein LineageOS-23.2-Baum dient nur als Nachschlagewerk.
2. **Fehlende Vendor-Bibliotheken**, die Lineage aus Quellcode baut, kommen 1:1 aus dem
   Stock-`vendor.img`.
3. **Änderungen bevorzugt in `vendor/viseos`.** Änderungen in den Lineage-Repos so klein wie
   möglich halten. Den AOSP-Kern (`build/`, `system/`, `frameworks/`, `external/`) nur anfassen,
   wenn es nicht anders geht. Bisher war das nicht nötig.
4. **Jede Änderung wird protokolliert** in `vendor/viseos/NOTES.md`: Datei, was, warum. Daraus
   werden später Forks bzw. Patches.
5. **Keine Firmware** (Bootloader/Radio) in Images oder OTA-Paketen. Die Firmware kommt nur über
   das Google-Factory-Image aufs Gerät.
6. **SEPolicy:** Kompilierfehler sauber lösen, keine `neverallow` in `system/sepolicy` entfernen.
7. **Kernel:** Solange der Lineage-Kernelbau an `vendor/lineage` hängt, werden die
   Kernel-Artefakte aus dem CP2A-Factory-Image als Prebuilts genutzt.
8. **Gebaut wird immer über `vendor/viseos/scripts/build.sh`.** `lunch` nie in einer Pipe.

## Was gegenüber AOSP anders ist (Kurzliste)

| Bereich | Änderung | Seite |
|---|---|---|
| Gerätebäume | Lineage-Health und Lineage-Touch entfernt, Kernel-Pfad überschreibbar gemacht, LineagePARTS ausgeblendet | [3](03-Geraet-tegu.md) |
| Kernel | Stock-GKI + 328 Module als Prebuilt in `vendor/viseos/prebuilts/kernel/tegu/6.1` | [3](03-Geraet-tegu.md) |
| Blobs | Rust-Prebuilts → `cc_prebuilt`, `libjson` aus Stock, doppelte Rust-Libs gefiltert, Firmware entfernt | [4](04-Blobs.md) |
| Telefon | ViseCall ersetzt den AOSP-Dialer, mit Overlays für Standard-Dialer und Telecom | [5](05-System-Apps.md#visecall) |
| Einrichtung | ViseSetup ersetzt Provision/SdkSetup | [5](05-System-Apps.md#visesetup) |
| Startbildschirm | ViseOSLauncher (privilegiert, Platform-Key) | [5](05-System-Apps.md#viseoslauncher) |
| Fehlerberichte | ViseReport + Konfigurations-Overlay (Server-URL) | [5](05-System-Apps.md#visereport) |
| Datensicherung | ViseBackup (eigener BackupTransport) | [5](05-System-Apps.md#visebackup) |
| Systemupdates | ViseUpdate + SELinux-Regeln + Server-URL `ota.smwforge.global` | [5](05-System-Apps.md#viseupdate), [7](07-OTA-Updates.md) |
| App-Store | SMWAppStore (vorsigniert, `/product/app`) | [5](05-System-Apps.md#smwappstore) |
| Signierung | eigene Release- und AVB-Schlüssel statt AOSP-Testschlüssel | [8](08-Signierung.md) |
