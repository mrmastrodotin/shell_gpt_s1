
import zipfile
import os

# Zip current directory content, excluding git and junk
# The result will be sgpt_deploy.zip in the current directory

EXCLUDES = {'.git', '.bgpt', '.vscode', '.idea', '__pycache__', 'node_modules', 'sgpt_deploy.zip'}

def zip_project():
    cwd = os.getcwd()
    # We want the folder name to be the root in the zip
    base_name = os.path.basename(cwd)
    output_filename = "sgpt_deploy.zip"
    
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(cwd):
            # Prune dirs in place
            dirs[:] = [d for d in dirs if d not in EXCLUDES and not d.startswith('.')]
            
            for file in files:
                if file in EXCLUDES or file.endswith('.pyc') or file == output_filename:
                    continue
                    
                abs_path = os.path.join(root, file)
                # Rel path from PARENT of cwd, so it includes the folder name
                # e.g. shell_gpt_s1/setup.py
                rel_path = os.path.relpath(abs_path, os.path.dirname(cwd))
                zipf.write(abs_path, rel_path)
    
    print(f"Created {output_filename}")

if __name__ == "__main__":
    zip_project()
