# 10. Offene Punkte

[← Bauen und Flashen](09-Bauen.md) · [Weiter: Änderungsprotokoll →](11-Aenderungsprotokoll.md)

Stand: 7. Oktober 2026

## Vor dem ersten öffentlichen Release

| # | Punkt | Warum wichtig | Wo |
|---|---|---|---|
| 1 | **ViseReport-Upload-Key setzen.** `config_upload_key` im Overlay ist nur ein Platzhalter. | Fehlerberichte werden sonst vom Server abgelehnt | `vendor/viseos/apps/ViseReportConfig/res/values/config.xml` (über `install_to_vendor.sh --server-url … --upload-key …` von ViseReport) |
| 2 | **OTA-Server einrichten:** DNS `ota.smwforge.global`, `viseupdate-server` installieren, `certbot --nginx` | ohne Server keine Updates. Das Veröffentlichen per SSH ist noch ungetestet. | [OTA-Updates](07-OTA-Updates.md#der-ota-server) |
| 3 | **Release-Schlüssel offline sichern** (`/root/.viseos-keys`, verschlüsselt, zwei Kopien) | Schlüsselverlust = nie wieder Updates | [Signierung](08-Signierung.md) |
| 4 | **Build-Typ `user` statt `userdebug` erwägen** | `userdebug` erlaubt `adb root` und ist debuggable. Für Endgeräte ist `user` üblich. `build.sh` setzt den Lunch-Typ fest auf `userdebug`. | `vendor/viseos/scripts/build.sh` |
| 5 | **`ro.vise.version` setzen** | ViseUpdate zeigt die installierte ViseOS-Version aus dieser Property an. Sie fehlt bisher. | z. B. `PRODUCT_SYSTEM_EXT_PROPERTIES` in `common.mk` |
| 6 | **`vendor/viseos` committen** | Der Großteil (scripts, products, config, Apps, NOTES.md) ist im Git-Repo noch nicht eingecheckt | `vendor/viseos` |
| 7 | **Lineage-Patches sichern**: `device/google/tegu/device-tegu.mk` (1 Zeile) und `device/google/zumapro/common.mk` (−10 Zeilen) | lokale Änderungen in Lineage-Repos gehen bei `repo sync` verloren. Als Fork oder Patch-Satz ablegen. | [Gerät tegu](03-Geraet-tegu.md#patches-an-den-lineage-gerätebäumen) |
| 8 | **Firmware auf beiden Slots** bei der Erstinstallation | OTAs enthalten keine Firmware. Nach einem Slotwechsel muss die Firmware des anderen Slots passen. | [Bauen und Flashen](09-Bauen.md) |

## Funktionsverluste gegenüber LineageOS

| Funktion | Ursache | Möglicher Ersatz |
|---|---|---|
| Ladebegrenzung / Akkuschonung (Lineage Health) | `hardware/google/pixel/lineage_health` braucht `hardware/lineage` | AOSP-eigene Lade-Optimierung prüfen, oder eigene HAL ohne Lineage-Typen |
| Touch-Empfindlichkeit / Handschuhmodus | Lineage-Touch-HAL (`vendor.lineage.touch`) | eigene Einstellung über die Pixel-Touch-Sysfs-Knoten |
| LineagePARTS (Einstellungen) | Lineage-SDK | nicht nötig bzw. in ViseOS-Apps abbilden |
| 16k-Seitenmodus (Kernel) | beim Übernehmen der Stock-Kernel bewusst weggelassen | nur bei Bedarf |

## Aufräumen

- `vendor/viseos/apps/ViseOSLauncher/aosp/`: doppelte Launcher-Lieferung. Sie ist per
  `.find-ignore` ausgeblendet und kann entfernt werden.
- Testartefakte unter `/root/aosp-tools/` aus der Erprobung von `build_and_update.sh`, **nicht
  hochladen**: `ota-staging`, `ota-archive`, `test-staging*`, `test-archive`, `test-release`,
  `build_and_update-test*.log`. Sie enthalten Testversionen bzw. testsignierte Builds.
- In den Privapp-Allowlists stehen Rechte, die gar nicht `privileged` sind:
  `MANAGE_APP_OPS_MODES` bei ViseBackup, `DEVICE_POWER` beim Launcher. Das ist harmlos, könnte
  aber in den App-Repos bereinigt werden.

## Ideen

- ViseCall und ViseSetup ebenfalls über `vise-app.sh` aus GitHub pflegen, wie Report und Launcher.
- Kanal `beta` für Testgeräte (`--channel beta` in `build_and_update.sh`).
- Firmware-Updates: Bisher nur per Factory-Image (Projektregel). Ob Firmware je per OTA
  ausgeliefert werden soll, ist eine offene Entscheidung.
