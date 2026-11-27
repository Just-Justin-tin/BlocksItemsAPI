from concurrent.futures import ThreadPoolExecutor
import ctypes
from io import BytesIO
from pathlib import Path
import sys
import threading
import tkinter as tk
from tkinter import colorchooser, ttk
from PIL import Image, ImageTk

import blocksitems_API as bi


# =============================================================================
# API & APP CONFIGURATION (pulled directly from blocksitems_API.py)
# =============================================================================
APP_DIR = Path(__file__).resolve().parent
APP_ICON_FILES = (
    "blocksitems_icon.ico",
    "blocksitems_icon.png",
    "blocksitems_icon.jpg",
    "blocksitems_icon.jpeg",
    "blocksitems_icon.webp",
)
BASE_URL = bi.url.rstrip("/")
CATEGORIES = list(bi.categories)  # ["Items", "Blocks", "Mods", "Modpacks", "All"]
SUB_CATEGORIES = [c for c in CATEGORIES if c != "All"]
RESULTS_PER_PAGE = 50
IMAGE_SIZE = 76


# =============================================================================
# GLOBAL STATE
# =============================================================================
selected_category = CATEGORIES[0]
selected_color_hex = None  # Optional color picker hex code (e.g. "#3498db") or None
current_page = 1
total_pages = 1
total_items_count = 0
search_generation = 0  # Tracks active search so stale background results are ignored

loaded_images = []  # Keeps PhotoImage references alive for the current page
pil_image_cache = {}  # Caches downloaded PIL images by URL for instant revisits
info_wrap_labels = []  # Labels whose wraplength updates on window resize

# Reusable HTTP session + thread pool for non-blocking API calls and image loading
http_session = bi.requests.Session()
image_executor = ThreadPoolExecutor(max_workers=8)


# =============================================================================
# DARK THEME COLORS
# =============================================================================
BG_MAIN = "#14151a"
BG_PANEL = "#1e2028"
BG_CARD = "#252834"
BG_INPUT = "#111217"
BG_IMAGE_BOX = "#161820"
BORDER_COLOR = "#34384a"

ACCENT = "#2ea043"
ACCENT_HOVER = "#3fb950"
BTN_INACTIVE = "#2b2e3c"
BTN_INACTIVE_HOVER = "#383c4e"
BTN_CLEAR = "#3e272e"
BTN_CLEAR_HOVER = "#53333c"
BTN_CLEAR_TEXT = "#f38ba8"

BADGE_COLORS = {
    "Items": "#2b5c8f",
    "Blocks": "#2e6f40",
    "Mods": "#6c4694",
    "Modpacks": "#945a28",
}

TEXT_PRIMARY = "#f3f4f8"
TEXT_SECONDARY = "#a6accd"
TEXT_MUTED = "#6c728a"
TEXT_ERROR = "#f38ba8"


# =============================================================================
# HELPER WIDGET: ENTRY WITH PLACEHOLDER TEXT
# =============================================================================
class PlaceholderEntry(tk.Entry):
    def __init__(self, master, placeholder="", **kwargs):
        super().__init__(master, **kwargs)
        self.placeholder = placeholder
        self.showing_placeholder = False
        self.normal_fg = kwargs.get("fg", TEXT_PRIMARY)

        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self._show_placeholder()

    def _show_placeholder(self):
        if not self.get():
            self.showing_placeholder = True
            self.configure(fg=TEXT_MUTED)
            self.insert(0, self.placeholder)

    def _on_focus_in(self, _event=None):
        if self.showing_placeholder:
            self.delete(0, tk.END)
            self.configure(fg=self.normal_fg)
            self.showing_placeholder = False

    def _on_focus_out(self, _event=None):
        if not self.get():
            self._show_placeholder()

    def set_placeholder(self, new_placeholder):
        """Update placeholder text without erasing anything the user already typed."""
        self.placeholder = new_placeholder
        if self.showing_placeholder:
            self.delete(0, tk.END)
            self.insert(0, self.placeholder)

    def get_value(self):
        """Return typed text, or empty string when only the placeholder is visible."""
        if self.showing_placeholder:
            return ""
        return self.get().strip()


# =============================================================================
# REAL API REQUESTS (using blocksitems_API.py for URL, requests, and filters)
# =============================================================================
def _fetch_single_category(category, query, mc_version, mod_name, color_hex, page):
    """Fetch one page (50 results) for a single category from BlocksItems API."""
    # Dominant color filtering for Items and Blocks (handled in blocksitems_API.py)
    if color_hex and category in ("Items", "Blocks"):
        return bi.search_with_color_filter(
            category=category,
            query=query,
            mc_version=mc_version,
            mod_name=mod_name,
            color_hex=color_hex,
            page=page,
            limit=RESULTS_PER_PAGE,
            session=http_session,
        )

    # Standard category endpoints matching blocksitems_API.py
    endpoint = f"{BASE_URL}/{category.lower()}"
    params = {
        "limit": RESULTS_PER_PAGE,
        "page": page,
    }
    if query:
        params["q"] = query.lower()

    # Optional MC Version & Mod Name query filters (in blocksitems_API.py)
    bi.apply_filter_params(category, params, query, mc_version, mod_name)

    response = http_session.get(endpoint, params=params, timeout=15)
    response.raise_for_status()
    payload = response.json()

    items = []
    for entry in payload.get("data", []):
        item_copy = dict(entry)
        item_copy["_category"] = category
        items.append(item_copy)

    # Local MC Version filter for Mods (in blocksitems_API.py)
    items = bi.apply_local_filters(category, items, mc_version=mc_version, color_hex=color_hex)

    pagination = payload.get("pagination") or {}
    return {
        "data": items,
        "pagination": {
            "page": pagination.get("page", page),
            "limit": pagination.get("limit", RESULTS_PER_PAGE),
            "pages": max(1, pagination.get("pages", 1)),
            "total": pagination.get("total", len(items)),
        },
        "url": response.url,
    }


def fetch_api_results(category, query, mc_version, mod_name, color_hex, page):
    """Fetch results for the chosen category (or all 4 categories combined for 'All')."""
    if category != "All":
        return _fetch_single_category(category, query, mc_version, mod_name, color_hex, page)

    # When filtering "All" by color, search both Items and Blocks by dominant color in parallel
    if color_hex:
        with ThreadPoolExecutor(max_workers=2) as pool:
            item_future = pool.submit(
                bi.search_with_color_filter,
                "Items", query, mc_version, mod_name, color_hex, 1, 500, http_session,
            )
            block_future = pool.submit(
                bi.search_with_color_filter,
                "Blocks", query, mc_version, mod_name, color_hex, 1, 500, http_session,
            )
            combined = []
            for fut in (item_future, block_future):
                try:
                    combined.extend(fut.result()["data"])
                except Exception:
                    pass

        combined.sort(key=lambda it: bi.dominant_color_distance(it, color_hex))
        total = len(combined)
        total_pages_all = max(1, (total + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE)
        safe_page = min(max(1, page), total_pages_all)
        start = (safe_page - 1) * RESULTS_PER_PAGE
        return {
            "data": combined[start:start + RESULTS_PER_PAGE],
            "pagination": {
                "page": safe_page,
                "limit": RESULTS_PER_PAGE,
                "pages": total_pages_all,
                "total": total,
            },
            "url": f"{BASE_URL}/[items|blocks]?q={query.lower()}&dominant_color={color_hex}&page={safe_page}",
        }

    # Same logic as blocksitems_API.py "All": query Items, Blocks, Mods, Modpacks
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {
            cat: pool.submit(
                _fetch_single_category, cat, query, mc_version, mod_name, color_hex, page
            )
            for cat in SUB_CATEGORIES
        }

        per_cat_items = {}
        max_pages = 1
        combined_total = 0

        for cat in SUB_CATEGORIES:
            try:
                res = futures[cat].result()
                per_cat_items[cat] = res["data"]
                max_pages = max(max_pages, res["pagination"]["pages"])
                combined_total += res["pagination"]["total"]
            except Exception:
                per_cat_items[cat] = []

    # Round-robin pick up to RESULTS_PER_PAGE (50) balanced across non-empty categories
    combined_items = []
    idx = 0
    while len(combined_items) < RESULTS_PER_PAGE:
        added_any = False
        for cat in SUB_CATEGORIES:
            cat_list = per_cat_items.get(cat, [])
            if idx < len(cat_list):
                combined_items.append(cat_list[idx])
                added_any = True
                if len(combined_items) >= RESULTS_PER_PAGE:
                    break
        if not added_any:
            break
        idx += 1

    return {
        "data": combined_items,
        "pagination": {
            "page": page,
            "limit": RESULTS_PER_PAGE,
            "pages": max_pages,
            "total": combined_total,
        },
        "url": f"{BASE_URL}/[items|blocks|mods|modpacks]?q={query.lower()}&limit={RESULTS_PER_PAGE}&page={page}",
    }


# =============================================================================
# ASYNC IMAGE LOADING
# =============================================================================
def _download_pil_image(image_url):
    if image_url in pil_image_cache:
        return pil_image_cache[image_url]

    resp = http_session.get(image_url, timeout=10)
    resp.raise_for_status()
    img = Image.open(BytesIO(resp.content)).convert("RGBA")

    # Preserve pixel-art sharpness for tiny textures, smooth resize for larger icons/renders
    resample = (
        Image.Resampling.NEAREST
        if max(img.size) <= 32
        else Image.Resampling.LANCZOS
    )
    img.thumbnail((IMAGE_SIZE, IMAGE_SIZE), resample)

    # Keep cache bounded so memory stays low across many pages
    if len(pil_image_cache) > 400:
        pil_image_cache.clear()
    pil_image_cache[image_url] = img
    return img


def load_item_image_async(image_url, image_label, gen):
    """Download and render an item's PNG icon/render in the background."""
    if not image_url:
        image_label.configure(text="No Image", fg=TEXT_MUTED)
        return

    # Instant path if already cached
    if image_url in pil_image_cache:
        tk_img = ImageTk.PhotoImage(pil_image_cache[image_url])
        loaded_images.append(tk_img)
        image_label.configure(image=tk_img, text="")
        return

    image_label.configure(text="...", fg=TEXT_MUTED)

    def _worker():
        try:
            pil_img = _download_pil_image(image_url)
        except Exception:
            pil_img = None

        def _apply():
            if gen != search_generation or not image_label.winfo_exists():
                return
            if pil_img is None:
                image_label.configure(text="No Image", fg=TEXT_MUTED)
                return
            tk_img = ImageTk.PhotoImage(pil_img)
            loaded_images.append(tk_img)
            image_label.configure(image=tk_img, text="")

        try:
            root.after(0, _apply)
        except tk.TclError:
            pass

    image_executor.submit(_worker)


# =============================================================================
# GUI ACTIONS
# =============================================================================
def select_category(category_name):
    """Select one of the 5 categories (equivalent to answering 'What are you looking for?')."""
    global selected_category, current_page
    selected_category = category_name
    current_page = 1

    # Keep blocksitems_API's variable synced as well
    bi.userinputcat = category_name

    for name, btn in category_buttons.items():
        if name == selected_category:
            btn.configure(
                bg=ACCENT,
                fg="#ffffff",
                activebackground=ACCENT_HOVER,
                activeforeground="#ffffff",
                font=("Segoe UI", 10, "bold"),
            )
        else:
            btn.configure(
                bg=BTN_INACTIVE,
                fg=TEXT_PRIMARY,
                activebackground=BTN_INACTIVE_HOVER,
                activeforeground=TEXT_PRIMARY,
                font=("Segoe UI", 10),
            )

    if selected_category != "All":
        prompt_text = f"What {selected_category.removesuffix('s')} are you looking for?"
    else:
        prompt_text = "What are you looking for? (Searches Items, Blocks, Mods, Modpacks)"
    main_search_entry.set_placeholder(prompt_text)

    status_var.set(f"Selected category: {selected_category} — type a query and press Enter or Search.")


def pick_color():
    """Open the color picker and save the chosen hex code to `selected_color_hex`."""
    global selected_color_hex
    initial = selected_color_hex if selected_color_hex else "#2ea043"
    _rgb, hex_code = colorchooser.askcolor(
        color=initial,
        title="Pick a Color (Optional)",
    )
    if hex_code:
        selected_color_hex = hex_code
        color_preview.configure(bg=selected_color_hex)
        color_hex_label.configure(text=selected_color_hex, fg=TEXT_PRIMARY)


def clear_color():
    """Clear the optional color selection."""
    global selected_color_hex
    selected_color_hex = None
    color_preview.configure(bg=BG_INPUT)
    color_hex_label.configure(text="None", fg=TEXT_MUTED)


def _clear_results_area():
    for widget in results_container.winfo_children():
        widget.destroy()
    loaded_images.clear()
    info_wrap_labels.clear()


def _show_message_in_results(text, color=TEXT_MUTED):
    _clear_results_area()
    tk.Label(
        results_container,
        text=text,
        bg=BG_PANEL,
        fg=color,
        font=("Segoe UI", 11),
        pady=50,
        wraplength=650,
        justify="center",
    ).pack(fill="x")
    results_canvas.yview_moveto(0)


def _current_wraplength():
    canvas_w = results_canvas.winfo_width()
    if canvas_w <= 1:
        canvas_w = 820
    return max(260, canvas_w - 170)


def showfounddata(data, gen):
    """
    Render the found items inside the scrollable middle list:
    - Picture on the left (icon_url / render_url)
    - Name in big bold text next to it
    - Below the name: the exact information printed in the terminal by blocksitems_API.py
    """
    _clear_results_area()

    items = data.get("data", [])
    pagination = data.get("pagination", {})
    total_found = pagination.get("total", len(items))

    results_header_label.configure(
        text=f"Found {selected_category}: showing {len(items)} on this page ({total_found:,} total)"
    )

    if not items:
        _show_message_in_results(
            "No results found. Try a different search term or adjust your optional filters."
        )
        return

    wrap_len = _current_wraplength()

    for item in items:
        item_cat = item.get("_category", selected_category)
        if item_cat == "All":
            item_cat = "Items"
        cat_singular = item_cat.removesuffix("s")

        card = tk.Frame(
            results_container,
            bg=BG_CARD,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
            padx=12,
            pady=10,
        )
        card.pack(fill="x", padx=10, pady=5)

        # --- Left: Picture of the Item / Block / Mod / Modpack ---
        image_frame = tk.Frame(
            card,
            width=84,
            height=84,
            bg=BG_IMAGE_BOX,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
        )
        image_frame.pack(side="left", anchor="n", padx=(0, 14))
        image_frame.pack_propagate(False)

        image_label = tk.Label(
            image_frame,
            bg=BG_IMAGE_BOX,
            fg=TEXT_MUTED,
            font=("Segoe UI", 8),
            justify="center",
        )
        image_label.pack(expand=True, fill="both")

        image_url = item.get("icon_url") or item.get("render_url")
        load_item_image_async(image_url, image_label, gen)

        # --- Right: Name in Big + Terminal Info Below ---
        info_frame = tk.Frame(card, bg=BG_CARD)
        info_frame.pack(side="left", fill="both", expand=True)

        # Title Row: Name in big + subtle category badge
        title_row = tk.Frame(info_frame, bg=BG_CARD)
        title_row.pack(fill="x", pady=(0, 5))

        display_name = item.get("display_name") or item.get("full_id") or "Unknown"
        name_label = tk.Label(
            title_row,
            text=display_name,
            bg=BG_CARD,
            fg=TEXT_PRIMARY,
            font=("Segoe UI", 14, "bold"),
            anchor="w",
            justify="left",
            wraplength=wrap_len - 80,
        )
        name_label.pack(side="left", fill="x", expand=True)
        info_wrap_labels.append(name_label)

        badge_bg = BADGE_COLORS.get(item_cat, BTN_INACTIVE)
        tk.Label(
            title_row,
            text=cat_singular,
            bg=badge_bg,
            fg="#ffffff",
            font=("Segoe UI", 8, "bold"),
            padx=8,
            pady=2,
        ).pack(side="right", anchor="n", padx=(8, 0))

        # --- Info printed in terminal by blocksitems_API.py ---
        if item_cat in ("Items", "Blocks"):
            mod_info = item.get("mod") or {}
            mod_display = mod_info.get("display_name") or mod_info.get("slug") or "Unknown"
            tk.Label(
                info_frame,
                text=f"Mod: {mod_display}",
                bg=BG_CARD,
                fg=TEXT_SECONDARY,
                font=("Segoe UI", 10),
                anchor="w",
            ).pack(fill="x", pady=(0, 3))

            versions = item.get("mc_versions") or []
            versions_text = ", ".join(versions) if versions else "None"
            ver_lbl = tk.Label(
                info_frame,
                text=f"Versions: {versions_text}",
                bg=BG_CARD,
                fg=TEXT_SECONDARY,
                font=("Segoe UI", 9),
                anchor="w",
                justify="left",
                wraplength=wrap_len,
            )
            ver_lbl.pack(fill="x")
            info_wrap_labels.append(ver_lbl)

            # Show dominant color badge when filtering by color (works for Items and Blocks)
            matched_hex = bi.get_dominant_hex(item)
            if matched_hex and selected_color_hex:
                color_row = tk.Frame(info_frame, bg=BG_CARD)
                color_row.pack(fill="x", pady=(4, 0))
                tk.Frame(
                    color_row,
                    width=12,
                    height=12,
                    bg=matched_hex,
                    highlightbackground=BORDER_COLOR,
                    highlightthickness=1,
                ).pack(side="left", padx=(0, 6))
                tk.Label(
                    color_row,
                    text=f"Dominant Color: {matched_hex}",
                    bg=BG_CARD,
                    fg=TEXT_MUTED,
                    font=("Consolas", 8),
                ).pack(side="left")

        elif item_cat == "Mods":
            loaders = item.get("loaders") or []
            loaders_text = ", ".join(loaders) if loaders else "Unknown"
            tk.Label(
                info_frame,
                text=f"Loader: {loaders_text}",
                bg=BG_CARD,
                fg=TEXT_SECONDARY,
                font=("Segoe UI", 10),
                anchor="w",
            ).pack(fill="x", pady=(0, 3))

            versions = item.get("mc_versions") or []
            versions_text = ", ".join(versions) if versions else "None"
            ver_lbl = tk.Label(
                info_frame,
                text=f"Versions: {versions_text}",
                bg=BG_CARD,
                fg=TEXT_SECONDARY,
                font=("Segoe UI", 9),
                anchor="w",
                justify="left",
                wraplength=wrap_len,
            )
            ver_lbl.pack(fill="x")
            info_wrap_labels.append(ver_lbl)

        elif item_cat == "Modpacks":
            mod_count = item.get("mod_count", "Unknown")
            tk.Label(
                info_frame,
                text=f"Mod count: {mod_count}",
                bg=BG_CARD,
                fg=TEXT_SECONDARY,
                font=("Segoe UI", 10),
                anchor="w",
            ).pack(fill="x", pady=(0, 3))

            summary = item.get("summary") or "No description"
            desc_lbl = tk.Label(
                info_frame,
                text=f"Description: {summary}",
                bg=BG_CARD,
                fg=TEXT_SECONDARY,
                font=("Segoe UI", 9),
                anchor="w",
                justify="left",
                wraplength=wrap_len,
            )
            desc_lbl.pack(fill="x", pady=(0, 3))
            info_wrap_labels.append(desc_lbl)

            mc_ver = item.get("mc_version") or "Unknown"
            tk.Label(
                info_frame,
                text=f"Version: {mc_ver}",
                bg=BG_CARD,
                fg=TEXT_SECONDARY,
                font=("Segoe UI", 9),
                anchor="w",
            ).pack(fill="x")

    # Scroll back to top whenever a new page/search loads
    results_canvas.yview_moveto(0)


def update_pagination(data):
    global current_page, total_pages, total_items_count
    pagination = data.get("pagination", {})
    current_page = pagination.get("page", current_page)
    total_pages = max(1, pagination.get("pages", 1))
    total_items_count = pagination.get("total", 0)

    current_page_label.configure(
        text=f"Current Page: {current_page} / {total_pages}   ({RESULTS_PER_PAGE} per page)"
    )
    prev_btn.configure(state="normal" if current_page > 1 else "disabled")
    next_btn.configure(state="normal" if current_page < total_pages else "disabled")


def run_search(page=1):
    """Run the API search in a background thread so the GUI stays smooth and responsive."""
    global current_page, search_generation
    current_page = page
    search_generation += 1
    gen = search_generation

    query = main_search_entry.get_value()
    mc_version = version_search_entry.get_value()
    mod_name = mod_search_entry.get_value()
    color_hex = selected_color_hex
    category = selected_category

    search_btn.configure(state="disabled", text="Searching...")
    prev_btn.configure(state="disabled")
    next_btn.configure(state="disabled")
    status_var.set(f"Searching {category} (page {page})...")
    _show_message_in_results(f"Loading {category} (Page {page})...")

    def _worker():
        try:
            result = fetch_api_results(
                category=category,
                query=query,
                mc_version=mc_version,
                mod_name=mod_name,
                color_hex=color_hex,
                page=page,
            )
            error_msg = None
        except Exception as exc:
            result = None
            error_msg = str(exc)

        def _on_complete():
            if gen != search_generation:
                return
            search_btn.configure(state="normal", text="Search")

            if error_msg is not None:
                _show_message_in_results(
                    f"Could not fetch data from BlocksItems API:\n{error_msg}",
                    color=TEXT_ERROR,
                )
                status_var.set(f"Error: {error_msg}")
                prev_btn.configure(state="normal" if current_page > 1 else "disabled")
                next_btn.configure(state="normal" if current_page < total_pages else "disabled")
                return

            # Keep blocksitems_API.data updated with latest response
            bi.data = result
            showfounddata(result, gen)
            update_pagination(result)

            extra_note = ""
            if color_hex and category in ("Mods", "Modpacks"):
                extra_note = "   |   Note: Dominant color filter applies to Items, Blocks, and All"
            status_var.set(f"Loaded: {result.get('url', '')}{extra_note}")

        try:
            root.after(0, _on_complete)
        except tk.TclError:
            pass

    threading.Thread(target=_worker, daemon=True).start()


def go_to_entered_page(_event=None):
    page_text = goto_page_entry.get().strip()
    if page_text.isdigit():
        target_page = int(page_text)
        if 1 <= target_page <= total_pages:
            goto_page_entry.delete(0, tk.END)
            run_search(page=target_page)
            return
    status_var.set(f"Invalid page number. Enter a number between 1 and {total_pages}.")


# =============================================================================
# CUSTOM WINDOW & TASKBAR ICON
# =============================================================================
def set_windows_taskbar_app_id(app_id="blocksitems.explorer.gui"):
    """Assign a custom AppUserModelID on Windows so the taskbar uses our icon instead of python.exe's."""
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except Exception:
            pass


def apply_app_icon(window):
    """
    Load a custom window & taskbar icon from the same folder as blocksitems_GUI.py.
    Drop a file named blocksitems_icon.ico or blocksitems_icon.png (or .jpg/.webp)
    next to this script to use it automatically.
    """
    icon_path = next((APP_DIR / name for name in APP_ICON_FILES if (APP_DIR / name).is_file()), None)
    if icon_path is None:
        return

    # On Windows, .ico files can be applied directly via iconbitmap
    if icon_path.suffix.lower() == ".ico":
        try:
            window.iconbitmap(default=str(icon_path))
            return
        except tk.TclError:
            pass

    # For .png/.jpg/.webp (or as a fallback for .ico), build multi-size icons via Pillow
    try:
        with Image.open(icon_path) as raw_img:
            img = raw_img.convert("RGBA")
        resample = (
            Image.Resampling.NEAREST
            if max(img.size) <= 32
            else Image.Resampling.LANCZOS
        )
        icon_photos = []
        for size in (256, 64, 32, 16):
            scale = min(size / img.width, size / img.height)
            new_w = max(1, round(img.width * scale))
            new_h = max(1, round(img.height * scale))
            resized = img.resize((new_w, new_h), resample)
            canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            canvas.paste(resized, ((size - new_w) // 2, (size - new_h) // 2), resized)
            icon_photos.append(ImageTk.PhotoImage(canvas))

        window._app_icon_images = icon_photos  # Keep references alive so Tk doesn't drop the icon
        window.iconphoto(True, *icon_photos)
    except Exception:
        pass


# =============================================================================
# BUILD DARK-THEMED MAIN WINDOW
# =============================================================================
set_windows_taskbar_app_id()

root = tk.Tk()
root.title("Blocks & Items Explorer")
root.geometry("920x740")
root.minsize(760, 580)
root.configure(bg=BG_MAIN)
apply_app_icon(root)

# Dark scrollbar styling via ttk
style = ttk.Style(root)
style.theme_use("clam")
style.configure(
    "Dark.Vertical.TScrollbar",
    gripcount=0,
    background="#34384a",
    darkcolor="#252834",
    lightcolor="#34384a",
    troughcolor=BG_PANEL,
    bordercolor=BG_PANEL,
    arrowcolor=TEXT_SECONDARY,
)
style.map(
    "Dark.Vertical.TScrollbar",
    background=[("active", "#484e66"), ("pressed", ACCENT)],
)

# --- Header ---
header_frame = tk.Frame(root, bg=BG_MAIN)
header_frame.pack(fill="x", padx=20, pady=(14, 6))

tk.Label(
    header_frame,
    text="Blocks & Items Explorer",
    bg=BG_MAIN,
    fg=TEXT_PRIMARY,
    font=("Segoe UI", 16, "bold"),
).pack(side="left")

# --- 5 Category Buttons (Items, Blocks, Mods, Modpacks, All) ---
category_frame = tk.Frame(root, bg=BG_MAIN)
category_frame.pack(fill="x", padx=20, pady=(4, 8))

category_buttons = {}
for idx, cat in enumerate(CATEGORIES):
    btn = tk.Button(
        category_frame,
        text=cat,
        command=lambda c=cat: select_category(c),
        bg=BTN_INACTIVE,
        fg=TEXT_PRIMARY,
        relief="flat",
        bd=0,
        padx=14,
        pady=9,
        cursor="hand2",
        font=("Segoe UI", 10),
    )
    btn.grid(row=0, column=idx, sticky="ew", padx=(0 if idx == 0 else 6, 0))
    category_frame.grid_columnconfigure(idx, weight=1)
    category_buttons[cat] = btn

# --- Search Bar & Optional Filters Panel ---
search_panel = tk.Frame(
    root,
    bg=BG_PANEL,
    highlightbackground=BORDER_COLOR,
    highlightthickness=1,
    padx=14,
    pady=12,
)
search_panel.pack(fill="x", padx=20, pady=(0, 10))

# Main search row
main_search_row = tk.Frame(search_panel, bg=BG_PANEL)
main_search_row.pack(fill="x", pady=(0, 10))

main_search_entry = PlaceholderEntry(
    main_search_row,
    placeholder="What Item are you looking for?",
    bg=BG_INPUT,
    fg=TEXT_PRIMARY,
    insertbackground=TEXT_PRIMARY,
    relief="flat",
    font=("Segoe UI", 11),
    highlightbackground=BORDER_COLOR,
    highlightcolor=ACCENT,
    highlightthickness=1,
)
main_search_entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 10))
main_search_entry.bind("<Return>", lambda _e: run_search(page=1))

search_btn = tk.Button(
    main_search_row,
    text="Search",
    command=lambda: run_search(page=1),
    bg=ACCENT,
    fg="#ffffff",
    activebackground=ACCENT_HOVER,
    activeforeground="#ffffff",
    disabledforeground="#c9d1d9",
    relief="flat",
    bd=0,
    padx=22,
    pady=6,
    cursor="hand2",
    font=("Segoe UI", 10, "bold"),
)
search_btn.pack(side="right")

# Optional filters row: MC Version + Mod Name + Color Picker
filters_row = tk.Frame(search_panel, bg=BG_PANEL)
filters_row.pack(fill="x")

# 1. Optional Minecraft Version search bar
version_group = tk.Frame(filters_row, bg=BG_PANEL)
version_group.pack(side="left", padx=(0, 14))

tk.Label(
    version_group,
    text="MC Version (optional)",
    bg=BG_PANEL,
    fg=TEXT_SECONDARY,
    font=("Segoe UI", 8),
).pack(anchor="w", pady=(0, 2))

version_search_entry = PlaceholderEntry(
    version_group,
    placeholder="e.g. 1.20.1",
    width=15,
    bg=BG_INPUT,
    fg=TEXT_PRIMARY,
    insertbackground=TEXT_PRIMARY,
    relief="flat",
    font=("Segoe UI", 9),
    highlightbackground=BORDER_COLOR,
    highlightcolor=ACCENT,
    highlightthickness=1,
)
version_search_entry.pack(ipady=4)
version_search_entry.bind("<Return>", lambda _e: run_search(page=1))

# 2. Optional Mod Name search bar
mod_group = tk.Frame(filters_row, bg=BG_PANEL)
mod_group.pack(side="left", padx=(0, 18))

tk.Label(
    mod_group,
    text="Mod Name (optional)",
    bg=BG_PANEL,
    fg=TEXT_SECONDARY,
    font=("Segoe UI", 8),
).pack(anchor="w", pady=(0, 2))

mod_search_entry = PlaceholderEntry(
    mod_group,
    placeholder="e.g. Create",
    width=22,
    bg=BG_INPUT,
    fg=TEXT_PRIMARY,
    insertbackground=TEXT_PRIMARY,
    relief="flat",
    font=("Segoe UI", 9),
    highlightbackground=BORDER_COLOR,
    highlightcolor=ACCENT,
    highlightthickness=1,
)
mod_search_entry.pack(ipady=4)
mod_search_entry.bind("<Return>", lambda _e: run_search(page=1))

# 3. Optional Color Picker
color_group = tk.Frame(filters_row, bg=BG_PANEL)
color_group.pack(side="left")

tk.Label(
    color_group,
    text="Color (optional - Items / Blocks / All)",
    bg=BG_PANEL,
    fg=TEXT_SECONDARY,
    font=("Segoe UI", 8),
).pack(anchor="w", pady=(0, 2))

color_controls = tk.Frame(color_group, bg=BG_PANEL)
color_controls.pack(anchor="w")

color_preview = tk.Frame(
    color_controls,
    width=26,
    height=26,
    bg=BG_INPUT,
    highlightbackground=BORDER_COLOR,
    highlightthickness=1,
    cursor="hand2",
)
color_preview.pack(side="left", padx=(0, 6))
color_preview.pack_propagate(False)
color_preview.bind("<Button-1>", lambda _e: pick_color())

pick_color_btn = tk.Button(
    color_controls,
    text="Pick Color",
    command=pick_color,
    bg=BTN_INACTIVE,
    fg=TEXT_PRIMARY,
    activebackground=BTN_INACTIVE_HOVER,
    activeforeground=TEXT_PRIMARY,
    relief="flat",
    bd=0,
    padx=10,
    pady=4,
    cursor="hand2",
    font=("Segoe UI", 9),
)
pick_color_btn.pack(side="left", padx=(0, 6))

color_hex_label = tk.Label(
    color_controls,
    text="None",
    width=8,
    bg=BG_PANEL,
    fg=TEXT_MUTED,
    font=("Consolas", 9),
    anchor="w",
)
color_hex_label.pack(side="left", padx=(0, 4))

clear_color_btn = tk.Button(
    color_controls,
    text="Clear",
    command=clear_color,
    bg=BTN_CLEAR,
    fg=BTN_CLEAR_TEXT,
    activebackground=BTN_CLEAR_HOVER,
    activeforeground=BTN_CLEAR_TEXT,
    relief="flat",
    bd=0,
    padx=8,
    pady=4,
    cursor="hand2",
    font=("Segoe UI", 8),
)
clear_color_btn.pack(side="left")

# --- Middle Scrollable Results Window ---
results_outer = tk.Frame(
    root,
    bg=BG_PANEL,
    highlightbackground=BORDER_COLOR,
    highlightthickness=1,
)
results_outer.pack(fill="both", expand=True, padx=20, pady=(0, 10))

results_header = tk.Frame(results_outer, bg=BG_PANEL, padx=12, pady=8)
results_header.pack(fill="x")

results_header_label = tk.Label(
    results_header,
    text="Results",
    bg=BG_PANEL,
    fg=TEXT_PRIMARY,
    font=("Segoe UI", 10, "bold"),
)
results_header_label.pack(side="left")

tk.Frame(results_outer, bg=BORDER_COLOR, height=1).pack(fill="x")

canvas_wrapper = tk.Frame(results_outer, bg=BG_PANEL)
canvas_wrapper.pack(fill="both", expand=True)

results_canvas = tk.Canvas(
    canvas_wrapper,
    bg=BG_PANEL,
    highlightthickness=0,
    bd=0,
)
results_scrollbar = ttk.Scrollbar(
    canvas_wrapper,
    orient="vertical",
    command=results_canvas.yview,
    style="Dark.Vertical.TScrollbar",
)
results_canvas.configure(yscrollcommand=results_scrollbar.set)

results_scrollbar.pack(side="right", fill="y")
results_canvas.pack(side="left", fill="both", expand=True)

results_container = tk.Frame(results_canvas, bg=BG_PANEL)
canvas_window = results_canvas.create_window((0, 0), window=results_container, anchor="nw")


def _on_container_configure(_event):
    results_canvas.configure(scrollregion=results_canvas.bbox("all"))


def _on_canvas_configure(event):
    results_canvas.itemconfig(canvas_window, width=event.width)
    new_wrap = max(260, event.width - 170)
    for lbl in info_wrap_labels:
        if lbl.winfo_exists():
            lbl.configure(wraplength=new_wrap)


def _on_mousewheel(event):
    bbox = results_canvas.bbox("all")
    if bbox and (bbox[3] - bbox[1]) > results_canvas.winfo_height():
        results_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


results_container.bind("<Configure>", _on_container_configure)
results_canvas.bind("<Configure>", _on_canvas_configure)
results_canvas.bind_all("<MouseWheel>", _on_mousewheel)

# --- Bottom Pagination Bar (Go to Page + Current Page right next to it) ---
pagination_bar = tk.Frame(
    root,
    bg=BG_PANEL,
    highlightbackground=BORDER_COLOR,
    highlightthickness=1,
    padx=14,
    pady=8,
)
pagination_bar.pack(fill="x", padx=20, pady=(0, 8))

prev_btn = tk.Button(
    pagination_bar,
    text="< Prev",
    command=lambda: run_search(page=max(1, current_page - 1)),
    bg=BTN_INACTIVE,
    fg=TEXT_PRIMARY,
    activebackground=BTN_INACTIVE_HOVER,
    activeforeground=TEXT_PRIMARY,
    disabledforeground=TEXT_MUTED,
    relief="flat",
    bd=0,
    padx=12,
    pady=4,
    cursor="hand2",
    font=("Segoe UI", 9),
    state="disabled",
)
prev_btn.pack(side="left")

# Center section: Go to Page input right next to Current Page indicator
page_center = tk.Frame(pagination_bar, bg=BG_PANEL)
page_center.pack(side="left", expand=True)

tk.Label(
    page_center,
    text="Go to Page:",
    bg=BG_PANEL,
    fg=TEXT_SECONDARY,
    font=("Segoe UI", 9),
).pack(side="left", padx=(0, 6))

goto_page_entry = tk.Entry(
    page_center,
    width=6,
    bg=BG_INPUT,
    fg=TEXT_PRIMARY,
    insertbackground=TEXT_PRIMARY,
    relief="flat",
    font=("Segoe UI", 9),
    highlightbackground=BORDER_COLOR,
    highlightcolor=ACCENT,
    highlightthickness=1,
    justify="center",
)
goto_page_entry.pack(side="left", ipady=3)
goto_page_entry.bind("<Return>", go_to_entered_page)

goto_btn = tk.Button(
    page_center,
    text="Go",
    command=go_to_entered_page,
    bg=ACCENT,
    fg="#ffffff",
    activebackground=ACCENT_HOVER,
    activeforeground="#ffffff",
    relief="flat",
    bd=0,
    padx=10,
    pady=3,
    cursor="hand2",
    font=("Segoe UI", 9, "bold"),
)
goto_btn.pack(side="left", padx=(6, 18))

current_page_label = tk.Label(
    page_center,
    text=f"Current Page: 1 / 1   ({RESULTS_PER_PAGE} per page)",
    bg=BG_PANEL,
    fg=TEXT_PRIMARY,
    font=("Segoe UI", 9, "bold"),
)
current_page_label.pack(side="left")

next_btn = tk.Button(
    pagination_bar,
    text="Next >",
    command=lambda: run_search(page=min(total_pages, current_page + 1)),
    bg=BTN_INACTIVE,
    fg=TEXT_PRIMARY,
    activebackground=BTN_INACTIVE_HOVER,
    activeforeground=TEXT_PRIMARY,
    disabledforeground=TEXT_MUTED,
    relief="flat",
    bd=0,
    padx=12,
    pady=4,
    cursor="hand2",
    font=("Segoe UI", 9),
    state="disabled",
)
next_btn.pack(side="right")

# --- Bottom Status Bar ---
status_var = tk.StringVar(value="Ready.")
status_bar = tk.Label(
    root,
    textvariable=status_var,
    bg="#0e0f13",
    fg=TEXT_MUTED,
    font=("Consolas", 8),
    anchor="w",
    padx=14,
    pady=5,
)
status_bar.pack(fill="x", side="bottom")


def _on_close():
    image_executor.shutdown(wait=False, cancel_futures=True)
    http_session.close()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", _on_close)

# Initialize default category & welcome prompt
select_category(CATEGORIES[0])
_show_message_in_results(
    "Choose a category above (Items, Blocks, Mods, Modpacks, or All),\n"
    "type your search term, and press Enter or click Search."
)

if __name__ == "__main__":
    root.mainloop()
