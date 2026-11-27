# Blocks & Items Explorer

Eine Python-Anwendung zum Suchen und Durchstöbern von Minecraft-**Items**, **Blöcken**, **Mods** und **Modpacks** über die [BlocksItems API](https://blocksitems.com/api/2026.1.3). Das Projekt umfasst sowohl eine Terminal-Version (CLI) als auch eine dunkle Desktop-GUI mit Bildvorschau, Seitennavigation und optionalen Filtern für Minecraft-Version, Mod-Namen und dominante Farbe.

---

## Dateien in diesem Projekt

| Datei | Beschreibung |
| --- | --- |
| **`blocksitems_API_noAI.py`** | Die ursprüngliche, **von Hand geschriebene** Terminal-Version des BlocksItems-API-Clients – komplett **ohne Hilfe eines KI-Agenten** programmiert. Ermöglicht die Auswahl einer Kategorie (`Items`, `Blocks`, `Mods`, `Modpacks` oder `All`), die Suche nach Namen, die Ausgabe von Item-/Mod-/Versionsdetails in der Konsole sowie das Blättern durch die Ergebnisseiten. |
| **`blocksitems_API.py`** | Erweiterte Version des API-Clients, die von der GUI verwendet wird. Behält bei direktem Ausführen die ursprüngliche Terminal-Oberfläche bei und ergänzt Hilfsfunktionen zum Filtern nach Minecraft-Version, Mod-Namen und dominanter Farbe (inkl. HSV/RGB-Farbabgleich, Bulk-Farbabfragen über `/lookup` und Block-Farbsuche über `/colors/search`). |
| **`blocksitems_GUI.py`** | Dunkle Desktop-Oberfläche, erstellt mit Tkinter und Pillow. Nutzt `blocksitems_API.py` und bietet Kategorie-Buttons, eine Suche mit optionalen Filtern für MC-Version, Mod-Name und Color-Picker, asynchrones Laden von Bildern mit Caching, Seitennavigation sowie ein eigenes Fenster- und Taskleisten-Icon. |
| **`blocksitems_icon.png`** | Eigenes Anwendungs-Icon, das von `blocksitems_GUI.py` automatisch für die Titelleiste und die Windows-Taskleiste geladen wird. Kann durch eine beliebige `blocksitems_icon.ico`-, `.png`-, `.jpg`-, `.jpeg`- oder `.webp`-Datei im selben Ordner ersetzt werden. |

---

## Voraussetzungen

- **Python 3.12 oder neuer** (erforderlich für `match`/`case`-Anweisungen und verschachtelte Anführungszeichen in f-Strings)
- **Tkinter** (bei Standard-Python-Installationen unter Windows und macOS bereits enthalten; unter Linux bei Bedarf `python3-tk` installieren)
- **Internetverbindung** (für Abfragen an `https://blocksitems.com/api/2026.1.3` und zum Laden der Icons/Renders)
- **Python-Pakete:**
  - `requests` – erforderlich für alle Skripte (`blocksitems_API_noAI.py`, `blocksitems_API.py` und `blocksitems_GUI.py`)
  - `pillow` – erforderlich für `blocksitems_GUI.py` (Bildvorschauen sowie eigenes Taskleisten- und Fenster-Icon)

### Abhängigkeiten installieren

Die benötigten Pakete lassen sich mit `pip` installieren:

```powershell
python -m pip install requests pillow
```

*(Wenn nur die Terminal-Skripte `blocksitems_API_noAI.py` oder `blocksitems_API.py` ausgeführt werden sollen, wird lediglich `requests` benötigt.)*

### Skripte ausführen

Im `API`-Ordner ausführen:

- **Desktop-GUI:**
  ```powershell
  python blocksitems_GUI.py
  ```
- **Handgeschriebener Terminal-Client (ohne KI):**
  ```powershell
  python blocksitems_API_noAI.py
  ```
- **Erweiterter Terminal-Client:**
  ```powershell
  python blocksitems_API.py
  ```
