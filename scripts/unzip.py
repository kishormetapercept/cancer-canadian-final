import zipfile
import sys
import os
import concurrent.futures
import threading
import shutil

def _get_members(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        members = []
        for info in zip_ref.infolist():
            is_dir = info.filename.endswith('/')
            if hasattr(info, 'is_dir'):
                is_dir = info.is_dir()
            if not is_dir:
                members.append(info.filename)
        return members

def _get_concurrency():
    raw = os.getenv('ZIP_EXTRACT_CONCURRENCY')
    if raw is None:
        return 4
    try:
        parsed = int(raw)
    except ValueError:
        return 4
    if parsed < 1:
        return 4
    return min(parsed, 32)

def _transform_directory_name(name):
    transformed = name
    if transformed.startswith('{') and transformed.endswith('}') and len(transformed) > 2:
        transformed = transformed[1:-1]
    transformed = transformed.lower()
    return transformed.replace(' ', '_')

def _normalize_entry_name(entry_name):
    parts = [part for part in _split_path(entry_name) if part]
    if not parts:
        return None

    is_dir = entry_name.endswith('/') or entry_name.endswith('\\')
    last_index = len(parts) - 1
    normalized_parts = []
    for idx, part in enumerate(parts):
        if part in ('.', '..'):
            return None
        if idx == last_index and not is_dir:
            normalized_parts.append(part)
        else:
            normalized_parts.append(_transform_directory_name(part))

    normalized = os.path.normpath(os.path.join(*normalized_parts))
    if os.path.isabs(normalized):
        return None
    drive, _ = os.path.splitdrive(normalized)
    if drive:
        return None
    if normalized == '..' or normalized.startswith(f"..{os.sep}"):
        return None
    return normalized

def _split_path(entry_name):
    return [part for part in entry_name.replace('\\', '/').split('/')]

def _build_output_map(members, output_dir):
    seen = set()
    output_root = os.path.abspath(output_dir)
    output_map = {}
    for member in members:
        normalized = _normalize_entry_name(member)
        if not normalized:
            return f"Invalid zip entry path: {member}", None

        key = normalized.lower() if os.name == 'nt' else normalized
        if key in seen:
            return f"Duplicate zip entry path: {member}", None
        seen.add(key)

        output_path = os.path.abspath(os.path.join(output_dir, normalized))
        if not output_path.startswith(output_root + os.sep) and output_path != output_root:
            return f"Invalid zip entry path: {member}", None

        if os.path.exists(output_path):
            return f"Refusing to overwrite existing path: {output_path}", None
        output_map[member] = output_path

    return None, output_map

def _write_member(zip_ref, member_name, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with zip_ref.open(member_name) as source, open(output_path, 'wb') as target:
        shutil.copyfileobj(source, target)

def _cleanup_language_versions(output_dir):
    targets = {'en', 'fr'}
    removed = 0
    for root, dirnames, _ in os.walk(output_dir):
        base = os.path.basename(root).lower()
        if base in targets:
            numeric_dirs = [d for d in dirnames if d.isdigit()]
            if len(numeric_dirs) > 1:
                numeric_dirs_sorted = sorted(numeric_dirs, key=lambda d: (int(d), d))
                keep = numeric_dirs_sorted[-1]
                for name in numeric_dirs_sorted[:-1]:
                    shutil.rmtree(os.path.join(root, name), ignore_errors=True)
                    removed += 1
                dirnames[:] = [d for d in dirnames if d == keep or not d.isdigit()]
            elif len(numeric_dirs) == 1:
                keep = numeric_dirs[0]
                dirnames[:] = [d for d in dirnames if d == keep or not d.isdigit()]
    return removed

def _promote_language_xml_files(output_dir):
    targets = {'en', 'fr'}
    moved = 0
    for root, _, files in os.walk(output_dir):
        if 'xml' not in files:
            continue
        lang_dir = os.path.basename(os.path.dirname(root))
        if lang_dir.lower() not in targets:
            continue
        if not os.path.basename(root).isdigit():
            continue
        xml_path = os.path.join(root, 'xml')
        dest_dir = os.path.dirname(os.path.dirname(root))
        dest = os.path.join(dest_dir, f"{lang_dir.lower()}_xml")
        os.makedirs(dest_dir, exist_ok=True)
        if os.path.exists(dest):
            os.remove(dest)
        shutil.move(xml_path, dest)
        shutil.rmtree(root, ignore_errors=True)
        moved += 1
    return moved

def extract_zip(zip_path, output_dir):
    try:
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        members = _get_members(zip_path)
        file_count = len(members)
        if file_count == 0:
            print("EXTRACTED:0")
            return 0

        validation_error, output_map = _build_output_map(members, output_dir)
        if validation_error:
            print(f"ERROR:{validation_error}")
            return 0

        max_workers = _get_concurrency()
        if max_workers <= 1 or file_count == 1:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for member in members:
                    _write_member(zip_ref, member, output_map[member])
            _cleanup_language_versions(output_dir)
            _promote_language_xml_files(output_dir)
            print(f"EXTRACTED:{file_count}")
            return file_count

        thread_local = threading.local()
        open_zipfiles = []
        open_zipfiles_lock = threading.Lock()

        def init_thread():
            zf = zipfile.ZipFile(zip_path, 'r')
            thread_local.zipfile = zf
            with open_zipfiles_lock:
                open_zipfiles.append(zf)

        def extract_member(member_name):
            zf = getattr(thread_local, 'zipfile', None)
            output_path = output_map[member_name]
            if zf is None:
                with zipfile.ZipFile(zip_path, 'r') as fallback_zip:
                    _write_member(fallback_zip, member_name, output_path)
                return
            _write_member(zf, member_name, output_path)

        first_error = None
        use_initializer = True
        try:
            executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=max_workers,
                initializer=init_thread
            )
        except TypeError:
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
            use_initializer = False

        try:
            futures = [executor.submit(extract_member, member) for member in members]
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    if first_error is None:
                        first_error = e
        finally:
            executor.shutdown(wait=True)
            if use_initializer:
                for zf in open_zipfiles:
                    try:
                        zf.close()
                    except Exception:
                        pass

        if first_error:
            print(f"ERROR:{first_error}")
            return 0

        _cleanup_language_versions(output_dir)
        _promote_language_xml_files(output_dir)
        print(f"EXTRACTED:{file_count}")
        return file_count
        
    except Exception as e:
        print(f"ERROR:{str(e)}")
        return 0

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("ERROR:Usage: python unzip.py <zip_path> <output_dir>")
        sys.exit(1)
        
    zip_path = sys.argv[1]
    output_dir = sys.argv[2]
    
    if not os.path.exists(zip_path):
        print(f"ERROR:Zip file not found: {zip_path}")
        sys.exit(1)
        
    extract_zip(zip_path, output_dir)
