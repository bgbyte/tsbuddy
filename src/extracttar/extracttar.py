import subprocess
from pathlib import Path

SEVEN_ZIP_PATH = r"C:\Program Files\7-Zip\7z.exe"

def extract_tar_files(base_path='.'):
    """
    Recursively extracts all .tar files under the given base_path using 7-Zip.
    """
    for tar_file in Path(base_path).rglob('*.tar'):
        output_dir = tar_file.parent
        subprocess.run([
            SEVEN_ZIP_PATH,
            'x',
            f'-o{output_dir}',
            '-sccUTF-8',
            '-aos',
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
            'x',
            f'-o{output_dir}',
            '-sccUTF-8',
            '-aos',
            str(gz_file)
        ], check=True)

def main():
    extract_tar_files()
    extract_gz_files()

if __name__ == '__main__':
    main()
