# DepthTricia

DepthTricia wandelt einzelne 2D-Fotos oder Bildordner anhand von Tiefenkarten
in Stereo-3D um. Oberfläche, Scheinfenster, Vorhänge, SBS-/Anaglyphenausgabe
und Metadatenübernahme stammen aus SplatTricia.

**Entwicklungsstand — noch kein geprüfter Windows-Release.**

Unterstützte Modelle: Depth Anything V2 Small, Depth Anything 3 Mono Large
und Depth Pro. Stereo-Erzeugung: `mlbw_l2_inpaint` mit
`light_inpaint_v1`. Berechnung auf CPU oder NVIDIA/CUDA.

Standard: 15‰ Deviation, Scheinfensterlage 100%, Edge Fix horizontal 2 /
vertikal 1 und Tiefenauflösung 1218 bei Depth Anything. Depth Pro verwendet
seine eigene Modellauflösung. Presets ermöglichen Modellstandard, 1218,
2048 und eigene Tiefenauflösungen sowie eigene Edge-Fix-Werte.

Modelle liegen sichtbar im Ordner `models`. Fehlende Modelle werden nur nach
ausdrücklicher Bestätigung heruntergeladen. Vorhandene Modelle funktionieren
offline, ohne Konto, Token, Netzwerkprüfung oder externen Modellcache.

Ein gemeinsames Windows-Paket wählt automatisch CUDA, wenn verfügbar, sonst
CPU. Große Laufzeitdateien werden als zusätzliche ZIP-Pakete bereitgestellt.
Vor der ersten Verarbeitung fragt DepthTricia, bevor fehlende Pakete
installiert oder heruntergeladen werden. Lokale ZIPs neben dem Programm
werden zuerst verwendet; anschließend funktioniert es offline.
DA2 und DA3 liegen im Haupt-ZIP. Das originale Apple-Depth-Pro-Modell liegt
in `DepthTricia_Models_DepthPro_1.0.zip` und wird nach Bestätigung zusammen
mit den Laufzeitpaketen installiert. Für die Offline-Installation alle sechs
ZIPs desselben Releases in einen Ordner laden, nur `DepthTricia_1.0.zip`
entpacken und die übrigen ZIPs neben dem entpackten Programmordner liegen lassen.

Ausgaben: `sbs`, `anaglyph` und `_temp` mit wiederverwendbaren Tiefenkarten.
Geänderte Stereo-Einstellungen benötigen keine neue Tiefenschätzung.

[Build und Quellcodebetrieb](BUILD.md) · [Entwicklungsstand](DEVELOPMENT.md) ·
[Drittanbieter und Lizenzen](THIRD_PARTY.md)
