# 8. Signierung

[← OTA-Updates](07-OTA-Updates.md) · [Weiter: Bauen und Flashen →](09-Bauen.md)

## Warum eigene Schlüssel?

Ein normaler AOSP-Build ist mit den **öffentlich bekannten** AOSP-Testschlüsseln signiert. Mit
diesen Schlüsseln kann jeder Updates und System-Apps bauen, denen das Gerät vertraut. ViseOS
signiert deshalb jeden Release-Build mit eigenen Schlüsseln.

**Entscheidungen** (Oktober 2026):

- **Wann:** nach dem Build signieren, wie LineageOS und GrapheneOS.
- **Ablage:** `/root/.viseos-keys`, ohne Passwort, Verzeichnisrechte `0700`.
- **Verified Boot:** eigener AVB-Schlüssel RSA-4096. Damit lässt sich der Bootloader wieder
  sperren.
- **Zertifikats-Subject:** `/C=DE/O=SMWForge/CN=ViseOS/emailAddress=no-reply@smwforge.com`

## Die Schlüssel

Erzeugt von `/root/aosp-tools/make-release-keys.sh`. Alle Schlüssel sind RSA-4096, die
Zertifikate 10000 Tage gültig.

| Datei | Ersetzt | Wofür |
|---|---|---|
| `releasekey.{pk8,x509.pem}` | `testkey` | normale System-Apps, **OTA-Pakete**, `otacerts.zip` |
| `platform.*` | `platform` | Framework und Platform-Apps (alle Vise-Apps mit `certificate: "platform"`) |
| `shared.*`, `media.*` | `shared`, `media` | Kontakte/Telefonie bzw. Medien-Provider |
| `networkstack.*`, `sdk_sandbox.*` | gleichnamige | Netzwerk-Stack, SDK-Sandbox |
| `bluetooth.*`, `nfc.*` | gleichnamige | vorsorglich, derzeit im Build nicht genutzt |
| `avb.pem` | `testkey_rsa2048/4096.pem` | Verified Boot: vbmeta, boot, init_boot, vbmeta_system, vbmeta_vendor |
| `avb_pkmd.bin` | – | öffentlicher AVB-Schlüssel für `fastboot flash avb_custom_key` |
| `apex/<name>.{pk8,x509.pem}` + `apex/<name>.pem` | Modul-Testschlüssel | je APEX Container-Zertifikat + Payload-Schlüssel (41 Module; 6 weitere sind vorsigniert) |

`make-release-keys.sh` überschreibt **nie** einen vorhandenen Schlüssel. Kommt durch ein
AOSP-Update ein neues APEX-Modul dazu, bekommt es beim nächsten `build_and_update.sh`
automatisch eigene Schlüssel.

> **Sicherung:** Das Verzeichnis `/root/.viseos-keys` muss offline gesichert werden,
> verschlüsselt und mindestens doppelt. Ohne diese Schlüssel kann ViseOS **nie wieder**
> aktualisiert werden. Bei gesperrtem Bootloader hilft dann nur Entsperren, und das löscht alle
> Daten. Die Schlüssel gehören nie in git, auf den OTA-Server oder nach `/root/aosp`.

## Ablauf beim Signieren

`build_and_update.sh` macht das automatisch:

```bash
sign_target_files_apks -o -d /root/.viseos-keys \
    -k build/make/target/product/security/bluetooth=/root/.viseos-keys/bluetooth \
    -k build/make/target/product/security/nfc=/root/.viseos-keys/nfc \
    --extra_apks <apex>.apex=/root/.viseos-keys/apex/<apex> \
    --extra_apex_payload_key <apex>.apex=/root/.viseos-keys/apex/<apex>.pem   # je APEX \
    --avb_<part>_key /root/.viseos-keys/avb.pem --avb_<part>_algorithm SHA256_RSA4096 \
    viseos_tegu-target_files.zip viseos_tegu-signed-target_files.zip

ota_from_target_files -k /root/.viseos-keys/releasekey viseos_tegu-signed-target_files.zip ota.zip
img_from_target_files viseos_tegu-signed-target_files.zip img.zip      # nur mit --images
```

- `-d` bildet `testkey`, `platform`, `shared`, `media`, `networkstack` und `sdk_sandbox` auf die
  Release-Schlüssel ab.
- `-o` ersetzt `otacerts.zip` in System **und** vendor_boot-Ramdisk durch den releasekey. Das
  ist der Schlüssel, gegen den ViseUpdate und `update_engine` OTAs prüfen. **Ohne `-o` behält
  das System den testkey** und würde jedes Release-OTA ablehnen.
- Vorsignierte Apps (Vendor-Blobs, SMWAppStore) bleiben unverändert.

### Automatische Prüfung nach dem Signieren

`build_and_update.sh` bricht ab, wenn eine dieser Bedingungen nicht erfüllt ist:

1. Jedes `otacerts.zip` im Build enthält genau den releasekey.
2. Kein eingebautes APK und kein APEX trägt noch ein AOSP-Testzertifikat
   (`build/make/target/product/security/…`), und kein APEX hat noch seinen
   Test-Payload-Schlüssel. Geprüft wird an den **echten Signaturen**: Der APK Signing Block
   v2/v3 wird aus jedem Paket gelesen (`/root/aosp-tools/lib/check_signed_tf.py`).
   `META/apkcerts.txt` taugt dafür nicht, denn `sign_target_files_apks` schreibt es nicht um.
   Pakete, die der Build selbst als vorsigniert führt (Vendor-Blobs, SMWAppStore, das
   CTS-Shim-APEX), bleiben bewusst unverändert. Im Test: 218 Pakete, davon 29 vorsigniert,
   0 Funde.
3. Der Public Key in `vbmeta.img` ist `avb_pkmd.bin`.

Builds mit Testschlüsseln gibt es nur noch ausdrücklich mit `--test-keys`.

## Verified Boot und Bootloader wieder sperren

Das Pixel 9a akzeptiert einen eigenen AVB-Root-Schlüssel. Danach lässt sich der Bootloader mit
ViseOS wieder sperren. Das Gerät zeigt beim Start einen **gelben** Hinweis auf ein eigenes OS
und bootet nur noch Images, die mit `avb.pem` signiert sind.

```bash
fastboot flash avb_custom_key avb_pkmd.bin
fastboot flashing lock          # löscht alle Daten
```

Vollständige Schritte stehen auf der Seite [Bauen und Flashen](09-Bauen.md#bootloader-wieder-sperren).

- **Downgrade-Schutz:** Der Rollback-Index ist das Sicherheitspatch-Datum
  (`PLATFORM_SECURITY_PATCH_TIMESTAMP`). Bei gesperrtem Bootloader lässt sich kein älterer Build
  installieren.
- **Fingerabdruck prüfen:** Die SHA-256-Summe von `avb_pkmd.bin` steht in `FLASHEN.txt` jedes
  Release-Ordners und in der Ausgabe von `make-release-keys.sh`. Vor dem Flashen vergleichen.

## Umstieg von Testschlüsseln

Geräte mit einem Testschlüssel-Build nehmen kein Release-OTA an, denn ihr `otacerts.zip` enthält
den testkey. Außerdem passen ihre App-Daten nicht zu den neuen Platform-Signaturen. Der Umstieg
braucht deshalb **einmal eine Neuinstallation mit Wipe**. Danach laufen alle Updates per OTA.
