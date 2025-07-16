# .TAR & .GZ Extractor (`tsbuddy-extract`)

## Overview
This module provides functionality to recursively extract `.tar` and `.gz` files from the current directory and its subdirectories using 7-Zip. This is commonly used for unpacking log archives for analysis.

## Requirements
- **7-Zip**: Ensure 7-Zip is installed on your system.
  - Default path for 7-Zip is set to `C:\Program Files\7-Zip\7z.exe`. Update the `SEVEN_ZIP_PATH` variable in the script if your installation is located elsewhere.
- **A .tar archive in current directory**: The script will start in the current directory.

## Installation
Install using pip
```bash
pip install tsbuddy
```

## Usage
1. Ensure the `SEVEN_ZIP_PATH` variable in the script points to your 7-Zip executable.
2. Run the script using the following command:

```bash
(venv) admin:~/tech_support_complete$ tsbuddy-extract
```

The script will:
- Recursively search for `.tar` files and extract them.
- Recursively search for `.gz` files and extract them.
- The extracted files & folders will output to the current directory, maintaining the structure.
- Skip overwriting existing files
- Force UTF-8 encoding

## Scripting
If you import this module into your own scripts, you will have the following functions available to you.

### `extract_tar_files(base_path='.')`
- Recursively extracts all `.tar` files under the given `base_path`.
- Uses 7-Zip for extraction.

### `extract_gz_files(base_path='.')`
- Recursively extracts all `.gz` files under the given `base_path`.
- Uses 7-Zip for extraction.

## Notes
- The script uses the `subprocess` module to call 7-Zip.
- The extracted files will be placed in the same directory as the original compressed files.

## License
This script is provided "as-is" without warranty of any kind. Use at your own risk.
