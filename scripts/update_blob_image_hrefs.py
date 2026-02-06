import argparse
import json
import os
import re
import sys


IMAGE_HREF_RE = re.compile(
    r'(?P<prefix><image\b[^>]*?\bhref=")(?P<href>[^"]*)(?P<suffix>")',
    re.IGNORECASE | re.DOTALL,
)


def _read_text(path):
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        return handle.read()


def _write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def update_dita_file(path, blob_root, href_prefix, dry_run):
    text = _read_text(path)
    updates = 0
    unchanged = 0
    missing = 0
    missing_files = set()

    def replacer(match):
        nonlocal updates, unchanged, missing
        href = match.group("href").strip()
        if not href:
            return match.group(0)
        if "/" in href or "\\" in href:
            unchanged += 1
            return match.group(0)

        candidate = os.path.join(blob_root, href)
        if not os.path.isfile(candidate):
            missing += 1
            missing_files.add(href)
            return match.group(0)

        if href_prefix:
            prefix = href_prefix.rstrip("/")
        else:
            prefix = os.path.relpath(blob_root, start=os.path.dirname(path)).replace("\\", "/")
        new_href = f"{prefix}/{href}"
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
        "missing_files": missing_files,
        "changed": updated_text != text,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Replace DITA image hrefs with relative paths to blob files."
    )
    parser.add_argument(
        "--xslt-root",
        required=True,
        help="Root path to xslt_output.",
    )
    parser.add_argument(
        "--blob-root",
        required=True,
        help="Path to blob/master folder to validate image files.",
    )
    parser.add_argument(
        "--prefix",
        default="",
        help="Href prefix to add for blob images (omit to compute relative path).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report changes without writing.",
    )

    args = parser.parse_args()
    xslt_root = os.path.abspath(args.xslt_root)
    blob_root = os.path.abspath(args.blob_root)

    if not os.path.isdir(xslt_root):
        print(f"ERROR:XSLT root not found: {xslt_root}")
        return 2
    if not os.path.isdir(blob_root):
        print(f"ERROR:Blob root not found: {blob_root}")
        return 2

    total_files = 0
    files_changed = 0
    images_updated = 0
    images_unchanged = 0
    images_missing = 0
    missing_files = set()

    for root, _, files in os.walk(xslt_root):
        for name in files:
            if not name.lower().endswith(".dita"):
                continue
            path = os.path.join(root, name)
            total_files += 1
            result = update_dita_file(path, blob_root, args.prefix, args.dry_run)
            images_updated += result["updated"]
            images_unchanged += result["unchanged"]
            images_missing += result["missing"]
            missing_files |= result["missing_files"]
            if result["changed"]:
                files_changed += 1

    stats = {
        "xslt_root": xslt_root,
        "blob_root": blob_root,
        "dita_files": total_files,
        "files_changed": files_changed,
        "images_updated": images_updated,
        "images_unchanged": images_unchanged,
        "images_missing_blob": images_missing,
        "dry_run": args.dry_run,
        "missing_files": sorted(list(missing_files))[:25],
    }

    print(f"RESULT:{json.dumps(stats)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
