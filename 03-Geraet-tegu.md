# 3. Gerät tegu: Anpassungen

[← Quellbaum](02-Quellbaum-und-Aufbau.md) · [Weiter: Blobs →](04-Blobs.md)

Die Gerätebäume stammen von LineageOS `lineage-24.0`. ViseOS nutzt die **AOSP-Variante**
`aosp_tegu.mk` und entfernt alles, was `vendor/lineage` oder `hardware/lineage` voraussetzt.
Die Änderungen in den Lineage-Repos sind bewusst klein gehalten und eignen sich als Patches.

## Kernel

**Problem:** `device/google/tegu-kernels/6.1` enthält nur Ladelisten. LineageOS baut den Kernel
über `vendor/lineage` (`kernel.mk`), das es in ViseOS nicht gibt. Der Build brach deshalb ab mit
`device/google/tegu-kernels/6.1/gzvm.ko … missing`.

**Lösung:** Kernel-Artefakte aus dem CP2A-Factory-Image als Prebuilts verwenden.

| | |
|---|---|
| Werkzeug | `vendor/viseos/scripts/prepare-kernel.py` |
| Eingabe | Factory-Zip `tegu-cp2a.260805.005-factory-*.zip` |
| Ausgabe | `vendor/viseos/prebuilts/kernel/tegu/6.1/` (~137 MB) |
| Inhalt | `boot.img` (GKI, Linux 6.1.157-android14-11), `dtbo.img`, `tegu.dtb` (aus vendor_kernel_boot), **328 Kernelmodule** aus vendor_kernel_boot-Ramdisk, `vendor_dlkm.img` und `system_dlkm.img`, Ladelisten, Blocklisten und `init.insmod.tegu.cfg` |
| Nicht übernommen | 16k-Seitenmodus |

Die Ladelisten sind inhaltlich identisch zu denen in `tegu-kernels` (geprüft). Nach einem
Update auf ein neues Factory-Image muss `prepare-kernel.py` erneut laufen.

Eingebunden wird der Kernel über das Produkt:

```make
# vendor/viseos/products/tegu/viseos_tegu.mk
TARGET_KERNEL_DIR := vendor/viseos/prebuilts/kernel/tegu/6.1
```

Die Version steht fest im Pfad, weil `TARGET_LINUX_KERNEL_VERSION` erst in `device-tegu.mk` gesetzt
wird. Das wertet der Build per `inherit-product` erst **nach** `viseos_tegu.mk` aus.

**Ergebnis:** `boot.img` und `dtbo.img` sind im Nutzinhalt identisch zu Stock (per `cmp`
geprüft). Nur der AVB-Footer wird vom Build neu erzeugt und mit dem ViseOS-Schlüssel signiert
(siehe [Signierung](08-Signierung.md)).

## Patches an den Lineage-Gerätebäumen

### `device/google/tegu/device-tegu.mk` (1 Zeile)

```diff
-TARGET_KERNEL_DIR := …
+TARGET_KERNEL_DIR ?= …
```

Ohne diese Änderung überschreibt `device-tegu.mk`, das später ausgewertet wird, die
Kernel-Einstellung des Produkts.

### `device/google/zumapro/common.mk` (10 Zeilen entfernt)

Entfernt wurden zwei Blöcke:

| Block | Inhalt | Warum entfernt |
|---|---|---|
| `# Lineage Health` | `include hardware/google/pixel/lineage_health/device.mk` + 3× `soong_config` `lineage_health` | Der Typ `hal_lineage_health_default` kommt aus `hardware/lineage`. Ohne ihn bricht checkpolicy ab (`unknown type hal_lineage_health_default`, Build stoppte bei 66 %). |
| `# Touch` | `include hardware/google/pixel/touch/device.mk` | gehört zum Lineage-Touch-HAL (`vendor.lineage.touch-service.pixel`). `hardware/google/pixel/touch` ist ohnehin ausgeblendet. |

**Funktionsverlust:** Lineage-Ladebegrenzung (Akkuschonung über den Health-HAL) und der
Touch-Empfindlichkeitsmodus (Handschuhmodus). Siehe [Offene Punkte](10-Offene-Punkte.md).

Geprüft mit `build.sh selinux_policy` (grün).

### Ausgeblendet per `.find-ignore`

- `hardware/google/pixel/touch`: Lineage-Touch-HAL
- `device/google/zumapro/parts`: LineagePARTS (Einstellungs-App des Lineage-SDK)

## Firmware (Bootloader/Radio)

Die Blob-Extraktion trägt die Firmware-Partitionen des Pixel ins Build ein:

- `vendor/google/tegu/BoardConfigVendor.mk`: `AB_OTA_PARTITIONS += abl bl1 bl2 bl31 gcf gsa gsa_bl1 ldfw modem pbl tzsw`
- `vendor/google/tegu/Android.mk`: `$(call add-radio-file-sha1-checked,radio/<fw>.img,…)`

Damit wären Bootloader und Modem über `target_files/RADIO/` in **jedem OTA-Payload** gelandet.
Das widerspricht der Projektregel „keine Firmware in Images oder OTA“.

`vendor/viseos/scripts/strip-firmware.py` entfernt beides. Es arbeitet idempotent und läuft am
Ende von `prepare-blobs.sh` sowie vor jedem `build_and_update.sh`. Die Originale liegen als
`*.with-firmware` daneben. `build_and_update.sh` prüft zusätzlich vor jeder Veröffentlichung,
dass `META/ab_partitions.txt` keine Firmware enthält.

**OTA-Payload von ViseOS:** `boot dtbo init_boot product pvmfw system system_dlkm system_ext
vbmeta vbmeta_system vbmeta_vendor vendor vendor_boot vendor_dlkm vendor_kernel_boot`

**Folge:** Die Firmware bleibt auf dem Stand, der per Google-Factory-Image geflasht wurde
(`CP2A.260805.005`). Sie muss auf **beiden** A/B-Slots stehen, siehe [Bauen und Flashen](09-Bauen.md).

## SEPolicy

- Keine Änderungen an `system/sepolicy`.
- ViseUpdate bringt eigene Regeln in `packages/apps/ViseUpdate/sepolicy` mit
  (`SYSTEM_EXT_PRIVATE_SEPOLICY_DIRS`, siehe [OTA](07-OTA-Updates.md)).
- Die entfernten Lineage-Blöcke (Health, Touch) beseitigen die einzigen Policy-Fehler.
