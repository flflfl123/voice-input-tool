[中文](README_zh.md) | [English](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Русский](README_ru.md) | [Español](README_es.md) | [Français](README_fr.md) | [Deutsch](README_de.md) | [Português](README_pt.md)

# Spracheingabe – Bedienungsanleitung

## 1. Softwareübersicht

Dies ist eine Spracheingabemethode für Windows, die eine Drittanbieter-ASR-API (Spracherkennung) anbindet. Durch Drücken der Tastenkombination wird die Aufnahme gestartet; durch erneutes Drücken wird die Aufnahme gestoppt und der erkannte Text automatisch an der aktuellen Cursorposition eingefügt.

## 2. Kernfunktionen

- Sprach-zu-Text: Aufnahme wird durch eine globale Tastenkombination ausgelöst, das Erkennungsergebnis wird automatisch an der Cursorposition eingefügt
- Mehrere Anbieter unterstützt: OpenAI-kompatibles Format, Doubao-Großmodell und Volcengine – drei ASR-Dienste
- Schwebendes Fenster: Zeigt während der Aufnahme den Echtzeitstatus an (mit dünnem Rahmen in der Themenfarbe), das Ergebnis wird automatisch in die Zwischenablage kopiert und eingefügt
- Verlauf: Speichert automatisch jedes Erkennungsergebnis, unterstützt Absatzeinrückung
- Mehrsprachige Oberfläche: Eingebaute 35 Oberflächensprachen, automatische Auswahl der passendsten Schriftart
- Themenwechsel: Unterstützt helle und dunkle Themen, alle Steuerelement-Farben werden einheitlich aktualisiert
- Schriftgrad-Einstellung: Über Auf-/Ab-Pfeile lässt sich der Schriftgrad (8 ~ 15, Standard 10) einstellen, betrifft nur die Schrift, nicht die Steuerelemente
- Tastenkombination anpassbar: Klick auf „Ändern" öffnet ein Fenster, in dem eine neue Tastenkombination erfasst wird; unterstützt 1 ~ 3 Tasten
- Heißwort-Ersetzung: Seltene Wörter werden in die Heißworttabelle eingetragen und über Phonetik-Fuzzy-Matching erzwungen ersetzt
- Regex-Regel-Ersetzung: Präzise Ersetzung bestimmter Texte durch Gleichungen oder Regex-Regeln
- ITN-Zahlenkonvertierung: Wandelt „十五六个" automatisch in „15~16个" um; unterstützt Bereiche, Daten, Prozentsätze, Brüche usw.; eingebaute Schutzwörter verhindern Fehlkonvertierungen von „一会儿""一样"
- Füllwörter entfernen: Automatisches Entfernen von mündlichen Füllwörtern wie „呃、啊、嗯" (ohne LLM, rein lokale Verarbeitung)
- LLM-Rollenverarbeitung: Wenn das Erkennungsergebnis mit einem Rollennamen beginnt, wird es von der entsprechenden Großmodell-Rolle verarbeitet (Überarbeitung, Übersetzung, kleiner Assistent usw.); Rollendateien werden per AST sicher geparst, nur literale Zuweisungen erlaubt
- Sprachbefehle: Durch Aussprechen von Befehlen wie „撤销""换行""退格" werden die entsprechenden Aktionen automatisch ausgeführt
- Tagebucharchiv: Speichert jede Spracheingabe und jedes Erkennungsergebnis nach Datum
- Autostart: Optionaler automatischer Start beim Hochfahren
- System-Tray: Minimierung in den Tray, Linksklick öffnet das Hauptfenster, Rechtsklick beendet

## 3. Schnellstart

1. Nach dem Programmstart wird die Software standardmäßig in den System-Tray minimiert
2. Linksklick auf das Tray-Symbol öffnet das Hauptfenster
3. Vor der ersten Verwendung auf der Seite „AI-Konfiguration" den ASR-Anbieter und den API-Schlüssel eintragen
4. In einem beliebigen Fenster mit Texteingabe den Cursor an die gewünschte Position setzen
5. `Ctrl+Alt` drücken, um die Aufnahme zu starten (Tray-Symbol wird rot, schwebendes Fenster erscheint)
6. In das Mikrofon sprechen
7. `Ctrl+Alt` erneut drücken, um die Aufnahme zu stoppen
8. Das Erkennungsergebnis wird automatisch an der Cursorposition eingefügt

> Hinweis: Wenn die Tastenkombination ohne konfigurierte API gedrückt wird, zeigt das schwebende Fenster „AI nicht konfiguriert" an – bitte zuerst die Konfiguration abschließen.

## 4. Oberflächenbeschreibung

Das Hauptfenster verfügt links über eine Navigationsleiste mit folgenden Seiten:

- Startseite: Zeigt den Aufnahmestatus und das letzte Erkennungsergebnis an, bietet eine Schaltfläche zum Kopieren
- Protokoll: Zeigt das Laufzeitprotokoll der Software in Echtzeit, inklusive Aufnahme, Erkennung und Nachverarbeitung
- Verlauf: Durchsuchen der bisherigen Erkennungseinträge, unterstützt Kopieren und Absatzeinrückung
- AI-Konfiguration: Eintragen von ASR-Anbieter, API-Adresse und -Schlüssel, Modellname usw.; enthält Schalter für „Textüberarbeitung aktivieren" und „LLM-Rollen aktivieren"
- Werkzeugkasten: Zentrale Schalter für die einzelnen Text-Nachverarbeitungsfunktionen (Endsatzzeichen entfernen, ITN, Füllwörter entfernen, Heißwörter, Regex-Regeln, Tagebucharchiv)
- Einstellungen: Allgemeine Einstellungen, einschließlich Tastenkombination, Thema, Schriftgrad, Oberflächensprache, Autostart, schwebendes Fenster usw.

## 5. Detaillierte Einstellungen

### ASR-bezogen (Seite AI-Konfiguration)

| Einstellung | Funktion |
| --- | --- |
| ASR-Anbieter | Auswahl des Spracherkennungsdienstes: openai_compatible (OpenAI-kompatibel), doubao (Doubao), volcengine (Volcengine) |
| base_url | Basisadresse der OpenAI-kompatiblen API |
| api_key | Schlüssel der OpenAI-kompatiblen API |
| model | Modellname, z. B. whisper-1 |
| app_key | Anwendungsschlüssel für Doubao / Volcengine |
| access_key | Zugriffsschlüssel für Doubao / Volcengine |
| resource_id | Doubao-Ressourcen-ID |
| cluster | Clustername von Volcengine |
| asr_mode | ASR-Erkennungsmodus |
| Textüberarbeitung aktivieren | Hauptschalter; wenn deaktiviert, wird kein LLM aufgerufen |
| LLM-Rollen aktivieren | Nur wählbar, wenn Textüberarbeitung aktiv ist; bei Deaktivierung ausgegraut |

### Allgemeine Einstellungen (Seite Einstellungen)

| Einstellung | Funktion |
| --- | --- |
| Tastenkombination | Globale Tastenkombination zum Auslösen der Aufnahme, standardmäßig Ctrl+Alt; Klick auf „Ändern" öffnet ein Fenster zum Erfassen einer neuen Kombination |
| Thema | Hell (light) oder dunkel (dark), standardmäßig dunkel |
| Schriftgrad | Schriftgrad 8 ~ 15, Standard 10; über Auf-/Ab-Pfeile einstellen, betrifft nur die Schrift, nicht die Steuerelemente, wirksam nach Neustart |
| Oberflächensprache | Wechselt die Anzeigesprache der Oberfläche, insgesamt 35 verfügbar |
| Autostart | Wenn aktiviert, wird das Programm beim Hochfahren automatisch gestartet |
| Schwebendes Fenster | Wenn aktiviert, wird während der Aufnahme ein schwebendes Fenster angezeigt (mit dünnem Rahmen in der Themenfarbe); bei Deaktivierung wird das Ergebnis nur im Textfeld des Hauptfensters angezeigt |

### Text-Nachverarbeitungsschalter (Seite Werkzeugkasten)

| Einstellung | Funktion | Standard |
| --- | --- | --- |
| Endsatzzeichen entfernen | Automatisches Entfernen von Komma und Punkt am Ende des Erkennungsergebnisses | An |
| ITN-Zahlenkonvertierung | Wandelt „十五六个" in „15~16个" usw. um; eingebaute Schutzwörter verhindern Fehlkonvertierungen von „一会儿""一样" | An |
| Füllwörter entfernen | Automatisches Entfernen mündlicher Füllwörter wie „呃、啊、嗯" (rein lokale Verarbeitung, ohne LLM) | An |
| Heißwort-Ersetzung | Erzwungene Ersetzung seltener Wörter über Phonetik-Fuzzy-Matching | An |
| Heißwort-Matching-Schwellwert | Ähnlichkeitsschwellwert für Heißwörter, 0.0~1.0, je größer desto strenger | 0.85 |
| Regex-Regel-Ersetzung | Präzise Ersetzung von Texten nach Gleichungen oder Regex-Regeln | An |
| Tagebucharchiv | Speichert jede Spracheingabe und jedes Erkennungsergebnis nach Datum | An |

> LLM-bezogene Schalter (Textüberarbeitung aktivieren, LLM-Rollen aktivieren) befinden sich auf der Seite „AI-Konfiguration", nicht im Werkzeugkasten.

### Audioparameter

| Einstellung | Funktion | Standard |
| --- | --- | --- |
| sample_rate | Audio-Abtastrate (Hz) | 16000 |
| chunk_size | Audio-Blockgröße (Bytes) | 3200 |

## 6. Unterstützte Oberflächensprachen

Die Software enthält die folgenden 35 Oberflächensprachen, wobei für jede Sprache automatisch die passendste Schriftart gewählt wird (für Chinesisch Microsoft YaHei, für Japanisch Yu Gothic, für Koreanisch Malgun Gothic, für andere Sprachen Segoe UI):

1. Vereinfachtes Chinesisch (zh_CN)
2. Traditionelles Chinesisch (zh_TW)
3. Englisch (en)
4. Spanisch (es)
5. Arabisch (ar)
6. Hindi (hi)
7. Indonesisch (id)
8. Japanisch (ja)
9. Französisch (fr)
10. Deutsch (de)
11. Russisch (ru)
12. Portugiesisch (pt)
13. Italienisch (it)
14. Türkisch (tr)
15. Polnisch (pl)
16. Niederländisch (nl)
17. Koreanisch (ko)
18. Vietnamesisch (vi)
19. Bengalisch (bn)
20. Urdu (ur)
21. Philippinisch (fil)
22. Malaiisch (ms)
23. Thailändisch (th)
24. Tschechisch (cs)
25. Ungarisch (hu)
26. Schwedisch (sv)
27. Finnisch (fi)
28. Rumänisch (ro)
29. Ukrainisch (uk)
30. Griechisch (el)
31. Dänisch (da)
32. Norwegisch (no)
33. Hebräisch (he)
34. Bulgarisch (bg)
35. Kroatisch (hr)

Beim ersten Start wird die Oberflächensprache automatisch anhand der Systemsprache gewählt; danach kann sie auf der Seite „Einstellungen" manuell gewechselt werden.

## 7. Häufige Fragen

### 1. Keine Reaktion auf die Tastenkombination?

- Bestätigen, dass die Software im System-Tray läuft (graues Tray-Symbol bedeutet bereit)
- Bestätigen, dass die Tastenkombination nicht von anderer Software belegt ist
- Auf der Seite „Einstellungen" auf die Schaltfläche „Ändern" neben der Tastenkombination klicken und im Popup-Fenster die Tastenkombination neu erfassen
- Auf der Protokoll-Seite prüfen, ob Fehlermeldungen angezeigt werden

### 2. Was tun, wenn die Erkennung fehlschlägt?

- Auf der Seite „AI-Konfiguration" prüfen, ob API-Schlüssel, Adresse und Modell korrekt eingetragen sind
- Netzwerkverbindung prüfen
- Die Seite „Protokoll" öffnen, um die genaue Fehlermeldung zu sehen
- Bestätigen, dass das Mikrofon funktioniert und die Lautstärke beim Sprechen ausreicht

### 3. Wie wird der Schriftgrad eingestellt?

Auf der Seite „Einstellungen" den Eintrag „Schriftgrad" suchen und über die Auf-/Ab-Pfeile rechts den Wert (8 ~ 15, Standard 10) einstellen. Je größer der Wert, desto größer die Schrift. Diese Einstellung betrifft nur die Schrift, nicht die Größe von Schaltflächen und anderen Steuerelementen; nach dem Ändern ist ein Neustart erforderlich.

### 4. Wie wird die Tastenkombination angepasst?

Auf der Seite „Einstellungen" den Eintrag „Tastenkombination" suchen, auf die Schaltfläche „Ändern" rechts klicken und im separaten Fenster die gewünschte Tastenkombination drücken (1 ~ 3 Tasten, z. B. Ctrl+Shift+V). Nach der Erfassung auf „Bestätigen" klicken, um zu speichern; nach einem Neustart wird die neue Tastenkombination wirksam.

### 5. Das Erkennungsergebnis wird nicht automatisch eingefügt?

- Bestätigen, dass das Zielfenster Einfügevorgänge unterstützt
- Bestätigen, dass sich der Cursor in einem eingabefähigen Bereich befindet
- Wenn das schwebende Fenster deaktiviert ist, wird das Erkennungsergebnis nur im Textfeld des Hauptfensters angezeigt und muss manuell über die Kopieren-Schaltfläche kopiert werden

### 6. Wie werden seltene Wörter hinzugefügt, um die Erkennung zu verbessern?

Die Datei `config/hot.txt` direkt bearbeiten, ein Heißwort pro Zeile. Zusätzlich können in `config/hot-rule.txt` Gleichungen oder Regex-Regeln für präzise Ersetzungen verwendet werden.

### 7. Wie verwendet man LLM-Rollen?

Im Verzeichnis `config/roles/` eine `.py`-Datei erstellen und darin Rolleneigenschaften per Variablenzuweisung definieren (name, trigger_words, system_prompt, output_mode usw.). Rollendateien werden per AST sicher geparst, nur literale Zuweisungen sind erlaubt – Funktionsaufrufe oder beliebiger Code sind nicht zulässig. Wenn das Erkennungsergebnis mit einem Rollennamen beginnt, wird die entsprechende Rolle automatisch ausgelöst.
