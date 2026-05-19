# 🎮 DeepRenPyTrans

**KI-gestützter universeller Übersetzer für Ren'Py Visual Novels.**

🌐 [English](README.md) | [Русский](README.ru.md) | [Español](README.es.md) | [Português](README.pt.md) | [Deutsch](README.de.md) | [Français](README.fr.md) | [简体中文](README.zh.md)

---

Übersetzen Sie jedes Ren'Py-Spiel in jede beliebige Sprache mit DeepSeek (einschließlich `deepseek-v4-flash` / `deepseek-v4-pro`), OpenAI oder lokalen LLMs – ohne den Quellcode des Spiels zu verändern.

---

## ✨ Features

- **🔍 Intelligente Extraktion** – Findet automatisch alle übersetzbaren Strings in `.rpy`-Dateien und filtert Code, IDs und Debug-Meldungen heraus.
- **🤖 KI-Übersetzung** – Stapelübersetzung über DeepSeek, OpenAI oder lokales Ollama mit szenenbezogenem Kontext.
- **🔌 Laufzeit-Injektion** – Hook-System ohne Quellcode-Modifikation über die Ren'Py-eigene Funktion `config.replace_text`.
- **📊 Qualitätsprüfung** – Findet unübersetzte Strings, verwaiste Übersetzungen und Müll-Einträge.
- **🧹 Wörterbuch-Bereinigung** – Entfernt automatisch Debug-Strings, Docstrings und Code-Artefakte.
- **⚡ Inkrementell** – Setzt abgebrochene Übersetzungen fort und verarbeitet nur neue oder fehlende Strings.
- **📱 Plattformübergreifend** – Funktioniert mit PC-, Android- (APK-Injektion) und iOS-Builds.

## 🚀 Schnellstart

### 1. Installieren

```bash
git clone https://github.com/Danko-Novak/DeepRenPyTrans.git
cd DeepRenPyTrans

# Option A: Als Paket installieren (empfohlen – stellt den Befehl `deeprenpytrans` bereit)
pip install -e .

# Option B: Nur Abhängigkeiten installieren
pip install -r requirements.txt
```

> Nach `pip install -e .` können Sie `deeprenpytrans` direkt anstelle von `python -m deeprenpytrans` verwenden.

### 2. Konfigurieren

```bash
# Beispielkonfigurationen kopieren
cp .env.example .env
cp config.example.yaml config.yaml

# Bearbeiten Sie .env mit Ihrem API-Schlüssel
# Bearbeiten Sie config.yaml mit Ihrem Spielpfad und der Zielsprache
```

Sie können das Tool auf zwei Arten ausführen:

#### Option A: Web-Konsole GUI (Empfohlen)
Starten Sie den lokalen Webserver und nutzen Sie die Benutzeroberfläche im Browser, um Einstellungen zu verwalten, Build-Flags zu ändern und Aufgaben auszuführen:
```bash
python gui_server.py
```
Dies öffnet automatisch Ihren Browser unter `http://localhost:8000`.

#### Option B: Befehlszeilenschnittstelle (CLI)
```bash
# Schritt 1: Strings aus Ihrem Spiel extrahieren
python -m deeprenpytrans extract --game "./MeinSpiel/game"

# Schritt 2: Mit KI übersetzen
python -m deeprenpytrans translate --strings strings_by_file.json --dict "./MeinSpiel/game/tl/german/dictionary.json"

# Schritt 3: Hooks für die Laufzeit generieren
python -m deeprenpytrans inject --game "./MeinSpiel/game" --lang german
```


## 📖 Befehle

### `extract` — Übersetzbare Strings finden

```bash
python -m deeprenpytrans extract --game ./MeinSpiel/game --output strings.json
```

Durchsucht alle `.rpy`-Dateien, extrahiert Strings in Anführungszeichen und wendet intelligente Filter an, um Folgendes zu überspringen:
- Interne IDs (`ITM_Sword`, `LOC_Bridge`, `ACT_NPC01`)
- Python-Code und Assertions
- Dateipfade und Hex-Farbcodes
- Debug- und Protokollmeldungen
- Bereits übersetzte Texte (Erkennung von Zielsprachenzeichen)

Optionen:
| Flag | Beschreibung |
|------|-------------|
| `--game PATH` | Pfad zum `game/`-Verzeichnis des Spiels |
| `--output FILE` | Ausgabe-JSON-Datei (Standard: `strings_by_file.json`) |
| `--include-log PATH` | Strings aus `untranslated.log` zusammenführen |

### `translate` — KI-gestützte Übersetzung

```bash
python -m deeprenpytrans translate --strings strings.json --dict dictionary.json
```

Sendet Strings in intelligenten Stapeln (nach Quelldatei gruppiert für besseren Kontext) an die KI-API.
Unterstützt inkrementelle Übersetzung – bereits übersetzte Strings werden übersprungen.

### `audit` — Qualitätsprüfung

```bash
python -m deeprenpytrans audit --dict dictionary.json --strings strings.json
```

Erstellt einen Bericht mit folgenden Details:
- ❌ Unübersetzte Strings (im Quellcode, aber nicht im Wörterbuch)
- 👻 Verwaiste Übersetzungen (im Wörterbuch, aber nicht im Quellcode)
- 🔁 Identische Schlüssel-Wert-Paare (möglicherweise nicht übersetzt)
- 📭 Leere Übersetzungen
- 🗑️ Müll-Einträge (Debug-Meldungen, Code-Schnipsel)

### `clean` — Müll aus dem Wörterbuch entfernen

```bash
python -m deeprenpytrans clean --dict dictionary.json --dry-run
python -m deeprenpytrans clean --dict dictionary.json --remove-orphaned
```

Optionen:
| Flag | Beschreibung |
|------|-------------|
| `--dry-run` | Vorschau der zu löschenden Einträge |
| `--keep-junk` | Debug-/Code-Strings nicht entfernen |
| `--remove-orphaned` | Auch Strings entfernen, die nicht im Quellcode gefunden wurden |

### `inject` — hooks.rpy generieren

```bash
python -m deeprenpytrans inject --game ./MeinSpiel/game --lang german
```

Generiert eine `hooks.rpy`-Datei, die:
- Die `dictionary.json` beim Spielstart lädt.
- Alle Texte über `config.replace_text` abfängt.
- Unübersetzte Strings während des Spiels in `untranslated.log` protokolliert.
- Einen Hotkey zum Ein- und Ausschalten der Übersetzung im Spiel hinzufügt.
- Schriftarten für die Zielsprache überschreibt.

## ⚙️ Konfiguration

### `config.yaml`

```yaml
game_dir: "./MeinSpiel/game"
target_language: "German"
translation_dir: "german"

api:
  provider: "deepseek"    # oder "openai", "ollama"
  model: "deepseek-chat"  # unterstützt neue deepseek-v4-flash / deepseek-v4-pro Modelle
  temperature: 0.2
  batch_size: 40

fonts:
  default: "DejaVuSans.ttf"
  replacements:
    "OriginalFont.ttf": "DejaVuSans.ttf"

extraction:
  skip_prefixes: ["ITM", "ACT", "LOC", "QST"]
  force_include: ["Q.Save", "Q.Load"]
```

### `.env`

```bash
DEEPSEEK_API_KEY=sk-ihr-schluessel-hier
# oder
OPENAI_API_KEY=sk-ihr-openai-schluessel
```

## 🏗️ Funktionsweise

```
┌────────────────┐     ┌──────────────┐     ┌────────────────┐
│  .rpy-Dateien  │────▶│  Extraktor   │────▶│  strings.json  │
│  (Spiel-Code)  │     │   (Filter)   │     │ (nach Datei)   │
└────────────────┘     └──────────────┘     └───────┬────────┘
                                                    │
                                                    ▼
┌────────────────┐     ┌──────────────┐     ┌────────────────┐
│  Wörterbuch    │◀────│  Übersetzer  │◀────│  KI-Provider   │
│     .json      │     │   (Stapel)   │     │ (DeepSeek/etc) │
└───────┬────────┘     └──────────────┘     └────────────────┘
        │
        ▼
┌────────────────┐     ┌──────────────┐
│   hooks.rpy    │────▶│ Ren'Py Spiel │ ← Spieler sieht übersetzten Text!
│  (Laufzeit)    │     │  (Laufzeit)  │
└────────────────┘     └──────────────┘
```

## 📱 Mobile Bereitstellung

### Android (APK-Injektion)
1. Verwenden Sie unser automatisiertes Skript `build_apk.bat`, das alle Schritte übernimmt:
   - Extraktion der Spieldateien aus der alten APK.
   - Wiederherstellung bereits komprimierter Ressourcen aus der Original-APK, um bis zu 60 % der Größe einzusparen (im Durchschnitt ~400-500 MB Ersparnis).
   - Durchführung von wav-zu-ogg Audiokompression.
   - Optimierung neuer Bilder für Mobilgeräte unter Überspringung bereits komprimierter Ressourcen.
   - Packen der APK mit Ultra-Komprimierung und automatische Signierung.
2. **Anpassung**: Sie können den Erstellungsprozess anpassen, indem Sie die Flags oben in `build_apk.bat` bearbeiten:
   - `RESTORE_OLD_ASSETS` (1/0): Aktivieren/Deaktivieren der Wiederherstellung bereits komprimierter Ressourcen aus der alten APK.
   - `COMPRESS_AUDIO` (1/0): Aktivieren/Deaktivieren der wav-zu-ogg-Konvertierung und Skriptanpassung.
   - `COMPRESS_IMAGES` (1/0): Aktivieren/Deaktivieren der Komprimierung neuer Bilder.
   - `INJECT_TRANSLATION` (1/0): Aktivieren/Deaktivieren der Übersetzungs-Injektion. Auf `0` setzen, um einen sauberen unübersetzten Port (in Originalsprache) zu erstellen.
   - `LANG_FOLDER`: Name des Zielsprachenordners in `game/tl/` (z. B. `german`).
   - `COMPRESSION_LEVEL` (0-9): 7-Zip-Komprimierungsstufe (9 = Ultra-Komprimierung, 0 = nur speichern).
3. Bei manueller Erstellung: Entpacken Sie die APK mit 7zip, ersetzen Sie die Dateien in `assets/x-game/game/`, entfernen Sie Signaturen in `META-INF/` und packen/signieren Sie sie neu.

### iOS
1. Xcode-Projekt über den Ren'Py Launcher generieren.
2. Den Übersetzungsordner `tl/german/` zum Projekt hinzufügen.
3. Build erstellen und bereitstellen.

## ⚠️ Wichtiger Hinweis & Einschränkungen

- **Teststatus**: Dieses Tool wurde bisher nur an einem einzigen Spiel getestet und verifiziert, bei dem alles korrekt übersetzt und erstellt wurde.
- **Spielspezifischer Code**: Obwohl das Ziel darin bestand, ein perfektes universelles Übersetzungswerkzeug zu schaffen, können andere Ren'Py-Spiele Anpassungen erfordern, um sich an ihre spezifische Codebasis, benutzerdefinierte Präfixe oder Skript-Eigenheiten anzupassen.
- **Keine Programmierkenntnisse?**: Wenn Sie nicht programmieren können oder keine Zeit haben, die Skripte anzupassen, empfehlen wir dringend die Verwendung von KI-Programmierassistenten wie **Antigravity**, **Cursor** oder ähnlichen Tools, um den Extraktor und die Filter an Ihr Zielspiel anzupassen.

## 🤝 Mitwirken

Beiträge sind gerne gesehen! Bereiche, die Hilfe benötigen:
- Integration zusätzlicher LLM-Provider.
- Unterstützung und Testen von CJK-Sprachen (Chinesisch, Japanisch, Koreanisch).
- Verbesserte Extraktionsheuristiken für spezifische Spiele.

## 🗺️ Roadmap & Funktionen

Wir verfolgen unsere Entwicklung, planen neue Funktionen und priorisieren Aufgaben basierend auf dem Feedback der Community. Wenn Sie eine Idee haben oder ein Feature anfordern möchten, besuchen Sie bitte den Tab **Discussions** (Diskussionen) auf GitHub, reichen Sie Ihren Vorschlag ein oder stimmen Sie für bestehende Ideen ab!

| Funktion | Stimmen | Status | Fortschritt |
| :--- | :--- | :--- | :--- |
| **Web-GUI-Konsole (Dashboard)** | - | 🚀 Veröffentlicht | `[████████████████████]` 100% |
| **Android APK Packer & Optimierer** | - | 🚀 Veröffentlicht | `[████████████████████]` 100% |
| **Lokale LLMs & Ollama-Unterstützung** | - | 🚀 Veröffentlicht | `[████████████████████]` 100% |
| **macOS- & Linux-Unterstützung** | 0 | 📋 Geplant | `[██░░░░░░░░░░░░░░░░░░]` 10% |
| **Übersetzungsprüfungen für Japanisch/Chinesisch** | 0 | 📋 Geplant | `[█░░░░░░░░░░░░░░░░░░░]` 5% |

---

## 💖 Projekt unterstützen

DeepRenPyTrans ist ein Herzensprojekt, das entwickelt wurde, um den Übersetzungsprozess von Visual Novels zu rationalisieren. Wenn dieses Tool Ihnen Zeit gespart oder geholfen hat, ein Spiel einem neuen Publikum zugänglich zu machen, ziehen Sie bitte eine Unterstützung seiner Entwicklung in Betracht.

Ich arbeite derzeit mit einer einfachen Entwicklungsstation und möchte diese zu einer dedizierten lokalen KI-Workstation unter Linux mit ROCm aufrüsten. Dies ermöglicht native Hochgeschwindigkeitstests von lokalen LLMs.

**Aktueller Spendenstand:** 0 / 1.200 USD

### 🚀 Upgrade-Stufen:
* **Stufe 1: GPU-Upgrade ($850)** — Upgrade auf eine 24-GB-AMD-Radeon-GPU (z. B. RX 7900 XTX oder ein entsprechendes Modell der nächsten Generation), um große lokale LLMs (wie 14B/32B/70B-Modelle) lokal unter Linux ROCm auszuführen.
* **Stufe 2: Speicher-Upgrade ($150)** — Upgrade auf eine schnelle 2-TB-PCIe-4.0-NVMe-SSD. Lokale LLM-Modelle benötigen enormen Speicherplatz (5 GB bis 40 GB+ pro Modell), und meine aktuelle 500-GB-SSD ist voll.
* **Stufe 3: RAM-Upgrade ($150)** — Hinzufügen von weiteren 32 GB RAM (Upgrade auf insgesamt 64 GB) für parallele Workflows, intensives IDE-Multitasking und CPU-Auslagerung für besonders große Modelle.
* **Laufende Kosten: API-Fonds ($50)** — Kleines Budget zum Testen kommerzieller APIs (DeepSeek, OpenAI, Claude) während der Übersetzungstests.

### So können Sie helfen:
* **Dem Repository einen Stern geben (Star):** Hilft bei der Sichtbarkeit und motiviert mich, weiter zu coden!
* **Mitwirken:** Erstellen Sie Issues, schlagen Sie Features vor oder senden Sie einen PR.
* **Spenden (USDT - TON / TON-Netzwerk):**
  `UQBdHUyR8nG5p_Rwhw_Rtmgc7QJdJ-G5nOPJa7Pq0mh2A27K`

## 📄 Lizenz

GNU AGPL v3 — siehe [LICENSE](LICENSE).
