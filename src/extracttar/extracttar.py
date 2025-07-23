import subprocess
from pathlib import Path
import os
import platform
import shutil

SEVEN_ZIP_PATH = shutil.which("7z")
#SEVEN_ZIP_PATH = r"C:\Program Files\7-Zip\7z.exe"

if SEVEN_ZIP_PATH is None:
    print("Warning: '7z' is not found in your system PATH. Please install 7-Zip or add it to your PATH. ...Attempting Windows 7z executable path (this may not work on all systems).")
    SEVEN_ZIP_PATH = r"C:\Program Files\7-Zip\7z.exe"
else:
    SEVEN_ZIP_PATH = r"7z"
    #SEVEN_ZIP_PATH = shutil.which("7z")


def extract_tar_files(base_path='.'):
    """
    Recursively extracts all .tar files under the given base_path using 7-Zip.
    """
    for tar_file in Path(base_path).rglob('*.tar'):
        output_dir = tar_file.parent
        subprocess.run([
            SEVEN_ZIP_PATH,
            'x',                    # Extract command
            f'-o{output_dir}',      # Output to same directory
            '-sccUTF-8',            # Force UTF-8 encoding
            '-aos',                 # Skip overwriting existing files
            str(tar_file)
        ], check=True)

def extract_gz_files(base_path='.'):
    """
    Recursively extracts all .gz files under the given base_path using 7-Zip.
    """
    for gz_file in Path(base_path).rglob('*.gz'):
        output_dir = gz_file.parent
        subprocess.run([
            SEVEN_ZIP_PATH,
            'x',                    # Extract command
            f'-o{output_dir}',      # Output to same directory
            '-sccUTF-8',            # Force UTF-8 encoding
            '-aos',                 # Skip overwriting existing files
            str(gz_file)
        ], check=True)

def main():
    extract_tar_files()
    extract_gz_files()

if __name__ == '__main__':
    main()
