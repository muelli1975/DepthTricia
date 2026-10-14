# DepthTricia 1.0

[English](README.md)

DepthTricia ist ein lokales Windows-Programm, das einzelne 2D-Fotos oder Bildordner in Stereo-3D umwandelt. Aus jedem Foto entstehen ein paralleles Side-by-Side-Stereobild (SBS) und eine Farb- oder Graustufen-Anaglyphe.

Die Tiefenschätzung verwendet **Depth Anything V2 Small**, **Depth Anything 3 Mono Large** oder **Depth Pro**. Oberfläche, Stereoregler und Metadatenübernahme orientieren sich an SplatTricia. Die Oberfläche ist auf Deutsch und Englisch verfügbar.

Die Verarbeitung läuft lokal, ohne Konto, Cloud oder Tracking. Fehlende Laufzeitpakete oder Modelle werden nur nach Bestätigung installiert oder heruntergeladen. Nach der Einrichtung funktioniert die Verarbeitung offline.

[![DepthTricia 1.0 – Benutzeroberfläche](docs/Screenshots/DepthTricia.png)](docs/Screenshots/DepthTricia.png)

[DepthTricia 1.0 herunterladen](https://github.com/muelli1975/DepthTricia/releases/tag/v1.0)

## Voraussetzungen und Installation

- Windows mit 64 Bit.
- Die Berechnung ist auf der CPU möglich; eine kompatible NVIDIA-Grafikkarte mit aktuellem Treiber ermöglicht CUDA-Beschleunigung.
- Das portable Paket benötigt keine separate Python-Installation und kein CUDA-Toolkit.

`DepthTricia_1.0.zip` herunterladen und entpacken, anschließend `DepthTricia.exe` starten. DA2 und DA3 sind im Haupt-ZIP enthalten. Vor der ersten Verarbeitung fragt das Programm, bevor fehlende Pakete installiert oder heruntergeladen werden.

Für eine Offline-Installation **alle sechs ZIP-Dateien desselben Releases** in einen Ordner herunterladen. Nur `DepthTricia_1.0.zip` entpacken; die übrigen fünf ZIPs neben dem entpackten Ordner `DepthTricia` liegen lassen. Sie enthalten vier Laufzeitpakete und das originale Apple-Depth-Pro-Modell. Lokale Pakete werden zuerst verwendet. Archive und installierte Dateien werden anhand ihrer Prüfsummen geprüft; jedes ZIP ist kleiner als 2 GiB.

Die Modelle liegen sichtbar im Ordner `models`. Vorhandene Modelle werden ohne Netzwerkprüfung, Konto, Token oder Abhängigkeit vom Hugging-Face-Cache geladen.

## Einstieg

1. Ein Einzelbild oder einen Bildordner auswählen.
2. **Unterordner im Input-Ordner verwenden** aktivieren oder einen eigenen Ausgabeordner auswählen.
3. Ein Preset wählen. Für CPU-Berechnung **CPU** verwenden.
4. Deviation und Scheinfensterlage nach Bedarf einstellen.
5. Optional Graustufen-Anaglyphen, **Originalgröße ausgeben** oder **Tiefenkarte als PNG speichern** wählen.
6. Auf **Start** klicken.

Modell, Auflösung, Berechnungsgerät und Edge Fix bleiben neben der Presetliste sichtbar. **Abbrechen** fordert den Abbruch an; der aktuelle Verarbeitungsschritt muss gegebenenfalls zunächst beendet werden.

## Modelle und Presets

Presets wählen Tiefenmodell, Berechnungsgerät, Auflösung und Edge Fix gemeinsam.

| Preset | Modell | Tiefenauflösung | Berechnung |
| --- | --- | --- | --- |
| Standard | DA3 Mono Large | 1218 | Automatisch |
| CPU | DA2 Small | Modellstandard: 518 | CPU |
| Schnell | DA3 Mono Large | Modellstandard: 504 | Automatisch |
| Fein | DA3 Mono Large | 2048 | Automatisch |
| Depth Pro | Depth Pro | Nativ: intern 1536 × 1536 | Automatisch |

Alle mitgelieferten Presets verwenden Edge Fix **horizontal 2 / vertikal 1**. **Automatisch** wählt CUDA, wenn verfügbar, andernfalls die CPU. Eigene Presets speichern Modell, Berechnungsgerät, Auflösung und Edge Fix gemeinsam. Depth Anything erlaubt eigene Auflösungen von 196 bis 4096 und rundet intern auf sein 14-Pixel-Raster auf; aus 2048 wird 2058. Die interne Auflösung von Depth Pro bleibt fest.

DA3 mit hoher Auflösung, Depth Pro und Inpainting in Originalgröße benötigen mehr Zeit und Speicher. Nach einem Speicherfehler werden weder Einstellungen noch Berechnungsgerät automatisch reduziert oder gewechselt.

## Stereoregler

**Deviation** bestimmt den horizontalen Tiefenumfang; Standard sind **15‰**. Die **Scheinfensterlage** verteilt diese Tiefe relativ zur Bildebene; Standard sind **100%**.

Beim zusätzlichen Rückversatz wird die gesamte Szene hinter das Scheinfenster verschoben. Dabei entstehende Randlücken werden automatisch gefüllt. Der Rückversatz ist nur bei Scheinfensterlage 100% verfügbar.

Die **Vorhänge des schwebenden Scheinfensters** maskieren Randbereiche. Nahpunktanzeige und Reglerverhalten entsprechen SplatTricia: Wertebereiche, Schrittweiten, Symmetrie und gegenseitige Sperren bleiben erhalten. Die Nahpunktanzeige beschreibt die Szene anhand von Deviation und Scheinfensterlage vor dem zusätzlichen Rückversatz und den Vorhängen.

Die automatische 2D-zu-3D-Umwandlung bleibt eine Schätzung. Gerade für Projektion sollten Tiefenwirkung, Scheinfensterlage und Bildränder visuell geprüft werden.

## Ausgabe und wiederverwendbare Tiefenkarten

Der gewählte Ausgabeordner enthält:

| Ordner | Inhalt |
| --- | --- |
| `sbs` | Parallele Side-by-Side-Bilder als JPEG |
| `anaglyph` | Farb- oder Graustufen-Anaglyphen als JPEG |
| `_temp` | Wiederverwendbare Tiefenkarten und Cache-Daten |
| `depth_maps` | Optionale relative Tiefenkarten als 16-Bit-PNG |

SBS verwendet JPEG-Qualität **95**, Anaglyphen **90**; beide verwenden **4:4:4** ohne Farbunterabtastung. Geeignete Metadaten der Quelldateien werden, soweit technisch möglich, in die JPEG-Ausgaben übernommen.

Jedes Halbbild wird standardmäßig auf 2160 Pixel Höhe begrenzt; kleinere Fotos werden nicht vergrößert. **Originalgröße ausgeben** erhält die vollständigen, korrekt ausgerichteten Bildabmessungen.

**Tiefenkarte als PNG speichern** exportiert die berechnete relative Tiefenkarte ohne Größenänderung: nah ist weiß, fern ist schwarz. Die Werte sind relativ und keine Entfernungen in Metern. Der separate `.npy`-Cache bewahrt normalisierte 32-Bit-Gleitkommawerte für die Berechnung.

Mit **Tiefenkarten wiederverwenden** lassen sich Stereoeinstellungen ohne erneute Tiefenschätzung ändern. Änderungen an Quelldatei, Tiefenmodell, Tiefenauflösung oder Edge Fix machen den jeweiligen Cache ungültig. **Temporäre Dateien löschen** entfernt `_temp`; fertige Bilder bleiben erhalten.

Vorhandene Ausgabebilder werden ersetzt. **Dateiname um Einstellungen ergänzen** erhält bewusst benannte Varianten einschließlich Modellangabe, zum Beispiel `bild_DA3MonoLarge_r1218_d15_w100_o0_sbs.jpg`. Der Wert hinter `r` ist die gewählte Tiefenauflösung vor der internen Rasterrundung; bei Modellstandard steht dort 518 für DA2 oder 504 für DA3, bei Depth Pro immer `r1536`.

Eigene Presets, Sprache, Ordner und die beiden Ausgabeoptionen werden lokal in `settings.json` im Programmordner gespeichert. Diese Datei bei Updates erhalten. Die Stereoregler starten mit ihren Standardwerten.

## Quellcode und langfristige Nutzung

Das Repository enthält den Anwendungsquellcode und Build-Hinweise. [BUILD.md](BUILD.md) beschreibt Quellcodebetrieb und portable Builds; [DEVELOPMENT.md](DEVELOPMENT.md) dokumentiert den Prüfstand. Die Stereo-Erzeugung verwendet `mlbw_l2_inpaint` mit `light_inpaint_v1` aus iw3.

Die Windows-Veröffentlichung hat Quellcode-Prüfungen und Tests der fertigen EXE bestanden, darunter Offline-Verarbeitung mit DA2 auf der CPU, Inpainting und Szenen-Rückversatz. Dies ist keine vollständige Prüfung der Depth-Pro- oder CUDA-Tiefenschätzung auf jeder Hardware.

Ziel ist, DepthTricia für spätere Weiterentwicklung und die stereoskopische Gemeinschaft verständlich und nutzbar zu halten. Aktive Pflege, Support, Bearbeitung von Issues oder Prüfung von Pull Requests können nicht zugesichert werden.

## Lizenz

Copyright Christoph Müller. Eigener DepthTricia-Quellcode und eigene Dokumentation stehen unter der **MIT-Lizenz**. Drittkomponenten und Modellgewichte behalten ihre jeweiligen Lizenzen, einschließlich der Apple-Bedingungen für Depth Pro.

Siehe [LICENSE.txt](LICENSE.txt) und [THIRD_PARTY.md](THIRD_PARTY.md).
