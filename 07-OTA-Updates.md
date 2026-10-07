# 7. OTA-Updates

[← Werkzeuge](06-Werkzeuge.md) · [Weiter: Signierung →](08-Signierung.md)

## Überblick

```
Build-Rechner                                   OTA-Server ota.smwforge.global         Gerät
build_and_update.sh                             /srv/viseupdate/                         ViseUpdate
  build.sh target-files-package otatools          files/tegu/viseos-tegu-1.0.0.zip  <──  Download (Range, fortsetzbar)
  sign_target_files_apks (Release-Schlüssel)      api/v1/tegu/stable.json           <──  GET …/api/v1/tegu/stable.json
  ota_from_target_files -k releasekey     ──>   viseupdate-publish                        update_engine: A/B-Installation
```

## Der Client: ViseUpdate

- **Erscheint unter:** *Einstellungen → System → Systemupdate*.
- **Prüft periodisch** per JobScheduler, Standard alle 24 h.
- **Lädt im Hintergrund**, fortsetzbar, und prüft dabei die SHA-256-Summe.
- **Prüft vor der Installation:**
  - OTA-Signatur gegen `otacerts.zip`
  - `ota-type=AB`
  - Gerät
  - bei inkrementellen Paketen den Quell-Build
  - Akkustand (≥ 30 % ohne Ladegerät)
- **Installiert** über `android.os.UpdateEngine` auf dem inaktiven Slot. Danach Neustart, und
  nach dem Start meldet die App Erfolg oder Rollback.
- **Gibt Platz frei:** Das Zip wird nach der Installation gelöscht, damit `/data` für den
  Snapshot-Merge frei ist.

Konfiguration in ViseOS:

```make
# vendor/viseos/config/common.mk – muss VOR vise-apps.mk stehen (viseupdate.mk nutzt ?=)
VISEUPDATE_SERVER_URL := https://ota.smwforge.global/api/v1/{device}/{channel}.json
```

Daraus wird `ro.viseupdate.server_url` in `system_ext/etc/build.prop`. Für das Pixel 9a fragt
das Gerät also `https://ota.smwforge.global/api/v1/tegu/stable.json` ab.

| Platzhalter | Wert |
|---|---|
| `{device}` | `ro.product.device` (`tegu`) |
| `{channel}` | gewählter Kanal (`stable`, `beta`) |
| `{incremental}` | `ro.build.version.incremental` des laufenden Builds |

Weitere Einstellungen (per Overlay oder Property) beschreibt die README von ViseUpdate, z. B.
Kanäle, Auto-Download, Streaming-Installation und Mindest-Akkustand.

**SELinux** (`packages/apps/ViseUpdate/sepolicy`, über `SYSTEM_EXT_PRIVATE_SEPOLICY_DIRS`):

- `system_app` darf `ota_package_file` (`/data/ota_package`) lesen und schreiben, und es darf
  `update_engine_service` finden.
- Die Binder-Calls in beide Richtungen und das Lesen durch `update_engine` stehen schon in der
  Plattform-Policy.

## Server-API

Es reicht eine **statische JSON-Datei pro Gerät und Kanal**:

```json
{
  "response_version": 1,
  "updates": [
    {
      "id": "<sha256>",
      "version": "1.0.0",
      "build_incremental": "viseos.20261007.101855",
      "timestamp": 1791360392,
      "type": "full",
      "url": "https://ota.smwforge.global/files/tegu/viseos-tegu-1.0.0.zip",
      "size": 1380944680,
      "sha256": "…",
      "changelog": "# Neu\n- …",
      "payload": { "offset": 0, "size": 0, "properties": ["FILE_HASH=…"] }
    }
  ]
}
```

- Als Update gilt nur ein Eintrag mit größerem `timestamp` (`ro.build.date.utc`) als der
  laufende Build.
- Inkrementelle Pakete (`"type": "incremental"`, `source_incremental`) bietet der Client nur an,
  wenn `source_incremental` genau zum laufenden Build passt. Bei gleichem Ziel nimmt er bevorzugt
  das inkrementelle Paket.
- `404`/`204` auf die JSON heißt „kein Update“.
- Downloads brauchen `Range`-Support (`206`). Bei `416` startet der Client neu.

## Der OTA-Server

Debian-Paket **`viseupdate-server`** (Quelle `/root/aosp-tools/viseupdate-server/`):

| Bestandteil | Inhalt |
|---|---|
| `viseupdate-server.service` | systemd-Dienst. Python-Server ohne externe Abhängigkeiten (nur Standardbibliothek), lauscht auf `127.0.0.1:8470`, nur lesend, `DynamicUser`, gehärtet |
| `/etc/nginx/sites-available/viseupdate-server` | vHost `ota.smwforge.global` → Dienst (`proxy_buffering off`). Wird bei der Erstinstallation aktiviert, wenn nginx da ist. |
| `/usr/bin/viseupdate-publish` | OTA-Zip ablegen, Kanal-JSON pflegen (beides atomar), Gerät im Paket prüfen, `--keep`/`--prune` |
| `/etc/default/viseupdate-server` | `VISEUPDATE_ROOT`, `VISEUPDATE_BASE_URL`, Port |
| `/srv/viseupdate/` | `api/v1/<gerät>/<kanal>.json`, `files/<gerät>/*.zip` (bleibt bei `purge` erhalten) |

Der Server liefert:

| Anfrage | Antwort |
|---|---|
| `GET/HEAD /api/v1/<gerät>/<kanal>[.json][?…]` | die JSON, sonst `404` |
| `GET/HEAD /files/<pfad>` | `Range`/`206`/`416`, `ETag`, `If-Range` |
| `GET /healthz` | `ok` |

Schutz gegen Path-Traversal: nur saubere Namen, kein `..`, keine versteckten Dateien.

**Einrichtung auf dem Server:**

```bash
sudo apt install ./viseupdate-server_1.0.0_all.deb
sudo certbot --nginx -d ota.smwforge.global     # HTTPS ist Pflicht
curl https://ota.smwforge.global/healthz          # ok
```

DNS: `ota.smwforge.global` muss auf den Server zeigen. Ändert certbot den vHost, fragt dpkg bei
späteren Updates nach. Dann „behalten“ wählen.

**Paket bauen und testen** (Build-Rechner):

```bash
/root/aosp-tools/viseupdate-server/build-deb.sh   # dist/viseupdate-server_<version>_all.deb
/root/aosp-tools/viseupdate-server/test.sh        # 41 Tests: Publish, HTTP, HTTPS, Range, Traversal
```

`gen_update_json.py` übernimmt `build-deb.sh` aus `packages/apps/ViseUpdate/tools`. Nach einem
Update von ViseUpdate also das Paket neu bauen.

## Veröffentlichen mit build_and_update.sh

```bash
/root/aosp-tools/build_and_update.sh --version 1.0.0 --changelog CHANGELOG.md --incremental
```

| Schritt | Was passiert |
|---|---|
| 1. Vorabprüfung | Release-Schlüssel vorhanden, Server per SSH erreichbar, `viseupdate-publish` installiert, ≥ 30 GB frei, keine Firmware im Build |
| 2. Build | `build.sh target-files-package otatools` mit eindeutiger `BUILD_NUMBER=viseos.JJJJMMTT.HHMMSS` |
| 3. Firmware-Prüfung | keine Bootloader-/Radio-Partition in `META/ab_partitions.txt`, keine Images in `RADIO/` |
| 4. Signieren | `sign_target_files_apks` mit `/root/.viseos-keys`, danach automatische Prüfung (siehe [Signierung](08-Signierung.md)) |
| 5. OTA | `ota_from_target_files -k releasekey`: volles Paket, mit `--incremental` zusätzlich ein Delta zum zuletzt veröffentlichten Build (nur bei gleichen Schlüsseln) |
| 6. Images (optional `--images`) | Fastboot-Paket für die Erstinstallation + `avb_pkmd.bin` + `FLASHEN.txt` in `release/<gerät>-<version>/` |
| 7. Veröffentlichen | per SSH (`rsync --partial`, dann `viseupdate-publish`), lokal oder als Staging-Ordner |
| 8. Archiv | signierte target_files nach `ota-archive/` (die letzten 3), Basis für das nächste Delta |

| Option | Bedeutung |
|---|---|
| `--target ssh` | Standard: `root@ota.smwforge.global` (anders: `--server` oder `OTA_SERVER=` in `build_and_update.conf`) |
| `--target local` | Server läuft auf dem Build-Rechner |
| `--target stage` | nur Ordner erzeugen. Hochladen: erst `files/`, dann `api/` per rsync |
| `--check` | nur Vorabprüfung |
| `--no-build` | vorhandene target_files verwenden |
| `--test-keys` | ausdrücklich mit AOSP-Testschlüsseln, **nie für echte Geräte** |

**Warum `BUILD_NUMBER`?** Ohne sie heißt jeder Build `eng.root`
(`ro.build.version.incremental`). Inkrementelle Pakete ließen sich dann keinem Quell-Build
eindeutig zuordnen.

**Größen (gemessen):** volles OTA etwa 1,3 GB. Ein Delta zwischen zwei Builds mit kaum
Änderungen war 188 KB groß.

## Wichtig: Firmware

OTAs von ViseOS enthalten **keine** Firmware, siehe [Gerät](03-Geraet-tegu.md#firmware-bootloaderradio).
Beim A/B-Wechsel startet das Gerät mit der Firmware des anderen Slots. Deshalb muss die
CP2A-Firmware bei der Erstinstallation auf **beide** Slots geflasht werden, siehe
[Bauen und Flashen](09-Bauen.md).
