import tkinter as tk
from tkinter import colorchooser

# Optional: Uncomment these imports later when you load real API data and images
# import requests
# from io import BytesIO
# from PIL import Image, ImageTk


# =============================================================================
# PLACEHOLDER CONFIGURATION
# Replace the placeholder URLs and data below with your real API endpoints.
# =============================================================================
BASE_URL = "PLACEHOLDER_BASE_URL"  # e.g. "https://blocksitems.com/api/2026.1.3"

CATEGORIES = ["Items", "Blocks", "Mods", "Modpacks", "All"]

# Placeholder API response matching the exact structure used in blocksitems_API.py
# plus an "image_url" placeholder field for the item picture.
PLACEHOLDER_DATA = {
    "data": [
        {
            "display_name": "Placeholder Item 1",
            "mod": {"display_name": "Placeholder Mod A"},
            "mc_versions": ["1.20.1", "1.20.4", "1.21"],
            "image_url": "PLACEHOLDER_IMAGE_URL_1",
        },
        {
            "display_name": "Placeholder Item 2",
            "mod": {"display_name": "Placeholder Mod B"},
            "mc_versions": ["1.19.2", "1.20.1"],
            "image_url": "PLACEHOLDER_IMAGE_URL_2",
        },
        {
            "display_name": "Placeholder Item 3",
            "mod": {"display_name": "Placeholder Mod C"},
            "mc_versions": ["1.18.2", "1.19.2", "1.20.1", "1.21.1"],
            "image_url": "PLACEHOLDER_IMAGE_URL_3",
        },
    ],
    "pagination": {
        "limit": 10,
        "page": 1,
        "total": 5,
    },
}


# =============================================================================
# GLOBAL STATE VARIABLES
# =============================================================================
selected_category = "Items"
selected_color_hex = None  # Optional color picker result (e.g. "#3498db") or None
current_page = 1
total_pages = 1
loaded_images = []  # Keeps references to loaded PhotoImages so Tkinter doesn't clear them


# =============================================================================
# THEME COLORS
# =============================================================================
BG_MAIN = "#1e1f26"
BG_PANEL = "#282a36"
BG_CARD = "#2f3241"
BG_INPUT = "#16171d"
BG_IMAGE_BOX = "#1a1b23"
BORDER_COLOR = "#44475a"

ACCENT = "#2ea043"
ACCENT_HOVER = "#3fb950"
BTN_INACTIVE = "#343746"
BTN_INACTIVE_HOVER = "#414558"
BTN_CLEAR = "#4a3238"
BTN_CLEAR_TEXT = "#f38ba8"

TEXT_PRIMARY = "#f8f8f2"
TEXT_SECONDARY = "#a6accd"
TEXT_MUTED = "#6c7086"


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

    def get_value(self):
        """Return the typed text, or an empty string if only the placeholder is shown."""
        if self.showing_placeholder:
            return ""
        return self.get().strip()


# =============================================================================
# PLACEHOLDER API & IMAGE FUNCTIONS
# Replace the bodies of these functions with your real URLs / API calls.
# =============================================================================
def build_url(category, query, mc_version="", mod_name="", color_hex=None, page=1):
    """
    Build the API request URL from the GUI inputs.
    PLACEHOLDER: Replace the endpoint paths and query parameter names with your real API format.
    """
    if category != "All":
        url = f"{BASE_URL}/{category.lower()}?q={query.lower()}"
    else:
        url = f"{BASE_URL}/search?q={query.lower()}&scope=all"

    # Optional Minecraft Version filter (PLACEHOLDER parameter name)
    if mc_version:
        url += f"&PLACEHOLDER_VERSION_PARAM={mc_version}"

    # Optional Mod Name filter (PLACEHOLDER parameter name)
    if mod_name:
        url += f"&PLACEHOLDER_MOD_PARAM={mod_name}"

    # Optional Color Hex filter (PLACEHOLDER parameter name)
    if color_hex:
        url += f"&PLACEHOLDER_COLOR_PARAM={color_hex}"

    # Pagination parameter (PLACEHOLDER parameter name)
    url += f"&page={page}"
    return url


def fetch_data(url):
    """
    Fetch JSON data from the API.
    PLACEHOLDER: Uncomment the requests lines below to fetch real data from your URL.
    """
    # response = requests.get(url)
    # return response.json()

    # Return placeholder data with the current page updated for previewing the GUI
    placeholder_response = {
        "data": PLACEHOLDER_DATA["data"],
        "pagination": {
            "limit": PLACEHOLDER_DATA["pagination"]["limit"],
            "page": current_page,
            "total": PLACEHOLDER_DATA["pagination"]["total"],
        },
    }
    return placeholder_response


def load_item_image(image_url, image_label):
    """
    Load an item image into the given Label widget.
    PLACEHOLDER: Replace this with your real image download/display code (e.g. requests + Pillow).
    """
    # Example for when you hook up real image URLs (requires Pillow: pip install pillow):
    #
    # if image_url:
    #     response = requests.get(image_url)
    #     pil_image = Image.open(BytesIO(response.content)).resize((80, 80))
    #     tk_image = ImageTk.PhotoImage(pil_image)
    #     loaded_images.append(tk_image)
    #     image_label.configure(image=tk_image, text="")
    #     return

    image_label.configure(
        text=f"Image\nPlaceholder\n\n({image_url or 'No URL'})",
        fg=TEXT_MUTED,
    )


# =============================================================================
# GUI ACTIONS
# =============================================================================
def select_category(category_name):
    global selected_category, current_page
    selected_category = category_name
    current_page = 1

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

    status_var.set(f"Category selected: {selected_category}")


def pick_color():
    """Open the color picker and save the chosen hex code to `selected_color_hex`."""
    global selected_color_hex
    initial_color = selected_color_hex if selected_color_hex else "#2ea043"
    _rgb, hex_code = colorchooser.askcolor(
        color=initial_color,
        title="Pick a Color (Optional)",
    )

    if hex_code:
        selected_color_hex = hex_code
        color_preview.configure(bg=selected_color_hex)
        color_hex_label.configure(text=selected_color_hex, fg=TEXT_PRIMARY)


def clear_color():
    """Reset the optional color selection back to None."""
    global selected_color_hex
    selected_color_hex = None
    color_preview.configure(bg=BG_INPUT)
    color_hex_label.configure(text="None", fg=TEXT_MUTED)


def showfounddata(data):
    """
    Display found items inside the middle scrollable results window,
    showing the same fields as showfounddata() in blocksitems_API.py
    plus a dedicated space for each item's picture.
    """
    # Clear previous result cards and image references
    for widget in results_container.winfo_children():
        widget.destroy()
    loaded_images.clear()

    items = data.get("data", [])
    results_header_label.configure(
        text=f"Found {selected_category} ({len(items)} shown)"
    )

    if not items:
        empty_label = tk.Label(
            results_container,
            text="No results found.",
            bg=BG_PANEL,
            fg=TEXT_MUTED,
            font=("Segoe UI", 11),
            pady=40,
        )
        empty_label.pack(fill="x")
        return

    category_singular = selected_category.removesuffix("s")

    for item in items:
        card = tk.Frame(
            results_container,
            bg=BG_CARD,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
            padx=12,
            pady=10,
        )
        card.pack(fill="x", padx=10, pady=6)

        # --- Extra Space for the Found Item's Picture ---
        image_frame = tk.Frame(
            card,
            width=96,
            height=96,
            bg=BG_IMAGE_BOX,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
        )
        image_frame.pack(side="left", padx=(0, 14))
        image_frame.pack_propagate(False)

        image_label = tk.Label(
            image_frame,
            bg=BG_IMAGE_BOX,
            fg=TEXT_MUTED,
            font=("Segoe UI", 7),
            justify="center",
            wraplength=88,
        )
        image_label.pack(expand=True, fill="both")
        load_item_image(item.get("image_url", "PLACEHOLDER_IMAGE_URL"), image_label)

        # --- Item Info (matching showfounddata in blocksitems_API.py) ---
        info_frame = tk.Frame(card, bg=BG_CARD)
        info_frame.pack(side="left", fill="both", expand=True)

        display_name = item.get("display_name", "Unknown")
        tk.Label(
            info_frame,
            text=f"{category_singular}: {display_name}",
            bg=BG_CARD,
            fg=TEXT_PRIMARY,
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        # Show Mod name for Items and Blocks (or whenever mod data exists in "All")
        if selected_category in ("Items", "Blocks") or (
            selected_category == "All" and "mod" in item
        ):
            mod_name = item.get("mod", {}).get("display_name", "Unknown Mod")
            tk.Label(
                info_frame,
                text=f"Mod: {mod_name}",
                bg=BG_CARD,
                fg=TEXT_SECONDARY,
                font=("Segoe UI", 10),
                anchor="w",
            ).pack(fill="x", pady=(0, 4))

        versions = item.get("mc_versions", [])
        versions_text = ", ".join(versions) if versions else "None"
        tk.Label(
            info_frame,
            text=f"Versions: {versions_text}",
            bg=BG_CARD,
            fg=TEXT_SECONDARY,
            font=("Segoe UI", 9),
            anchor="w",
            justify="left",
            wraplength=560,
        ).pack(fill="x")

    # Scroll back to top after updating results
    results_canvas.yview_moveto(0)


def update_pagination(data):
    global current_page, total_pages
    pagination = data.get("pagination", {})
    limit = pagination.get("limit", 0)
    current_page = pagination.get("page", current_page)
    total_pages = max(1, pagination.get("total", 1))

    page_info_label.configure(
        text=f"{selected_category} per page: {limit}   |   Page {current_page} of {total_pages}"
    )
    prev_btn.configure(state="normal" if current_page > 1 else "disabled")
    next_btn.configure(state="normal" if current_page < total_pages else "disabled")


def run_search(page=1):
    global current_page
    current_page = page

    query = main_search_entry.get_value()
    mc_version = version_search_entry.get_value()
    mod_name = mod_search_entry.get_value()

    url = build_url(
        category=selected_category,
        query=query,
        mc_version=mc_version,
        mod_name=mod_name,
        color_hex=selected_color_hex,
        page=current_page,
    )

    data = fetch_data(url)
    showfounddata(data)
    update_pagination(data)

    color_info = selected_color_hex if selected_color_hex else "None"
    status_var.set(f"URL: {url}   |   Color Hex: {color_info}")


def go_to_entered_page(_event=None):
    page_text = goto_page_entry.get().strip()
    if page_text.isdigit():
        target_page = int(page_text)
        if 1 <= target_page <= total_pages:
            run_search(page=target_page)
            goto_page_entry.delete(0, tk.END)
            return
    status_var.set(f"Please enter a valid page number between 1 and {total_pages}.")


# =============================================================================
# BUILD MAIN WINDOW
# =============================================================================
root = tk.Tk()
root.title("Blocks & Items API Explorer")
root.geometry("860x700")
root.minsize(720, 560)
root.configure(bg=BG_MAIN)

# --- Top Header ---
header_frame = tk.Frame(root, bg=BG_MAIN)
header_frame.pack(fill="x", padx=20, pady=(14, 6))

tk.Label(
    header_frame,
    text="Blocks & Items Search",
    bg=BG_MAIN,
    fg=TEXT_PRIMARY,
    font=("Segoe UI", 16, "bold"),
).pack(anchor="w")

# --- Category Buttons (Items, Blocks, Mods, Modpacks, All) ---
category_frame = tk.Frame(root, bg=BG_MAIN, padx=20, pady=6)
category_frame.pack(fill="x")

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
        pady=8,
        cursor="hand2",
        font=("Segoe UI", 10),
    )
    btn.grid(row=0, column=idx, sticky="ew", padx=(0 if idx == 0 else 6, 0))
    category_frame.grid_columnconfigure(idx, weight=1)
    category_buttons[cat] = btn

# --- Main Search Bar ---
search_panel = tk.Frame(
    root,
    bg=BG_PANEL,
    highlightbackground=BORDER_COLOR,
    highlightthickness=1,
    padx=14,
    pady=12,
)
search_panel.pack(fill="x", padx=20, pady=8)

main_search_row = tk.Frame(search_panel, bg=BG_PANEL)
main_search_row.pack(fill="x", pady=(0, 10))

main_search_entry = PlaceholderEntry(
    main_search_row,
    placeholder="Search for an item, block, mod, or modpack...",
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
    relief="flat",
    bd=0,
    padx=20,
    pady=6,
    cursor="hand2",
    font=("Segoe UI", 10, "bold"),
)
search_btn.pack(side="right")

# --- Optional Filters Row (2 Smaller Searchbars + Color Picker) ---
filters_row = tk.Frame(search_panel, bg=BG_PANEL)
filters_row.pack(fill="x")

# 1. Optional Minecraft Version Searchbar
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

# 2. Optional Mod Name Searchbar
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
    text="Color (optional)",
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
    activebackground="#5e3e46",
    activeforeground=BTN_CLEAR_TEXT,
    relief="flat",
    bd=0,
    padx=8,
    pady=4,
    cursor="hand2",
    font=("Segoe UI", 8),
)
clear_color_btn.pack(side="left")

# --- Middle Window: Found Items + Picture Space ---
results_outer = tk.Frame(
    root,
    bg=BG_PANEL,
    highlightbackground=BORDER_COLOR,
    highlightthickness=1,
)
results_outer.pack(fill="both", expand=True, padx=20, pady=(4, 8))

results_header = tk.Frame(results_outer, bg=BG_PANEL, padx=12, pady=8)
results_header.pack(fill="x")

results_header_label = tk.Label(
    results_header,
    text="Found Items",
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
results_scrollbar = tk.Scrollbar(
    canvas_wrapper,
    orient="vertical",
    command=results_canvas.yview,
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


def _on_mousewheel(event):
    bbox = results_canvas.bbox("all")
    if bbox and (bbox[3] - bbox[1]) > results_canvas.winfo_height():
        results_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


results_container.bind("<Configure>", _on_container_configure)
results_canvas.bind("<Configure>", _on_canvas_configure)
results_canvas.bind_all("<MouseWheel>", _on_mousewheel)

# --- Bottom Pagination Bar ---
pagination_frame = tk.Frame(root, bg=BG_MAIN, padx=20, pady=4)
pagination_frame.pack(fill="x")

prev_btn = tk.Button(
    pagination_frame,
    text="< Prev",
    command=lambda: run_search(page=max(1, current_page - 1)),
    bg=BTN_INACTIVE,
    fg=TEXT_PRIMARY,
    activebackground=BTN_INACTIVE_HOVER,
    activeforeground=TEXT_PRIMARY,
    relief="flat",
    bd=0,
    padx=12,
    pady=4,
    cursor="hand2",
    font=("Segoe UI", 9),
)
prev_btn.pack(side="left")

page_info_label = tk.Label(
    pagination_frame,
    text="Page 1 of 1",
    bg=BG_MAIN,
    fg=TEXT_SECONDARY,
    font=("Segoe UI", 9),
)
page_info_label.pack(side="left", padx=12)

next_btn = tk.Button(
    pagination_frame,
    text="Next >",
    command=lambda: run_search(page=min(total_pages, current_page + 1)),
    bg=BTN_INACTIVE,
    fg=TEXT_PRIMARY,
    activebackground=BTN_INACTIVE_HOVER,
    activeforeground=TEXT_PRIMARY,
    relief="flat",
    bd=0,
    padx=12,
    pady=4,
    cursor="hand2",
    font=("Segoe UI", 9),
)
next_btn.pack(side="left")

# Go-to-page controls on the right
goto_btn = tk.Button(
    pagination_frame,
    text="Go",
    command=go_to_entered_page,
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
goto_btn.pack(side="right")

goto_page_entry = tk.Entry(
    pagination_frame,
    width=5,
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
goto_page_entry.pack(side="right", padx=6, ipady=3)
goto_page_entry.bind("<Return>", go_to_entered_page)

tk.Label(
    pagination_frame,
    text="Go to Page:",
    bg=BG_MAIN,
    fg=TEXT_SECONDARY,
    font=("Segoe UI", 9),
).pack(side="right")

# --- Status Bar (shows placeholder URL & saved color hex) ---
status_var = tk.StringVar(value="Ready.")
status_bar = tk.Label(
    root,
    textvariable=status_var,
    bg="#16171d",
    fg=TEXT_MUTED,
    font=("Consolas", 8),
    anchor="w",
    padx=12,
    pady=5,
)
status_bar.pack(fill="x", side="bottom", pady=(6, 0))

# Initialize default category and display placeholder items on startup
select_category("Items")
run_search(page=1)

root.mainloop()
