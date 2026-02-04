import argparse
import json
import os
import re
import sys


XREF_HREF_RE = re.compile(
    r'(?P<prefix><xref\b[^>]*?\bhref=")(?P<href>[^"]*)(?P<suffix>")',
    re.IGNORECASE | re.DOTALL,
)
XREF_TARGET_RE = re.compile(r'^#(X_[0-9A-F]{32})$', re.IGNORECASE)
ID_RE = re.compile(r'\bid="(X_[0-9A-F]{32})"', re.IGNORECASE)


def _read_text(path):
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        return handle.read()


def _write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def _lang_from_dita_path(path):
    lower_parts = [part.lower() for part in path.split(os.sep)]
    if "en_xml" in lower_parts:
        return "en"
    if "fr_xml" in lower_parts:
        return "fr"
    return None


def collect_dita_files(xslt_root):
    files = []
    missing_lang = 0
    for root, _, names in os.walk(xslt_root):
        for name in names:
            if not name.lower().endswith(".dita"):
                continue
            path = os.path.join(root, name)
            lang = _lang_from_dita_path(path)
            if not lang:
                missing_lang += 1
                continue
            files.append((path, lang))
    return files, missing_lang


def build_id_index(files):
    id_map = {}
    duplicate_keys = set()

    for path, lang in files:
        text = _read_text(path)
        for id_value in ID_RE.findall(text):
            key = (lang, id_value.upper())
            if key in id_map and id_map[key] != path:
                duplicate_keys.add(key)
                continue
            id_map.setdefault(key, path)

    return id_map, duplicate_keys


def update_dita_file(path, lang, id_map, duplicate_keys, dry_run):
    text = _read_text(path)
    updates = 0
    unchanged = 0
    missing = 0
    ambiguous = 0
    missing_ids = set()
    ambiguous_ids = set()

    def replacer(match):
        nonlocal updates, unchanged, missing, ambiguous
        href = match.group("href")
        target_match = XREF_TARGET_RE.match(href.strip())
        if not target_match:
            return match.group(0)

        target_id = target_match.group(1)
        lookup_id = target_id.upper()
        key = (lang, lookup_id)
        if key in duplicate_keys:
            ambiguous += 1
            ambiguous_ids.add(lookup_id)
            return match.group(0)

        target_path = id_map.get(key)
        if not target_path:
            missing += 1
            missing_ids.add(lookup_id)
            return match.group(0)

        if os.path.normcase(os.path.abspath(target_path)) == os.path.normcase(os.path.abspath(path)):
            unchanged += 1
            return match.group(0)

        rel_path = os.path.relpath(target_path, start=os.path.dirname(path))
        rel_path = rel_path.replace("\\", "/")
        new_href = f"{rel_path}#{target_id}"
        if href == new_href:
            unchanged += 1
            return match.group(0)

        updates += 1
        return f"{match.group('prefix')}{new_href}{match.group('suffix')}"

    updated_text = XREF_HREF_RE.sub(replacer, text)
    if updated_text != text and not dry_run:
        _write_text(path, updated_text)

    return {
        "updated": updates,
        "unchanged": unchanged,
        "missing": missing,
        "ambiguous": ambiguous,
        "missing_ids": missing_ids,
        "ambiguous_ids": ambiguous_ids,
        "changed": updated_text != text,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Replace DITA xref href fragments with relative paths to target topics."
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
    xslt_root = os.path.abspath(args.xslt_root)

    if not os.path.isdir(xslt_root):
        print(f"ERROR:XSLT root not found: {xslt_root}")
        return 2

    files, missing_lang = collect_dita_files(xslt_root)
    if not files:
        print("ERROR:No DITA files found under XSLT root.")
        return 2

    id_map, duplicate_keys = build_id_index(files)
    if not id_map:
        print("ERROR:No X_ IDs found under XSLT root.")
        return 2

    files_changed = 0
    xrefs_updated = 0
    xrefs_unchanged = 0
    xrefs_missing = 0
    xrefs_ambiguous = 0
    missing_ids = set()
    ambiguous_ids = set()

    for path, lang in files:
        result = update_dita_file(path, lang, id_map, duplicate_keys, args.dry_run)
        xrefs_updated += result["updated"]
        xrefs_unchanged += result["unchanged"]
        xrefs_missing += result["missing"]
        xrefs_ambiguous += result["ambiguous"]
        missing_ids |= result["missing_ids"]
        ambiguous_ids |= result["ambiguous_ids"]
        if result["changed"]:
            files_changed += 1

    stats = {
        "xslt_root": xslt_root,
        "dita_files": len(files),
        "files_changed": files_changed,
        "xrefs_updated": xrefs_updated,
        "xrefs_unchanged": xrefs_unchanged,
        "xrefs_missing_target": xrefs_missing,
        "xrefs_ambiguous_target": xrefs_ambiguous,
        "duplicate_ids": len(duplicate_keys),
        "missing_lang_files": missing_lang,
        "dry_run": args.dry_run,
        "missing_target_ids": sorted(list(missing_ids))[:25],
        "ambiguous_target_ids": sorted(list(ambiguous_ids))[:25],
    }

    print(f"RESULT:{json.dumps(stats)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
