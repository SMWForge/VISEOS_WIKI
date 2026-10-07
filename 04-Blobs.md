# 4. Proprietäre Blobs

[← Gerät tegu](03-Geraet-tegu.md) · [Weiter: System-Apps →](05-System-Apps.md)

## Quelle

| | |
|---|---|
| Stand | `CP2A.260805.005` (Pixel-9a-Factory-Image) |
| Ziel | `vendor/google/tegu` (`tegu-vendor.mk`, `Android.bp`, `Android.mk`, `BoardConfigVendor.mk`, `proprietary/`) |
| Werkzeug | LineageOS `extract-utils` (nur für die Extraktion) |
| Stock-`vendor.img` | Referenz für fehlende Bibliotheken |

## Nacharbeit: `prepare-blobs.sh`

Nach **jeder** Blob-Extraktion aus dem AOSP-Root ausführen:

```bash
vendor/viseos/scripts/prepare-blobs.sh
```

Das Script ruft der Reihe nach auf:

| Schritt | Script | Was es macht | Warum |
|---|---|---|---|
| 1 | `fix-blobs.py` | baut `rust_prebuilt_*` in `vendor/google/tegu/Android.bp` zu `cc_prebuilt_*` um. Die `*.dylib.so`-Abhängigkeiten kommen als `viseos_rust_*`-Module aus dem Stock-`vendor.img`, außerdem erzeugt es `products/tegu/rust-blobs.mk`. | AOSP verbietet Rust-Prebuilts außerhalb von `/system`. |
| 2 | `add-stock-libs.py libjson` | übernimmt fehlende Vendor-Libs 1:1 aus dem Stock-`vendor.img` | Lineage baut `libjson` aus Quellcode, in ViseOS gibt es diese Quellen nicht (Regel 2) |
| 3 | `filter-rust-blobs.py` | entfernt die `viseos_rust_*`-Module, die AOSP selbst für vendor baut (Liste `rust-from-source.txt`) | Soong erzeugt für **jedes** definierte Modul Install-Regeln, sonst kollidieren z. B. `vendor/lib64/libaho_corasick.dylib.so` aus AOSP und aus Stock |
| 4 | `strip-firmware.py` | entfernt Firmware aus `AB_OTA_PARTITIONS` und die `add-radio-file`-Zeilen | Regel 5: keine Firmware in Images/OTA (siehe [Gerät](03-Geraet-tegu.md#firmware-bootloaderradio)) |

AOSP baut diese Rust-Bibliotheken selbst, deshalb kommen sie **nicht** aus Stock
(`rust-from-source.txt`):

`libaho_corasick libandroid_logger libbitflags libenv_filter liblibc liblog_rust libmemchr libnix
libregex_automata libregex libregex_syntax librustutils libstd`

## Hinweise

- `vendor/google/tegu` ist generiert. Eigene Änderungen gehören in die Scripts in
  `vendor/viseos/scripts`, nicht von Hand in die generierten Dateien. Sonst sind sie nach der
  nächsten Extraktion weg.
- Die Vendor-APKs aus den Blobs sind vorsigniert (`PRESIGNED`) und werden beim
  [Signieren](08-Signierung.md) nicht verändert.
- Bei einem neuen Factory-Image: Blobs neu extrahieren, `prepare-blobs.sh`,
  `prepare-kernel.py`, dann bauen.
