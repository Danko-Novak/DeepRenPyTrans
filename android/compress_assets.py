import os
import sys
import subprocess
import json
from concurrent.futures import ProcessPoolExecutor, as_completed

# Ensure Pillow is installed
try:
    from PIL import Image
except ImportError:
    print("Pillow library not found. Installing now...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image

def compress_image(file_path, max_width=1280, quality=60):
    try:
        with Image.open(file_path) as img:
            orig_w, orig_h = img.size
            
            # Calculate new size if image is wider than max_width
            if orig_w > max_width:
                ratio = max_width / float(orig_w)
                new_h = int(float(orig_h) * ratio)
                img = img.resize((max_width, new_h), Image.Resampling.LANCZOS)
                resized = True
            else:
                resized = False

            # Determine format
            ext = os.path.splitext(file_path)[1].lower()

            if ext in ['.jpg', '.jpeg']:
                img.save(file_path, 'JPEG', quality=quality, optimize=True)
                return True, resized, file_path
            elif ext == '.png':
                img.save(file_path, 'PNG', optimize=True)
                return True, resized, file_path
    except Exception as e:
        print(f"Error compressing {file_path}: {e}")
        return False, False, file_path
    return False, False, file_path

def main():
    base_dir = os.environ.get("TARGET_DIR", "./apk_work/game")
    target_dir = os.path.join(base_dir, "images")
    restored_json = os.environ.get("RESTORED_JSON", "./apk_work/restored_assets.json")
    
    if not os.path.exists(target_dir):
        print(f"Target directory {target_dir} not found. Please run build_apk.sh first!")
        return

    # Load list of restored assets to avoid double-compression
    restored_assets = set()
    if os.path.exists(restored_json):
        try:
            with open(restored_json, 'r', encoding='utf-8') as f:
                restored_assets = set(path.lower() for path in json.load(f))
            print(f"Loaded {len(restored_assets)} restored assets from JSON. These will be skipped.")
        except Exception as e:
            print(f"Error loading restored assets list: {e}")

    print("====================================================")
    print("  Starting PARALLEL Image Compression Pipeline")
    print("====================================================")
    
    # Folders to skip (GUI must remain intact to avoid UI glitches)
    skip_folders = ["gui", "05_gui"]
    
    tasks = []
    
    for root, dirs, files in os.walk(target_dir):
        # Check if we should skip this folder
        should_skip = False
        for skip in skip_folders:
            if skip in root.split(os.sep):
                should_skip = True
                break
        if should_skip:
            continue

        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png']:
                file_path = os.path.join(root, file)
                
                # Check if it was restored from old APK
                rel_path = os.path.relpath(file_path, base_dir).replace('\\', '/').lower()
                if rel_path in restored_assets:
                    continue
                
                # Check file size (only compress if larger than 50KB to save time)
                if os.path.getsize(file_path) > 50 * 1024:
                    tasks.append(file_path)

    total_tasks = len(tasks)
    print(f"Found {total_tasks} images to compress. Spawning workers...")
    
    compressed_count = 0
    resized_count = 0
    
    # Determine thread/process count (utilize maximum cores)
    max_workers = os.cpu_count() or 4
    print(f"Using {max_workers} parallel workers.")
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(compress_image, path): path for path in tasks}
        
        for future in as_completed(futures):
            success, resized, path = future.result()
            if success:
                compressed_count += 1
                if resized:
                    resized_count += 1
                if compressed_count % 50 == 0 or compressed_count == total_tasks:
                    print(f"  Processed {compressed_count}/{total_tasks} images...")

    print("====================================================")
    print(f"  PARALLEL COMPRESSION COMPLETE!")
    print(f"  Total images optimized: {compressed_count}")
    print(f"  Images resized to 1280px: {resized_count}")
    print(f"  Restored assets skipped: {len(restored_assets)}")
    print("====================================================")

if __name__ == "__main__":
    main()
