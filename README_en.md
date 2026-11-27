# Blocks & Items Explorer

A Python application for searching and browsing Minecraft **Items**, **Blocks**, **Mods**, and **Modpacks** using the [BlocksItems API](https://blocksitems.com/api/2026.1.3). It includes both a terminal (CLI) version and a dark-themed desktop GUI with image previews, pagination, and optional filters for Minecraft version, mod name, and dominant color.

---

## Files in This Project

| File | Description |
| --- | --- |
| **`blocksitems_API_noAI.py`** | The original **handcoded** terminal version of the BlocksItems API client, written manually **without the help of an AI agent**. Lets you pick a category (`Items`, `Blocks`, `Mods`, `Modpacks`, or `All`), search by name, view item/mod/version details in the console, and navigate through result pages. |
| **`blocksitems_API.py`** | Extended version of the API client used by the GUI. Keeps the original terminal interface when run directly, and adds helper functions for filtering by Minecraft version, mod name, and dominant color (including HSV/RGB color matching, bulk color lookups via `/lookup`, and block color search via `/colors/search`). |
| **`blocksitems_GUI.py`** | Dark-themed desktop interface built with Tkinter and Pillow. Connects to `blocksitems_API.py` to provide category buttons, search with optional MC version / mod name / color picker filters, asynchronous image loading with caching, pagination controls, and a custom window & taskbar icon. |
| **`blocksitems_icon.png`** | Custom application icon automatically loaded by `blocksitems_GUI.py` for the window title bar and Windows taskbar. Can be replaced with any `blocksitems_icon.ico`, `.png`, `.jpg`, `.jpeg`, or `.webp` file in the same folder. |

---

## Requirements

- **Python 3.12 or newer** (required for `match`/`case` statements and nested quotes in f-strings)
- **Tkinter** (included by default with standard Python installations on Windows and macOS; on Linux install `python3-tk` if missing)
- **Internet connection** (to query `https://blocksitems.com/api/2026.1.3` and load icons/renders)
- **Python packages:**
  - `requests` — required for all scripts (`blocksitems_API_noAI.py`, `blocksitems_API.py`, and `blocksitems_GUI.py`)
  - `pillow` — required for `blocksitems_GUI.py` (image thumbnails and custom taskbar/window icon)

### Installing Dependencies

Install the required packages with `pip`:

```powershell
python -m pip install requests pillow
```

*(If you only want to run the terminal scripts `blocksitems_API_noAI.py` or `blocksitems_API.py`, only `requests` is needed.)*

### Running the Scripts

From inside the `API` folder:

- **Desktop GUI:**
  ```powershell
  python blocksitems_GUI.py
  ```
- **Handcoded Terminal Client (no AI):**
  ```powershell
  python blocksitems_API_noAI.py
  ```
- **Extended Terminal Client:**
  ```powershell
  python blocksitems_API.py
  ```
