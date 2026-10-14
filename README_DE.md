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
Hinter Modellstandard steht der Wert: 518 bei DA2, 504 bei DA3.
Depth Pro verwendet intern fest 1536×1536 Pixel.

Die Ausgabe wird standardmäßig auf 2160 Pixel Höhe begrenzt; kleinere Fotos
werden nicht vergrößert. **Ausgabe in Originalgröße** erhält die vollständigen,
korrekt ausgerichteten Bildabmessungen. **Tiefenkarte speichern** erzeugt
zusätzlich eine 16-Bit-Graustufen-PNG im Ordner `depth_maps`: nah ist hell,
fern ist dunkel. Die berechnete Kartenauflösung bleibt erhalten; die Werte
sind relativ und keine Entfernungsangaben in Metern.
Beide Checkboxen starten ausgeschaltet und merken sich ihre Auswahl.
Eigene Tiefen-Presets und diese Optionen stehen lokal in `settings.json`
im Programmordner; diese Datei bei einem Update erhalten. Bei aktivierter
Ergänzung der Einstellungen im Dateinamen steht auch das Modell darin,
z. B. `bild_DA3MonoLarge_d15_w100_o0_sbs.jpg`.

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
Die `.npy`-Dateien unter `_temp` enthalten die normalisierten Tiefenwerte mit
32-Bit-Gleitkommagenauigkeit als Rechencache. Die optionale PNG ist davon
getrennt und zum Betrachten oder Weiterverwenden gedacht.

[Build und Quellcodebetrieb](BUILD.md) · [Entwicklungsstand](DEVELOPMENT.md) ·
[Drittanbieter und Lizenzen](THIRD_PARTY.md)
