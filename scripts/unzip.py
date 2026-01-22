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

def _validate_targets(members, output_dir):
    seen = set()
    output_root = os.path.abspath(output_dir)
    for member in members:
        normalized = os.path.normpath(member)
        if os.path.isabs(normalized):
            return f"Invalid zip entry path: {member}"
        drive, _ = os.path.splitdrive(normalized)
        if drive:
            return f"Invalid zip entry path: {member}"
        if normalized == '..' or normalized.startswith(f"..{os.sep}"):
            return f"Invalid zip entry path: {member}"

        key = normalized.lower() if os.name == 'nt' else normalized
        if key in seen:
            return f"Duplicate zip entry path: {member}"
        seen.add(key)

        output_path = os.path.abspath(os.path.join(output_dir, normalized))
        if not output_path.startswith(output_root + os.sep) and output_path != output_root:
            return f"Invalid zip entry path: {member}"

        if os.path.exists(output_path):
            return f"Refusing to overwrite existing path: {output_path}"

    return None

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

        validation_error = _validate_targets(members, output_dir)
        if validation_error:
            print(f"ERROR:{validation_error}")
            return 0

        max_workers = _get_concurrency()
        if max_workers <= 1 or file_count == 1:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(output_dir)
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
            if zf is None:
                with zipfile.ZipFile(zip_path, 'r') as fallback_zip:
                    fallback_zip.extract(member_name, output_dir)
                return
            zf.extract(member_name, output_dir)

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
