import argparse
import concurrent.futures
import fnmatch
import os
import re
import csv
import shutil
import sys
import tempfile
import uuid
from html import entities as html_entities
from html import unescape as html_unescape
from multiprocessing import freeze_support, get_context
from pathlib import Path
from xml.etree import ElementTree

XSLT_FILES = {
    "first": "Entity_Store.xsl",
    "second": "Entity_Parser.xsl",
    "third": "XMLtoDITA_Build.xsl",
    "fourth": "Build_Structure.xsl",
    "final": "Build_Validation.xsl",
}

DEFAULT_PATTERNS = ("xml", "*.xml")
DTD_PLACEHOLDER = "<!-- placeholder DTD to satisfy the XML parser -->\n"
MAP_FILENAME = "content.ditamap"
REPORT_FILENAME = "invalid_richtext_report.csv"
_AMP_ENTITY_RE = re.compile(
    br"&(?!(?:#\d+;|#x[0-9A-Fa-f]+;|[A-Za-z][A-Za-z0-9._-]*;))"
)
_EMPTY_P_BEFORE_P_RE = re.compile(r'(<p\b[^>]*>)(\s*)(?=<p\b)', re.IGNORECASE)
_EMPTY_P_BEFORE_CLOSE_RE = re.compile(
    r'(<p\b[^>]*>)(\s*)(?=</(?:div|content|section|body)\b)',
    re.IGNORECASE
)
_EMPTY_P_SELF_CLOSE_RE = re.compile(
    r"<p\b[^>]*/>\s*</p>",
    re.IGNORECASE
)
_UNCLOSED_P_BEFORE_CLOSE_RE = re.compile(
    r"(<p\b[^>]*>)(?:(?!</p>).)*?(</(?:div|content|section|body)\b[^>]*>)",
    re.IGNORECASE | re.DOTALL
)
_HTML_ENTITY_RE = re.compile(r"&([A-Za-z][A-Za-z0-9]+);")
_XML_ENTITY_NAMES = {"lt", "gt", "amp", "quot", "apos"}
_HTML_TAG_RE = re.compile(r"<(/?)([A-Za-z][A-Za-z0-9:_-]*)([^>]*)>")
_HTML_ATTR_RE = re.compile(
    r"\s+[A-Za-z_:][A-Za-z0-9:._-]*\s*=\s*\"[^\"]*\""
)
_HTML_ATTR_SQ_RE = re.compile(
    r"\s+[A-Za-z_:][A-Za-z0-9:._-]*\s*=\s*'[^']*'"
)
_VOID_HTML_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}
_CONTENT_BLOCK_RE = re.compile(
    r"(<content\b[^>]*>)(.*?)(</content>)",
    re.IGNORECASE | re.DOTALL,
)
_STRAY_FIELD_CLOSE_RE = re.compile(
    r"</field>\s*</content>\s*</field>(?=\s*(?:<field\b|</fields\b))",
    re.IGNORECASE,
)

_EXEC = {}


def _as_dir_uri(path):
    uri = Path(path).resolve().as_uri()
    if not uri.endswith("/"):
        uri += "/"
    return uri


def _format_error(exc):
    try:
        return f"{exc.__class__.__name__}: {exc}"
    except Exception:
        return repr(exc)


def _ensure_concept_dtd(dir_path):
    dtd_path = Path(dir_path, "concept.dtd")
    if dtd_path.exists():
        return dtd_path
    dtd_path.write_text(DTD_PLACEHOLDER, encoding="ascii")
    return dtd_path


def _ensure_map_dtd(dir_path):
    dtd_path = Path(dir_path, "map.dtd")
    if dtd_path.exists():
        return dtd_path
    dtd_path.write_text(DTD_PLACEHOLDER, encoding="ascii")
    return dtd_path


def _sanitize_xml_entities(file_path):
    data = Path(file_path).read_bytes()
    if b"&" not in data:
        return False
    fixed = _AMP_ENTITY_RE.sub(b"&amp;", data)
    if fixed == data:
        return False
    Path(file_path).write_bytes(fixed)
    return True


def _sanitize_xml_text(file_path):
    text = Path(file_path).read_text(encoding="utf-8", errors="replace")
    if not text:
        return False

    out = []
    in_tag = False

    for idx, ch in enumerate(text):
        if ch == "<":
            if in_tag:
                out.append(ch)
                continue
            nxt = text[idx + 1] if idx + 1 < len(text) else ""
            if nxt and (nxt.isalpha() or nxt in ("/", "?", "!")):
                in_tag = True
                out.append(ch)
            else:
                out.append("&lt;")
            continue

        if in_tag and ch == ">":
            in_tag = False
            out.append(ch)
            continue

        if in_tag and ch == "\"":
            prev = text[idx - 1] if idx > 0 else ""
            nxt = text[idx + 1] if idx + 1 < len(text) else ""
            if prev != "=" and nxt not in (" ", "\t", "\r", "\n", ">", "/", "?"):
                out.append("&quot;")
            else:
                out.append(ch)
            continue

        out.append(ch)

    fixed = "".join(out)
    if fixed == text:
        return False
    Path(file_path).write_text(fixed, encoding="utf-8")
    return True


def _fix_empty_paragraphs(file_path):
    text = Path(file_path).read_text(encoding="utf-8", errors="replace")
    if "<p" not in text:
        return False
    fixed = _EMPTY_P_BEFORE_P_RE.sub(r"\1</p>\2", text)
    fixed = _EMPTY_P_BEFORE_CLOSE_RE.sub(r"\1</p>\2", fixed)
    fixed = _EMPTY_P_SELF_CLOSE_RE.sub("<p></p>", fixed)
    if fixed == text:
        return False
    Path(file_path).write_text(fixed, encoding="utf-8")
    return True


def _close_unterminated_paragraphs(file_path):
    text = Path(file_path).read_text(encoding="utf-8", errors="replace")
    if "<p" not in text:
        return False

    def _close(match):
        open_tag = match.group(1)
        close_tag = match.group(2)
        middle = match.group(0)[len(open_tag): -len(close_tag)]
        return f"{open_tag}{middle}</p>{close_tag}"

    fixed = _UNCLOSED_P_BEFORE_CLOSE_RE.sub(_close, text)
    if fixed == text:
        return False
    Path(file_path).write_text(fixed, encoding="utf-8")
    return True


def _normalize_html_entities(file_path):
    text = Path(file_path).read_text(encoding="utf-8", errors="replace")
    if "&" not in text:
        return False

    def _replace(match):
        name = match.group(1)
        if name in _XML_ENTITY_NAMES:
            return match.group(0)
        codepoint = html_entities.name2codepoint.get(name)
        if codepoint:
            return f"&#{codepoint};"
        html5_value = html_entities.html5.get(f"{name};")
        if html5_value:
            return "".join(f"&#{ord(ch)};" for ch in html5_value)
        return f"&amp;{name};"

    fixed = _HTML_ENTITY_RE.sub(_replace, text)
    if fixed == text:
        return False
    Path(file_path).write_text(fixed, encoding="utf-8")
    return True


def _find_html_entity_issues(text):
    issues = []
    bad_names = set()
    for match in _HTML_ENTITY_RE.finditer(text):
        name = match.group(1)
        if name in _XML_ENTITY_NAMES:
            continue
        if name in html_entities.name2codepoint:
            bad_names.add(name)
            continue
        if f"{name};" in html_entities.html5:
            bad_names.add(name)
            continue
    if bad_names:
        issues.append(f"xml_unsafe_entity:{', '.join(sorted(bad_names))}")
    if re.search(r"&(?!(?:#\d+;|#x[0-9A-Fa-f]+;|[A-Za-z][A-Za-z0-9]+;))", text):
        issues.append("bare_ampersand")
    return issues


def _find_html_structure_issues(text):
    issues = []

    if re.search(r"<p\s*/\s*>", text, re.IGNORECASE):
        issues.append("empty_p_tag")

    if re.search(r"<p\b[^>]*>(?:(?!</p>).)*<p\b", text, re.IGNORECASE | re.DOTALL):
        issues.append("nested_p_tag")

    stack = []
    mismatched = set()
    for match in _HTML_TAG_RE.finditer(text):
        closing, tag, attrs = match.groups()
        tag_lower = tag.lower()
        if tag_lower.startswith("!") or tag_lower.startswith("?"):
            continue
        attrs_text = attrs or ""
        self_closing = attrs_text.strip().endswith("/") or tag_lower in _VOID_HTML_TAGS
        if closing:
            if not stack:
                mismatched.add(tag_lower)
                continue
            last = stack.pop()
            if last != tag_lower:
                mismatched.add(tag_lower)
        elif not self_closing:
            stack.append(tag_lower)

        tag_text = match.group(0)
        cleaned = _HTML_ATTR_RE.sub("", tag_text)
        cleaned = _HTML_ATTR_SQ_RE.sub("", cleaned)
        if "\"" in cleaned or "'" in cleaned:
            issues.append("bad_attribute_quotes")

    if mismatched:
        issues.append(f"mismatched_closing:{', '.join(sorted(mismatched))}")
    if stack:
        unclosed = ", ".join(sorted(set(stack))[:10])
        issues.append(f"unclosed_tags:{unclosed}")

    return issues


def _summarize_text(text, limit=220):
    snippet = " ".join(text.split())
    if len(snippet) > limit:
        return snippet[:limit] + "..."
    return snippet


def _balance_html_fragment(fragment):
    stack = []
    for match in _HTML_TAG_RE.finditer(fragment):
        closing, tag, attrs = match.groups()
        tag_lower = tag.lower()
        if tag_lower.startswith("!") or tag_lower.startswith("?"):
            continue
        attrs_text = attrs or ""
        self_closing = attrs_text.strip().endswith("/") or tag_lower in _VOID_HTML_TAGS
        if closing:
            if not stack:
                continue
            if stack[-1] == tag_lower:
                stack.pop()
                continue
            if tag_lower in stack:
                while stack and stack[-1] != tag_lower:
                    stack.pop()
                if stack and stack[-1] == tag_lower:
                    stack.pop()
        elif not self_closing:
            stack.append(tag_lower)

    if not stack:
        return fragment
    closers = "".join(f"</{tag}>" for tag in reversed(stack))
    return fragment + closers


def _remove_orphan_closing_tags(fragment):
    closing_tags = set(m.group(1).lower() for m in re.finditer(r"</\s*([A-Za-z][A-Za-z0-9:_-]*)\s*>", fragment))
    if not closing_tags:
        return fragment
    fixed = fragment
    for tag in closing_tags:
        if re.search(rf"<\s*{re.escape(tag)}(\s|>|/)", fragment, re.IGNORECASE):
            continue
        fixed = re.sub(rf"</\s*{re.escape(tag)}\s*>", "", fixed, flags=re.IGNORECASE)
    return fixed


def _balance_content_blocks(file_path):
    text = Path(file_path).read_text(encoding="utf-8", errors="replace")
    if "<content" not in text:
        return False

    def _replace(match):
        start, inner, end = match.groups()
        fixed_inner = _remove_orphan_closing_tags(inner)
        fixed_inner = _balance_html_fragment(fixed_inner)
        return f"{start}{fixed_inner}{end}"

    fixed = _CONTENT_BLOCK_RE.sub(_replace, text)
    if fixed == text:
        return False
    Path(file_path).write_text(fixed, encoding="utf-8")
    return True


def _fix_stray_field_closers(file_path):
    text = Path(file_path).read_text(encoding="utf-8", errors="replace")
    if "</content>" not in text:
        return False
    fixed = _STRAY_FIELD_CLOSE_RE.sub("</field>", text)
    if fixed == text:
        return False
    Path(file_path).write_text(fixed, encoding="utf-8")
    return True


def _collect_rich_text_issues(source_path):
    issues = []
    try:
        tree = ElementTree.parse(source_path)
    except Exception as exc:
        return [
            {
                "source_file": str(source_path),
                "item_id": "",
                "item_name": "",
                "field_key": "",
                "issues": f"xml_parse_error:{exc}",
                "snippet": "",
            }
        ]

    root = tree.getroot()
    for item in root.iter("item"):
        item_id = item.get("id", "")
        item_name = item.get("name", "")
        for field in item.findall(".//field"):
            if field.get("type") != "Rich Text":
                continue
            field_key = field.get("key", "")
            content = field.findtext("content", default="")
            if not content:
                continue
            html_text = html_unescape(content)
            issue_list = []
            issue_list.extend(_find_html_entity_issues(html_text))
            issue_list.extend(_find_html_structure_issues(html_text))
            if issue_list:
                issues.append(
                    {
                        "source_file": str(source_path),
                        "item_id": item_id,
                        "item_name": item_name,
                        "field_key": field_key,
                        "issues": "; ".join(dict.fromkeys(issue_list)),
                        "snippet": _summarize_text(html_text),
                    }
                )
    return issues


def _is_warning_text(message):
    msg = (message or "").lower()
    return "warning at mode" in msg or "xtde0540" in msg


def _is_warning_error(exc):
    message = str(exc)
    return _is_warning_text(message)


def _is_warning_only_message(message):
    if not _is_warning_text(message):
        return False
    msg = message or ""
    if "Error on line" in msg or "SXXP" in msg:
        return False
    return True


def _run_final_on_outputs(output_dir):
    dita_files = sorted(Path(output_dir).glob("*.dita"))
    for dita_path in dita_files:
        try:
            _EXEC["final"].transform_to_file(
                source_file=str(dita_path),
                output_file=str(dita_path),
            )
        except Exception as exc:
            if _is_warning_error(exc):
                continue
            raise
    return len(dita_files)


def _cleanup_before_final(output_dir):
    output_path = Path(output_dir)
    removed = 0
    for path in output_path.glob("*.ditamap"):
        try:
            path.unlink()
            removed += 1
        except OSError:
            pass
    return removed


def _cleanup_after_final(output_dir):
    output_path = Path(output_dir)
    removed = 0
    for pattern in ("*.ditamap", "*.dtd"):
        for path in output_path.glob(pattern):
            try:
                path.unlink()
                removed += 1
            except OSError:
                pass
    return removed


def _write_ditamap(output_dir):
    output_path = Path(output_dir)
    dita_files = [
        path.name
        for path in sorted(output_path.glob("*.dita"))
        if path.name.lower() != "xml.dita"
    ]
    if not dita_files:
        return None

    _ensure_map_dtd(output_path)
    map_path = output_path / MAP_FILENAME
    lines = [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n",
        "<!DOCTYPE map PUBLIC \"-//OASIS//DTD DITA Map//EN\" \"map.dtd\">\n",
        "<map>\n",
        "  <title>content</title>\n"
    ]
    lines.extend([f"  <topicref href=\"{name}\"/>\n" for name in dita_files])
    lines.append("</map>\n")
    map_path.write_text("".join(lines), encoding="utf-8")
    return str(map_path)


def _init_worker(xslt_dir):
    global _EXEC
    try:
        from saxonche import PySaxonProcessor
    except Exception as exc:
        raise RuntimeError(
            "Missing saxonche. Install with: pip install saxonche"
        ) from exc

    proc = PySaxonProcessor(license=False)
    xslt = proc.new_xslt30_processor()

    compiled = {}
    for key, name in XSLT_FILES.items():
        stylesheet_path = str(Path(xslt_dir, name).resolve())
        compiled[key] = xslt.compile_stylesheet(stylesheet_file=stylesheet_path)
    _EXEC = compiled


def _ensure_clean_dir(path, overwrite):
    path = Path(path)
    if path.exists():
        if not overwrite:
            raise RuntimeError(f"Output directory exists: {path}")
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _copy_source_as_xml(source_path, temp_dir):
    target = Path(temp_dir, "xml")
    shutil.copy2(source_path, target)
    return target


def _copy_source_to_output(source_path, output_dir):
    output_path = Path(output_dir, Path(source_path).name)
    shutil.copy2(source_path, output_path)
    return output_path


def _run_pipeline(args):
    (
        source_path,
        output_dir,
        temp_root,
        keep_temp,
        overwrite,
        step_logs,
    ) = args

    temp_dir = Path(temp_root, f"job_{uuid.uuid4().hex}")
    temp_dir.mkdir(parents=True, exist_ok=True)
    _ensure_concept_dtd(temp_dir)

    error = None
    rich_text_issues = _collect_rich_text_issues(source_path)
    output_str = str(output_dir)
    try:
        if step_logs:
            print(f"STEP:{source_path}:first:start")
        _copy_source_as_xml(source_path, temp_dir)

        step_01 = temp_dir / "01.xml"
        step_02 = temp_dir / "02.xml"
        xml_dita = temp_dir / "xml.dita"

        _EXEC["first"].transform_to_file(
            source_file=str(source_path),
            output_file=str(step_01),
        )
        if step_logs:
            print(f"STEP:{source_path}:first:done")
            print(f"STEP:{source_path}:second:start")
        _EXEC["second"].transform_to_file(
            source_file=str(step_01),
            output_file=str(step_02),
        )
        if step_logs:
            print(f"STEP:{source_path}:second:done")
        _sanitize_xml_entities(step_02)
        _normalize_html_entities(step_02)
        _sanitize_xml_text(step_02)
        _fix_empty_paragraphs(step_02)
        _close_unterminated_paragraphs(step_02)
        _balance_content_blocks(step_02)
        _fix_stray_field_closers(step_02)
        if step_logs:
            print(f"STEP:{source_path}:third:start")
        _EXEC["third"].transform_to_file(
            source_file=str(step_02),
            output_file=str(xml_dita),
        )
        if step_logs:
            print(f"STEP:{source_path}:third:done")

        output_dir = _ensure_clean_dir(output_dir, overwrite)
        output_str = str(output_dir)
        _ensure_concept_dtd(output_dir)
        _copy_source_to_output(source_path, output_dir)

        if step_logs:
            print(f"STEP:{source_path}:fourth:start")
        _EXEC["fourth"].set_base_output_uri(_as_dir_uri(output_dir))
        _EXEC["fourth"].transform_to_file(
            source_file=str(xml_dita),
            output_file=str(Path(output_dir, "xml.dita")),
        )
        if step_logs:
            print(f"STEP:{source_path}:fourth:done")
            print(f"STEP:{source_path}:final:start")
        _cleanup_before_final(output_dir)
        final_count = _run_final_on_outputs(output_dir)
        if final_count == 0:
            raise RuntimeError("No .dita outputs found after fourth.xsl")
        if step_logs:
            print(f"STEP:{source_path}:final:done")
        _cleanup_after_final(output_dir)
    except Exception as exc:
        if _is_warning_only_message(str(exc)):
            error = None
        else:
            error = _format_error(exc)
    finally:
        if not keep_temp:
            shutil.rmtree(temp_dir, ignore_errors=True)

    return str(source_path), output_str, error, rich_text_issues


def _matches_patterns(name, patterns):
    return any(fnmatch.fnmatch(name, pattern) for pattern in patterns)


def _collect_inputs(input_path, patterns):
    input_path = Path(input_path)
    if input_path.is_file():
        return [input_path], None

    if not input_path.is_dir():
        raise RuntimeError(f"Input path not found: {input_path}")

    matches = []
    for root, _, files in os.walk(input_path):
        for filename in files:
            if _matches_patterns(filename, patterns):
                matches.append(Path(root, filename))
    return matches, input_path


def _output_dir_for_input(source_path, input_root, output_root, flat_output):
    source_path = Path(source_path)
    output_root = Path(output_root)

    if flat_output:
        return output_root

    if input_root:
        relative = source_path.relative_to(input_root)
        parent = relative.parent
    else:
        parent = Path()

    stem = source_path.stem if source_path.suffix else source_path.name
    return output_root / parent / stem


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Run the XSLT pipeline with Saxon/C (saxonche)."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input XML file or directory containing XML files.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Output root directory.",
    )
    parser.add_argument(
        "--xslt-dir",
        default="XSLT",
        help="Directory containing XSLT files.",
    )
    parser.add_argument(
        "--temp-root",
        default=None,
        help="Temp root directory (defaults to <output-dir>/_tmp).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of worker processes (defaults to CPU count).",
    )
    parser.add_argument(
        "--pattern",
        action="append",
        default=None,
        help="Filename pattern(s) when input is a directory. "
        "Defaults to: xml, *.xml",
    )
    parser.add_argument(
        "--flat-output",
        action="store_true",
        help="Write all outputs into the output root (can collide).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow deleting existing output directories.",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep temp directories for debugging.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first failure.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print errors and summary.",
    )
    parser.add_argument(
        "--step-logs",
        action="store_true",
        help="Print start/finish logs for each XSLT step.",
    )
    return parser.parse_args()


def main():
    try:
        import saxonche  # noqa: F401
    except Exception:
        print("ERROR: saxonche is required. Install with: pip install saxonche")
        return 2

    args = _parse_args()

    patterns = args.pattern or list(DEFAULT_PATTERNS)
    inputs, input_root = _collect_inputs(args.input, patterns)
    if not inputs:
        print("ERROR: No input files matched.")
        return 2

    output_root = Path(args.output_dir)
    output_root = output_root.resolve()
    temp_root = Path(args.temp_root).resolve() if args.temp_root else output_root / "_tmp"
    temp_root.mkdir(parents=True, exist_ok=True)

    workers = args.workers or (os.cpu_count() or 4)
    workers = max(1, min(workers, len(inputs)))

    jobs = []
    for source_path in inputs:
        job_output = _output_dir_for_input(
            source_path, input_root, output_root, args.flat_output
        )
        jobs.append(
            (
                source_path,
                job_output,
                temp_root,
                args.keep_temp,
                args.overwrite,
                args.step_logs,
            )
        )

    ctx = get_context("spawn")
    errors = 0
    all_rich_text_issues = []

    with concurrent.futures.ProcessPoolExecutor(
        max_workers=workers,
        mp_context=ctx,
        initializer=_init_worker,
        initargs=(args.xslt_dir,),
    ) as executor:
        future_map = {executor.submit(_run_pipeline, job): job[0] for job in jobs}
        for future in concurrent.futures.as_completed(future_map):
            source_path = future_map[future]
            try:
                result_source, output_dir, error, rich_text_issues = future.result()
                if rich_text_issues:
                    all_rich_text_issues.extend(rich_text_issues)
                if error:
                    errors += 1
                    print(f"ERROR:{result_source}: {error}")
                    if args.fail_fast:
                        for pending in future_map:
                            pending.cancel()
                        break
                else:
                    if not args.quiet:
                        print(f"OK:{result_source} -> {output_dir}")
            except Exception as exc:
                errors += 1
                print(f"ERROR:{source_path}: {exc}")
                if args.fail_fast:
                    for pending in future_map:
                        pending.cancel()
                    break

    if all_rich_text_issues:
        report_path = output_root / REPORT_FILENAME
        with report_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                ["source_file", "item_id", "item_name", "field_key", "issues", "snippet"]
            )
            for entry in all_rich_text_issues:
                writer.writerow(
                    [
                        entry["source_file"],
                        entry["item_id"],
                        entry["item_name"],
                        entry["field_key"],
                        entry["issues"],
                        entry["snippet"],
                    ]
                )
        if not args.quiet:
            print(f"REPORT:{report_path}")

    if errors:
        print(f"FAILED:{errors}")
        return 1
    print(f"DONE:{len(inputs)}")
    return 0


if __name__ == "__main__":
    freeze_support()
    sys.exit(main())
