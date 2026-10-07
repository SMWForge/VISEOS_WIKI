# 6. Werkzeuge

[← System-Apps](05-System-Apps.md) · [Weiter: OTA-Updates →](07-OTA-Updates.md)

| Werkzeug | Ort | Zweck |
|---|---|---|
| [`build.sh`](#buildsh) | `vendor/viseos/scripts/` | einziger Einstieg zum Bauen |
| [`vise-app.sh`](#vise-appsh) | `/root/aosp-tools/` | Apps aus GitHub klonen/aktualisieren und einbinden |
| [`build_and_update.sh`](#build_and_updatesh) | `/root/aosp-tools/` | bauen, signieren, OTA erzeugen und veröffentlichen |
| [`make-release-keys.sh`](#make-release-keyssh) | `/root/aosp-tools/` | Release-Schlüssel erzeugen |
| [`viseupdate-server`](07-OTA-Updates.md#der-ota-server) | `/root/aosp-tools/viseupdate-server/` | Debian-Paket für den OTA-Server |
| `prepare-blobs.sh`, `prepare-kernel.py` | `vendor/viseos/scripts/` | siehe [Blobs](04-Blobs.md), [Kernel](03-Geraet-tegu.md#kernel) |

## build.sh

```bash
vendor/viseos/scripts/build.sh            # voller Build
vendor/viseos/scripts/build.sh nothing    # nur Analyse (Soong/Kati), schnell
vendor/viseos/scripts/build.sh ViseUpdate selinux_policy   # einzelne Ziele
```

- Ruft `lunch viseos_tegu-cp2a-userdebug` auf und dann `m <ziele>`.
- **Log:** `out/viseos-build-<datum>.log`.
- **Ausgabe am Ende:** Fehlerzeilen, Logende und Exit-Code.
- **Regel:** `lunch` nie in einer Pipe, immer über dieses Script bauen.

## vise-app.sh

Klont eine App aus GitHub (`git@github.com-smwforge:SMWForge/<repo>.git`) oder aktualisiert sie
per `git pull --ff-only`. Danach bindet es die App ins OS ein.

```bash
/root/aosp-tools/vise-app.sh -addorupdate <repo> <true|false> [--rebuild] [--check]
```

| Argument | Bedeutung |
|---|---|
| `true` | privilegierte System-App: `/system_ext/priv-app`, Platform-Key, Privapp-Allowlist |
| `false` | normale vorinstallierte App: `/product/app`, nicht privilegiert, ohne Platform-Key (signierte APK bleibt vorsigniert, unsignierte bekommt den Default-Dev-Key) |
| `--rebuild` | APK auch ohne neuen Commit neu bauen |
| `--check` | danach `build.sh nothing` |

Das Script erkennt drei Repo-Typen:

| Typ | Erkennung | Ablage | Einbindung |
|---|---|---|---|
| Gradle mit `aosp/`-Ordner | `aosp/Android.bp` | Klon in `/root/VISEOS_DEV/Vise/<repo>`, APK + Dateien nach `vendor/viseos/apps/<Modul>/` | die `Android.bp` des Repos (bei `true`), sonst erzeugt |
| Gradle ohne `aosp/` | `gradlew` | wie oben | `Android.bp` wird erzeugt |
| Soong-Quellprojekt | `Android.bp` im Root | `packages/apps/<repo>` | `*.mk` des Repos per `inherit-product`, sonst `PRODUCT_PACKAGES` |

Dabei passiert automatisch:

- **APK bauen:** über `aosp/update_apk.sh` bzw. `./gradlew :app:assembleRelease`, aber nur bei
  neuem Commit.
- **uses-library:** Die `uses-library`-Einträge der APK werden in die `Android.bp` übernommen
  (`uses_libs` / `optional_uses_libs`).
- **Privapp-Allowlist:** Bei `true` prüft das Script sie gegen die privilegierten Rechte aus
  `frameworks/base/core/res/AndroidManifest.xml`. Fehlt ein Recht, bricht es ab, denn das Gerät
  würde nicht booten. Fehlt die Allowlist ganz, erzeugt es eine.
- **Ins Produkt:** Steht das Modul schon in einem Makefile unter `vendor/viseos`, bleibt es dort.
  Sonst kommt ein markierter Block nach `vendor/viseos/config/vise-apps.mk`.
- **Zustand:** wird pro App in `vendor/viseos/apps/<Modul>/.vise-app` festgehalten (Repo, Commit,
  Modus, kopierte Dateien). Dateien, die nicht mehr gebraucht werden, entfernt das Script wieder.
- **Protokoll:** Jede Änderung landet automatisch in `vendor/viseos/NOTES.md`.
- **Lokale Änderungen im Klon:** Hat ein Klon lokale Änderungen, bricht das Script ab, statt sie
  zu überschreiben.

Umgebungsvariablen: `AOSP_DIR`, `VISE_SRC_DIR`, `VISE_GIT_BASE`, `ANDROID_HOME`.

## build_and_update.sh

Bauen, signieren und als OTA veröffentlichen, in einem Schritt. Ausführlich auf der Seite
[OTA-Updates](07-OTA-Updates.md#veröffentlichen-mit-build_and_updatesh).

```bash
/root/aosp-tools/build_and_update.sh --version 1.0.0 --changelog CHANGELOG.md --incremental
```

## make-release-keys.sh

Erzeugt alle Release-Schlüssel nach `/root/.viseos-keys`. Vorhandene Schlüssel überschreibt es
nie, es ergänzt nur fehlende, z. B. für neue APEX-Module. Details auf der Seite
[Signierung](08-Signierung.md).
