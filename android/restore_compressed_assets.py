import os
import sys
import zipfile
import json

OLD_APK = os.environ.get("OLD_APK", "./spacejourneyx-205_010c-release.apk")
TARGET_DIR = os.environ.get("TARGET_DIR", "./apk_work/game")
RESTORED_JSON = os.environ.get("RESTORED_JSON", "./apk_work/restored_assets.json")

ASSET_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.mp3', '.ogg', '.wav', '.mp4', '.webm', '.ttf', '.otf', '.woff'}

def normalize_old_path(zip_path):
    parts = zip_path.split('/')
    try:
        idx = -1
        for i, part in enumerate(parts):
            clean_part = part[2:] if part.startswith('x-') else part
            if clean_part == 'assets':
                idx = i
                break
        if idx == -1 or idx + 2 >= len(parts):
            return None
        
        next_part = parts[idx+1]
        clean_next = next_part[2:] if next_part.startswith('x-') else next_part
        if clean_next != 'game':
            return None
            
        rel_parts = parts[idx+2:]
        cleaned_rel_parts = []
        for p in rel_parts:
            cleaned_rel_parts.append(p[2:] if p.startswith('x-') else p)
            
        return '/'.join(cleaned_rel_parts)
    except Exception:
        return None

def main():
    if not os.path.exists(TARGET_DIR):
        print(f"Error: Target directory {TARGET_DIR} does not exist.")
        sys.exit(1)
        
    print("====================================================")
    print("  Restoring Compressed Assets from Old APK")
    print("====================================================")
    
    # 1. Map old APK assets
    old_assets = {} # normalized_path_lower -> (original_zip_path, size)
    with zipfile.ZipFile(OLD_APK, 'r') as z:
        for name in z.namelist():
            norm = normalize_old_path(name)
            if norm:
                ext = os.path.splitext(norm)[1].lower()
                if ext in ASSET_EXTENSIONS:
                    old_assets[norm.lower()] = (name, z.getinfo(name).file_size)
                    
    print(f"Indexed {len(old_assets)} assets from old APK.")
    
    # 2. Match and restore
    restored_count = 0
    saved_bytes = 0
    restored_paths = []
    
    with zipfile.ZipFile(OLD_APK, 'r') as z:
        for root, dirs, files in os.walk(TARGET_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, TARGET_DIR)
                rel_path_zip = rel_path.replace('\\', '/')
                rel_path_zip_lower = rel_path_zip.lower()
                
                # Check if it matches an asset in the old APK
                if rel_path_zip_lower in old_assets:
                    old_zip_path, old_size = old_assets[rel_path_zip_lower]
                    new_size = os.path.getsize(file_path)
                    
                    if old_size < new_size:
                        # Restore file!
                        try:
                            # Read old data
                            data = z.read(old_zip_path)
                            # Write to target
                            with open(file_path, 'wb') as f:
                                f.write(data)
                            
                            saved = new_size - old_size
                            saved_bytes += saved
                            restored_count += 1
                            restored_paths.append(rel_path_zip)
                            
                            if restored_count % 100 == 0:
                                print(f"  Restored {restored_count} files...")
                        except Exception as e:
                            print(f"  Error restoring {rel_path_zip}: {e}")
                            
    # 3. Save the restored file list
    with open(RESTORED_JSON, 'w', encoding='utf-8') as f:
        json.dump(restored_paths, f, ensure_ascii=False, indent=2)
        
    print("====================================================")
    print("  RESTORE SUMMARY")
    print(f"  Total files restored: {restored_count}")
    print(f"  Total space saved: {saved_bytes / (1024*1024):.2f} MB")
    print(f"  List of restored assets saved to: {RESTORED_JSON}")
    print("====================================================")

if __name__ == "__main__":
    main()
