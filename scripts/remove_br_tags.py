import argparse
import json
import os
import re
import sys


BR_RE = re.compile(r"<br\s*/?>", re.IGNORECASE)


def _read_text(path):
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        return handle.read()


def _write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def collect_dita_files(xslt_root):
    for root, _, names in os.walk(xslt_root):
        for name in names:
            if name.lower().endswith(".dita"):
                yield os.path.join(root, name)


def update_dita_file(path, dry_run):
    text = _read_text(path)
    matches = list(BR_RE.finditer(text))
    if not matches:
        return {"removed": 0, "changed": False}

    updated_text = BR_RE.sub(" ", text)
    changed = updated_text != text
    if changed and not dry_run:
        _write_text(path, updated_text)

    return {"removed": len(matches), "changed": changed}


def main():
    parser = argparse.ArgumentParser(
        description="Remove <br/> tags from .dita files under xslt_output."
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

    dita_files = list(collect_dita_files(xslt_root))
    if not dita_files:
        print("ERROR:No DITA files found under XSLT root.")
        return 2

    files_changed = 0
    br_tags_removed = 0

    for path in dita_files:
        result = update_dita_file(path, args.dry_run)
        br_tags_removed += result["removed"]
        if result["changed"]:
            files_changed += 1

    stats = {
        "xslt_root": xslt_root,
        "dita_files": len(dita_files),
        "files_changed": files_changed,
        "br_tags_removed": br_tags_removed,
        "dry_run": args.dry_run,
    }

    print(f"RESULT:{json.dumps(stats)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
