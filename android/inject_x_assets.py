import os
import sys
import shutil

def copy_with_x_prefix(src, dest):
    if not os.path.exists(dest):
        os.makedirs(dest)
        
    for item in os.listdir(src):
        # Skip system or hidden files
        if item.startswith('.') or item == '__pycache__':
            continue
            
        src_item = os.path.join(src, item)
        # Prepend "x-" to each folder and file name to match Ren'Py Android layout
        dest_item = os.path.join(dest, "x-" + item)
        
        if os.path.isdir(src_item):
            copy_with_x_prefix(src_item, dest_item)
        else:
            shutil.copy2(src_item, dest_item)

def main():
    if len(sys.argv) < 3:
        print("Usage: python inject_x_assets.py <src_dir> <dest_dir>")
        sys.exit(1)
        
    src_dir = sys.argv[1]
    dest_dir = sys.argv[2]
    
    print(f"Injecting assets with 'x-' prefix from {src_dir} to {dest_dir}...")
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
    os.makedirs(dest_dir)
    
    copy_with_x_prefix(src_dir, dest_dir)
    print("Injection complete successfully.")

if __name__ == "__main__":
    main()
