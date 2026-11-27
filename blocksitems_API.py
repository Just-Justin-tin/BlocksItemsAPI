import requests

url = "https://blocksitems.com/api/2026.1.3"
userinputcat = ""
userinputend = "No"
categories = ["Items", "Blocks", "Mods", "Modpacks", "All"]


def showfounddata():
    datenlange = len(data["data"])
    for i in range(datenlange):
        if userinputcat != "All":
            print(f"{userinputcat.strip("s")}: {data["data"][i]["display_name"]}\n")
        else:
            print(f"{cat.strip("s")}: {data["data"][i]["display_name"]}\n")

        match userinputcat:
            case "Items" | "Blocks":
                print(f"Mod: {data["data"][i]["mod"]["display_name"]}\n")
            case "Mods":
                print(f"Mod: {data["data"][i]["display_name"]}\nLoader:{data["data"][i]["loaders"]}\n")
            case "Modpacks":
                print(f"Mod count: {data["data"][i]["mod_count"]}\nDiscription:{data["data"][i]["summary"]}\n")
                
        match userinputcat:
            case "Items" | "Blocks" | "Mods":
                print(f"Versions: ")
                for j in data["data"][i]["mc_versions"]:
                    print(j)
            case "Modpacks":
                print(f"Version: ")
                print(data["data"][i]["mc_version"])  
        print("\n")

# =============================================================================
# ADDED FILTER CODE FOR GUI (Minecraft Version, Mod Name, Color)
# =============================================================================
import colorsys
from concurrent.futures import ThreadPoolExecutor
import math

BASE_API_URL = url.rstrip("/")
COLOR_SCAN_LIMIT = 500  # Max items/blocks per API page when scanning for dominant color
COLOR_SCAN_MAX_PAGES = 5  # Scan up to 5 pages spread across A-Z (up to 2,500 candidates)
COLOR_SEARCH_API_LIMIT = 100  # Max limit accepted by /colors/search
_color_search_cache = {}  # Caches filtered color results so switching pages is instant


def format_mod_slug(mod_name):
    """Convert a Mod Name (e.g. 'Create') to the lowercase slug expected by the API."""
    return mod_name.strip().lower().replace(" ", "-") if mod_name else ""


def _hex_to_rgb(hex_str):
    if not hex_str:
        return None
    cleaned = hex_str.lstrip("#")
    if len(cleaned) != 6:
        return None
    try:
        return (int(cleaned[0:2], 16), int(cleaned[2:4], 16), int(cleaned[4:6], 16))
    except ValueError:
        return None


def _rgb_distance(hex_a, hex_b):
    """Euclidean RGB distance (0..441.7) between two hex colors."""
    rgb_a = _hex_to_rgb(hex_a)
    rgb_b = _hex_to_rgb(hex_b)
    if not rgb_a or not rgb_b:
        return float("inf")
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(rgb_a, rgb_b)))


def get_dominant_hex(item):
    """Return the dominant color hex string of an item/block, or None."""
    colors = item.get("colors") or {}
    return colors.get("dominant") or item.get("_matched_hex")


def dominant_color_distance(item, target_hex):
    """Compute Euclidean RGB distance from an item/block's dominant color to target_hex."""
    dominant = get_dominant_hex(item)
    if not dominant:
        return float("inf")
    return _rgb_distance(dominant, target_hex)


def matches_dominant_color(dominant_hex, target_hex):
    """
    Return True if `dominant_hex` closely matches `target_hex` in HSV + RGB space.
    - For colorful targets (red, green, blue, etc.): requires similar hue, non-gray
      saturation, and close RGB distance so unrelated colors/grays are filtered out.
    - For dark/neutral targets (black, white, gray): requires low saturation/brightness match.
    """
    dom_rgb = _hex_to_rgb(dominant_hex)
    tgt_rgb = _hex_to_rgb(target_hex)
    if not dom_rgb or not tgt_rgb:
        return False

    dh, ds, dv = colorsys.rgb_to_hsv(dom_rgb[0] / 255.0, dom_rgb[1] / 255.0, dom_rgb[2] / 255.0)
    th, ts, tv = colorsys.rgb_to_hsv(tgt_rgb[0] / 255.0, tgt_rgb[1] / 255.0, tgt_rgb[2] / 255.0)
    dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(dom_rgb, tgt_rgb)))

    # Very dark target (e.g. black)
    if tv <= 0.15:
        return dv <= 0.25 and dist <= 85

    # Neutral target (white / gray)
    if ts <= 0.25:
        return ds <= 0.28 and dist <= 95

    # Colorful target: enforce hue proximity (~36 deg), colorfulness, and RGB closeness
    hue_diff = min(abs(th - dh), 1.0 - abs(th - dh))
    return ds >= 0.18 and dv >= 0.15 and hue_diff <= 0.10 and dist <= 165


def apply_filter_params(category, params, query="", mc_version="", mod_name=""):
    """Add optional Minecraft Version and Mod Name query parameters for the API request."""
    mod_slug = format_mod_slug(mod_name)
    if category in ("Items", "Blocks", "Modpacks"):
        if mc_version:
            params["mc_version"] = mc_version
        if mod_slug:
            params["mod"] = mod_slug
    elif category == "Mods" and mod_name and not query:
        params["q"] = mod_name.lower()
    return params


def attach_item_colors(items, session=None):
    """
    Fetch `colors` (including `dominant`) for items via the bulk POST /lookup endpoint,
    since GET /items omits the `colors` field.
    """
    ids = [it["full_id"] for it in items if it.get("full_id")]
    if not ids:
        return items

    client = session or requests
    response = client.post(
        f"{BASE_API_URL}/lookup",
        json={"ids": ids[:1000], "fields": ["colors"]},
        timeout=20,
    )
    response.raise_for_status()
    lookup_results = response.json().get("results") or {}

    for it in items:
        entry = lookup_results.get(it.get("full_id")) or {}
        color_obj = (entry.get("item") or entry.get("block") or {}).get("colors")
        if color_obj:
            it["colors"] = color_obj
    return items


def filter_by_dominant_color(items, color_hex):
    """Keep only items/blocks whose dominant color matches `color_hex`, sorted closest-first."""
    matched = [
        it for it in items
        if matches_dominant_color(get_dominant_hex(it), color_hex)
    ]
    matched.sort(key=lambda it: dominant_color_distance(it, color_hex))
    return matched


def filter_color_search_blocks(entries, mc_version="", mod_name=""):
    """Filter /colors/search block entries locally by Minecraft Version and Mod Name."""
    mod_slug = format_mod_slug(mod_name)
    results = []
    for entry in entries:
        block = entry.get("block") or {}
        if mc_version and mc_version not in (block.get("mc_versions") or []):
            continue
        if mod_slug:
            b_mod = block.get("mod") or {}
            mod_match = (
                mod_slug in (b_mod.get("slug") or "").lower()
                or mod_name.lower() in (b_mod.get("display_name") or "").lower()
            )
            if not mod_match:
                continue
        block_copy = dict(block)
        block_copy["_category"] = "Blocks"
        block_copy["_matched_hex"] = entry.get("hex")
        results.append(block_copy)
    return results


def search_blocks_by_color(color_hex, mc_version="", mod_name="", page=1, limit=50, session=None):
    """Query the /colors/search endpoint and filter/paginate matching blocks."""
    client = session or requests
    params = {
        "hex": color_hex.lstrip("#"),
        "limit": COLOR_SEARCH_API_LIMIT,
    }
    response = client.get(f"{BASE_API_URL}/colors/search", params=params, timeout=15)
    response.raise_for_status()
    payload = response.json()

    results = filter_color_search_blocks(
        payload.get("data", []),
        mc_version=mc_version,
        mod_name=mod_name,
    )
    total = len(results)
    total_pages = max(1, math.ceil(total / limit))
    safe_page = min(max(1, page), total_pages)
    start = (safe_page - 1) * limit
    return {
        "data": results[start:start + limit],
        "pagination": {
            "page": safe_page,
            "limit": limit,
            "pages": total_pages,
            "total": total,
        },
        "url": response.url,
    }


def _pick_sample_pages(api_pages, max_pages=COLOR_SCAN_MAX_PAGES):
    """Choose up to `max_pages` pages evenly spread across 1..api_pages (covers A through Z)."""
    if api_pages <= max_pages:
        return list(range(1, api_pages + 1))
    step = (api_pages - 1) / (max_pages - 1)
    pages = sorted({1, api_pages, *(round(1 + i * step) for i in range(max_pages))})
    return pages


def _fetch_page_with_colors(client, category, endpoint, base_params, page_num):
    """Fetch one API page of Items/Blocks and attach `colors` via /lookup if category is Items."""
    params = dict(base_params)
    params["page"] = page_num
    response = client.get(endpoint, params=params, timeout=20)
    response.raise_for_status()
    payload = response.json()

    items = []
    for entry in payload.get("data", []):
        item_copy = dict(entry)
        item_copy["_category"] = category
        items.append(item_copy)

    # /items doesn't return colors directly, so fetch dominant colors in one bulk /lookup call
    if category == "Items" and items:
        attach_item_colors(items, session=client)

    return items, payload, response.url


def search_with_color_filter(category, query="", mc_version="", mod_name="", color_hex=None, page=1, limit=50, session=None):
    """
    Search Items or Blocks and filter strictly by their dominant color (`colors.dominant`):
    - Blocks without text/mod/version filters use /colors/search directly (global database match).
    - Items and filtered Blocks scan up to 5 evenly-spaced pages (up to 2,500 records across A-Z),
      attach `colors.dominant` via bulk /lookup for Items, filter by dominant color, and paginate.
    """
    client = session or requests

    # Fast global color search when browsing Blocks purely by color
    if category == "Blocks" and not query and not mc_version and not mod_name:
        return search_blocks_by_color(
            color_hex=color_hex,
            page=page,
            limit=limit,
            session=client,
        )

    cache_key = (category, query.lower(), mc_version, format_mod_slug(mod_name), color_hex.lower())
    if cache_key in _color_search_cache:
        matched, cached_url = _color_search_cache[cache_key]
    else:
        endpoint = f"{BASE_API_URL}/{category.lower()}"
        base_params = {
            "limit": COLOR_SCAN_LIMIT,
        }
        if query:
            base_params["q"] = query.lower()
        apply_filter_params(category, base_params, query, mc_version, mod_name)

        # Fetch page 1 first to discover how many total pages exist
        page1_items, payload1, url1 = _fetch_page_with_colors(
            client, category, endpoint, base_params, 1
        )
        api_pages = max(1, (payload1.get("pagination") or {}).get("pages", 1))
        all_candidates = list(page1_items)

        # If more pages exist, sample additional evenly-spaced pages across A-Z in parallel
        extra_pages = [p for p in _pick_sample_pages(api_pages) if p != 1]
        if extra_pages:
            with ThreadPoolExecutor(max_workers=len(extra_pages)) as pool:
                futures = [
                    pool.submit(_fetch_page_with_colors, client, category, endpoint, base_params, p)
                    for p in extra_pages
                ]
                for fut in futures:
                    try:
                        more_items, _, _ = fut.result()
                        all_candidates.extend(more_items)
                    except Exception:
                        pass

        # For Blocks with filters, also include matching hits from global /colors/search
        if category == "Blocks":
            try:
                cs_resp = client.get(
                    f"{BASE_API_URL}/colors/search",
                    params={"hex": color_hex.lstrip("#"), "limit": COLOR_SEARCH_API_LIMIT},
                    timeout=15,
                )
                if cs_resp.ok:
                    cs_blocks = filter_color_search_blocks(
                        cs_resp.json().get("data", []),
                        mc_version=mc_version,
                        mod_name=mod_name,
                    )
                    q_low = query.lower()
                    for blk in cs_blocks:
                        if not q_low or q_low in (blk.get("display_name") or "").lower() or q_low in (blk.get("full_id") or "").lower():
                            all_candidates.append(blk)
            except Exception:
                pass

        # Deduplicate by full_id before filtering by dominant color
        seen_ids = set()
        unique_candidates = []
        for it in all_candidates:
            fid = it.get("full_id") or id(it)
            if fid not in seen_ids:
                seen_ids.add(fid)
                unique_candidates.append(it)

        matched = filter_by_dominant_color(unique_candidates, color_hex)
        cached_url = f"{url1}&dominant_color={color_hex}"

        if len(_color_search_cache) >= 12:
            _color_search_cache.clear()
        _color_search_cache[cache_key] = (matched, cached_url)

    total = len(matched)
    total_pages = max(1, math.ceil(total / limit))
    safe_page = min(max(1, page), total_pages)
    start = (safe_page - 1) * limit
    return {
        "data": matched[start:start + limit],
        "pagination": {
            "page": safe_page,
            "limit": limit,
            "pages": total_pages,
            "total": total,
        },
        "url": cached_url,
    }


def apply_local_filters(category, items, mc_version="", color_hex=None):
    """
    Apply client-side filters that the API endpoints don't support directly:
    - Filter Mods by Minecraft Version
    - Filter Items/Blocks by dominant color if color_hex is given
    """
    if category == "Mods" and mc_version:
        items = [it for it in items if mc_version in (it.get("mc_versions") or [])]

    if category in ("Items", "Blocks") and color_hex:
        items = filter_by_dominant_color(items, color_hex)

    return items
# =============================================================================
# END OF ADDED FILTER CODE FOR GUI
# =============================================================================

# =============================================================================
# ADDED __NAME__ CHECK FOR GUI: Only run the terminal loop when this file is run directly,
# so importing blocksitems_API in blocksitems_GUI.py does not block on input().
# =============================================================================
if __name__ == "__main__":
# =============================================================================
# END OF CODE ADDED FOR GUI
# =============================================================================
    while True:
        while userinputcat not in categories:
            userinputcat = input("What are you looking for?\nItems, Blocks, Mods, Modpacks, All\n")

        if userinputcat != "All":

            userinput = input(f"What {userinputcat.strip("s")} are you looking for?\n")
            url = "https://blocksitems.com/api/2026.1.3/" + userinputcat.lower() + "?q=" + userinput.lower()
            data = requests.get(url)
            data = data.json()
            showfounddata()


        else:
            userinput = input(f"What are you looking for?\n")

            for cat in categories:
                if cat != "All":
                    url = "https://blocksitems.com/api/2026.1.3/" + cat.lower() + "?q=" + userinput.lower() + "&scope=all"
                    print(f"{cat}:\n")
                    data = requests.get(url)
                    data = data.json()
                    showfounddata()
        
        userinputend = "No"

        while userinputend != "Yes":
            
            if userinputcat != "All":
                userinputpage = input(userinputcat + " per page: " + str(data["pagination"]["limit"]) + "\nCurrent Page: " + str(data["pagination"]["page"]) + "\nPages: " + str(data["pagination"]["pages"]) + "\nGo to Page: ")
            else:
                userinputpage = input(cat + " per page: " + str(data["pagination"]["limit"]) + "\nCurrent Page: " + str(data["pagination"]["page"]) + "\nPages: " + str(data["pagination"]["pages"]) + "\nGo to Page: ")
            
            if userinputpage.isdigit():

                if int(userinputpage) <= data["pagination"]["pages"]:

                    if "&page=" in url: 
                        url = url.replace("&page=" + str(data["pagination"]["page"]), "&page=" + str(userinputpage))
                    
                    else:
                        url = url + "&page=" + str(userinputpage)
                    data = requests.get(url)
                    data = data.json()
                    showfounddata()

                else:
                    print("Invalid page number, Type a number between 1 and " + str(data["pagination"]["pages"]))
                    userinputend = input("Do you want to search for something else?\nYes No\n")
                    
            if userinputpage.isdigit() == False:
                userinputend = input("Do you want to search for something else?\nYes No\n")
            if userinputend == "Yes":
                userinputcat = ""