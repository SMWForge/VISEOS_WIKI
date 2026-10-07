# 9. Bauen und Flashen

[← Signierung](08-Signierung.md) · [Weiter: Offene Punkte →](10-Offene-Punkte.md)

## Voraussetzungen

- Baum unter `/root/aosp`, Local Manifest `viseos_tegu.xml`, Blobs extrahiert und
  `prepare-blobs.sh` ausgeführt, Kernel-Prebuilts per `prepare-kernel.py`.
- Für Releases: Schlüssel in `/root/.viseos-keys` (`make-release-keys.sh`).
- Für Gradle-Apps: Android-SDK unter `/root/Android/Sdk`.

## Entwicklungs-Build

```bash
vendor/viseos/scripts/build.sh nothing    # erst die Analyse grün bekommen
vendor/viseos/scripts/build.sh            # dann voll bauen (erstmals ~1,5 h, im Hintergrund)
```

Ergebnis in `out/target/product/tegu/`: `boot.img`, `init_boot.img`, `vendor_boot.img`,
`vendor_kernel_boot.img`, `dtbo.img`, `vbmeta*.img`, `system.img`, `vendor.img`, `product.img`,
`system_ext.img`, `super_empty.img` u. a. Bootloader- und Radio-Images entstehen bewusst keine.

Der Lunch-Typ ist derzeit `userdebug` (siehe [Offene Punkte](10-Offene-Punkte.md)).

## Release-Build

```bash
/root/aosp-tools/build_and_update.sh --version 1.0.0 --changelog CHANGELOG.md --images --incremental
```

Das baut, signiert, erzeugt die OTAs und veröffentlicht sie auf `ota.smwforge.global`. Mit
`--images` entsteht zusätzlich der Ordner `/root/aosp-tools/release/tegu-1.0.0/` für die
Erstinstallation:

| Datei | Inhalt |
|---|---|
| `viseos-tegu-1.0.0-img.zip` | signierte Fastboot-Images (`fastboot update`) |
| `avb_pkmd.bin` | öffentlicher AVB-Schlüssel |
| `FLASHEN.txt` | Schritt-für-Schritt-Anleitung mit Fingerabdruck |

## Erstinstallation auf dem Pixel 9a

> Alle Schritte löschen die Daten auf dem Gerät.

1. **Stock-Firmware auf beide Slots.** ViseOS liefert Bootloader und Radio nicht mit. Die
   passende Firmware aus dem Factory-Image `CP2A.260805.005` muss auf **beiden** A/B-Slots
   stehen, sonst startet nach einem OTA-Slotwechsel eventuell eine unpassende Firmware.
   Bootloader und Radio aus dem Factory-Image deshalb mit `--slot=all` flashen.
2. **ViseOS flashen:**
   ```bash
   fastboot flashing unlock                   # falls gesperrt
   fastboot -w update viseos-tegu-1.0.0-img.zip
   ```
3. **Starten und prüfen**, dass das System sauber läuft.

### Bootloader wieder sperren

Nur mit Release-Builds, erst nach erfolgreichem Start:

```bash
fastboot reboot bootloader
fastboot erase avb_custom_key
fastboot flash avb_custom_key avb_pkmd.bin
fastboot reboot bootloader
fastboot flashing lock                     # löscht nochmals alle Daten
```

Danach bootet das Gerät mit gelbem Hinweis und nimmt nur noch mit diesen Schlüsseln signierte
Images und OTAs an.

## Updates

Alle weiteren Updates kommen per OTA über ViseUpdate (siehe [OTA-Updates](07-OTA-Updates.md)).
Ab dem zweiten Release erzeugt `--incremental` zusätzlich kleine Delta-Pakete.
