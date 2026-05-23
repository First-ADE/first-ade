import os
import re
import sys
import urllib.parse

LINK_REGEX = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')

def check_file_links(file_path):
    errors = []
    base_dir = os.path.dirname(file_path)
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        links = LINK_REGEX.findall(content)
        for _text, target in links:
            parsed = urllib.parse.urlparse(target)
            path = parsed.path
            
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            if not path:
                continue
                
            if path.startswith("file:///"):
                local_path = path.replace("file:///", "")
                if os.name == 'nt' and local_path.startswith('/'):
                    local_path = local_path[1:]
            else:
                if path.startswith("/"):
                    repo_root = find_repo_root(file_path)
                    local_path = os.path.join(repo_root, path.lstrip("/"))
                else:
                    local_path = os.path.join(base_dir, path)
            
            local_path = os.path.normpath(local_path)
            
            if not os.path.exists(local_path):
                errors.append((target, local_path))
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        
    return errors

def find_repo_root(start_path):
    current = os.path.abspath(start_path)
    while True:
        if os.path.exists(os.path.join(current, ".git")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return os.getcwd()
        current = parent

def scan_docs(directories):
    total_errors = 0
    repo_root = os.getcwd()
    
    for directory in directories:
        dir_path = os.path.join(repo_root, directory)
        if not os.path.exists(dir_path):
            continue
            
        print(f"Scanning directory: {directory}")
        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.endswith(".md"):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, repo_root)
                    errors = check_file_links(full_path)
                    if errors:
                        print(f"✗ File '{rel_path}' contains broken links:")
                        for target, resolved in errors:
                            print(f"  - Target:   '{target}'")
                            print(f"    Resolved: '{resolved}'")
                        total_errors += len(errors)
                    
    if total_errors > 0:
        print(f"\nFailed: Found {total_errors} broken local links in documentation.")
        sys.exit(1)
    else:
        print("\n✓ All local markdown links verified successfully!")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("dirs", nargs="*", default=["docs", "specs"], help="Directories to scan")
    args = parser.parse_args()
    scan_docs(args.dirs)
