import argparse
import json
import os
import re
import sys


IMAGE_HREF_RE = re.compile(
    r'(?P<prefix><image\b[^>]*?\bhref=")(?P<href>[^"]*)(?P<suffix>")',
    re.IGNORECASE | re.DOTALL,
)
GUID_RE = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE,
)
FORCED_EXTENSION = "jpeg"


def _read_text(path):
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        return handle.read()


def _write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def _lang_from_item_path(path):
    parts = path.split(os.sep)
    if len(parts) < 3:
        return None
    lang = parts[-3].lower()
    if lang in ("en", "fr") and parts[-2].isdigit() and parts[-1].lower() == "xml":
        return lang
    return None


def _lang_from_dita_path(path):
    lower_parts = [part.lower() for part in path.split(os.sep)]
    if "en_xml" in lower_parts:
        return "en"
    if "fr_xml" in lower_parts:
        return "fr"
    return None


def _extract_item_details(text):
    id_match = re.search(r'\bid="\{([^}]+)\}"', text, re.IGNORECASE)
    blob_match = re.search(
        r'key="blob"[^>]*>\s*<content>([^<]+)</content>',
        text,
        re.IGNORECASE,
    )
    if not id_match or not blob_match:
        return None
    ext_match = re.search(
        r'key="extension"[^>]*>\s*<content>([^<]+)</content>',
        text,
        re.IGNORECASE,
    )
    return {
        "id": id_match.group(1).upper(),
        "blob": blob_match.group(1).strip(),
        "extension": ext_match.group(1).strip() if ext_match else "",
    }


def _extension_from_href(href):
    if "." not in href:
        return ""
    return href.rsplit(".", 1)[-1]


def _guid_from_href(href):
    if not href:
        return None
    value = href.strip()
    if value.startswith("{") and value.endswith("}"):
        value = value[1:-1].strip()
    if GUID_RE.match(value):
        return value.upper()
    return None


def build_blob_index(images_root):
    blob_map = {}
    ext_map = {}
    scanned = 0
    matched = 0

    for root, _, files in os.walk(images_root):
        for name in files:
            if name.lower() != "xml":
                continue
            scanned += 1
            path = os.path.join(root, name)
            lang = _lang_from_item_path(path)
            if not lang:
                continue
            text = _read_text(path)
            details = _extract_item_details(text)
            if not details or not details["blob"]:
                continue
            key = (details["id"], lang)
            blob_map[key] = details["blob"]
            if details["extension"]:
                ext_map[key] = details["extension"]
            matched += 1

    return blob_map, ext_map, scanned, matched


def update_dita_file(path, lang, blob_map, ext_map, dry_run):
    text = _read_text(path)
    updates = 0
    unchanged = 0
    missing = 0
    missing_ids = set()

    def replacer(match):
        nonlocal updates, unchanged, missing
        href = match.group("href").strip()
        guid = _guid_from_href(href)
        if not guid:
            return match.group(0)
        key = (guid, lang)
        blob = blob_map.get(key)
        if not blob:
            missing += 1
            missing_ids.add(guid)
            return match.group(0)

        new_href = f"{blob}.{FORCED_EXTENSION}"
        if href == new_href:
            unchanged += 1
            return match.group(0)

        updates += 1
        return f"{match.group('prefix')}{new_href}{match.group('suffix')}"

    updated_text = IMAGE_HREF_RE.sub(replacer, text)
    if updated_text != text and not dry_run:
        _write_text(path, updated_text)

    return {
        "updated": updates,
        "unchanged": unchanged,
        "missing": missing,
        "missing_ids": missing_ids,
        "changed": updated_text != text,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Replace DITA image hrefs with blob ids from Sitecore export."
    )
    parser.add_argument(
        "--images-root",
        required=True,
        help="Root path to Sitecore image export (Cancer information).",
    )
    parser.add_argument(
        "--xslt-root",
        required=True,
        help="Root path to xslt_output.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report changes without writing.",
    )

    args = parser.parse_args()
    images_root = os.path.abspath(args.images_root)
    xslt_root = os.path.abspath(args.xslt_root)

    if not os.path.isdir(images_root):
        print(f"ERROR:Images root not found: {images_root}")
        return 2
    if not os.path.isdir(xslt_root):
        print(f"ERROR:XSLT root not found: {xslt_root}")
        return 2

    blob_map, ext_map, scanned, matched = build_blob_index(images_root)
    if not blob_map:
        print("ERROR:No blob entries found under images root.")
        return 2

    total_files = 0
    files_changed = 0
    images_updated = 0
    images_unchanged = 0
    images_missing = 0
    missing_lang = 0
    missing_ids = set()

    for root, _, files in os.walk(xslt_root):
        for name in files:
            if not name.lower().endswith(".dita"):
                continue
            path = os.path.join(root, name)
            lang = _lang_from_dita_path(path)
            if not lang:
                missing_lang += 1
                continue
            total_files += 1
            result = update_dita_file(path, lang, blob_map, ext_map, args.dry_run)
            images_updated += result["updated"]
            images_unchanged += result["unchanged"]
            images_missing += result["missing"]
            missing_ids |= result["missing_ids"]
            if result["changed"]:
                files_changed += 1

    stats = {
        "images_root": images_root,
        "xslt_root": xslt_root,
        "scanned_items": scanned,
        "blob_entries": matched,
        "dita_files": total_files,
        "files_changed": files_changed,
        "images_updated": images_updated,
        "images_unchanged": images_unchanged,
        "images_missing_blob": images_missing,
        "missing_lang_files": missing_lang,
        "dry_run": args.dry_run,
        "missing_blob_ids": sorted(list(missing_ids))[:25],
    }

    print(f"RESULT:{json.dumps(stats)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
