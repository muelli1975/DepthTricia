# DepthTricia

DepthTricia wandelt einzelne 2D-Fotos oder Bildordner anhand von Tiefenkarten
in Stereo-3D um. Oberfläche, Scheinfenster, Vorhänge, SBS-/Anaglyphenausgabe
und Metadatenübernahme stammen aus SplatTricia.

**Entwicklungsstand — noch kein geprüfter Windows-Release.**

Unterstützte Modelle: Depth Anything V2 Small, Depth Anything 3 Mono Large
und optional Depth Pro. Stereo-Erzeugung: `mlbw_l2_inpaint` mit
`light_inpaint_v1`. Berechnung auf CPU oder NVIDIA/CUDA.

Standard: 15‰ Deviation, Scheinfensterlage 100%, Edge Fix horizontal 2 /
vertikal 1 und Tiefenauflösung 1218 bei Depth Anything. Depth Pro verwendet
seine eigene Modellauflösung. Presets ermöglichen Modellstandard, 1218,
2048 und eigene Tiefenauflösungen sowie eigene Edge-Fix-Werte.

Modelle liegen sichtbar im Ordner `models`. Fehlende Modelle werden nur nach
ausdrücklicher Bestätigung heruntergeladen. Vorhandene Modelle funktionieren
offline, ohne Konto, Token, Netzwerkprüfung oder externen Modellcache.

Ausgaben: `sbs`, `anaglyph` und `_temp` mit wiederverwendbaren Tiefenkarten.
Geänderte Stereo-Einstellungen benötigen keine neue Tiefenschätzung.

[Build und Quellcodebetrieb](BUILD.md) · [Entwicklungsstand](DEVELOPMENT.md) ·
[Drittanbieter und Lizenzen](THIRD_PARTY.md)
