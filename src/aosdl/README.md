# OmniSwitch AOS Downloader (aosdl)

## Overview
The `aosdl.py` script automates the process of connecting to multiple devices via SSH, identifying their platform family, and downloading the appropriate AOS images to the devices' /flash/ directory.

## Features
- Connects to devices using SSH.
- Identifies platform family based on shell prompt.
- Downloads AOS images based on platform family.
- Supports multiple devices with customizable credentials.
- Also offers a GA build number lookup tool: aosdl-ga

## Requirements
- Python 3.x
- `paramiko` library
- An AOS image repository

## Installation
1. Ensure Python 3.x is installed on your system.
2. Install the `paramiko` library using pip:
   ```bash
   pip install paramiko
   ```

## Usage
1. Run the script:
   ```powershell
   (venv) admin:~/$ aosdl
   ```
2. Follow the prompts to enter AOS version information and device details.
3. The script will connect to each device, identify its platform family, and download the appropriate images.

```powershell
(venv) admin:~/$ aosdl
Enter device IP: 192.168.1.1
Enter username for 192.168.1.1 [admin]: admin
Enter password for 192.168.1.1 [switch]:
Connecting to 192.168.1.1...
[192.168.1.1] Platform family: shasta
[192.168.1.1] Downloading Uos.img...
[192.168.1.1] Downloaded Uos.img to /flash/
```

## Configuration
### Image Mapping
The script uses a predefined mapping of platform families to image files. You can modify the `image_map` dictionary in the script to add or update mappings.

### Constants
- `ga_index.json`: This is an index associating OmniSwitch family to GA build number for each AOS release.

## AOSDL-GA CLI Command

`aosdl-ga` is a CLI command designed to look up GA builds for specific AOS versions and platform families. It uses the `ga_index.json` file to provide accurate build information. The file needs to be updated as GA builds are released.

### Usage

Run the `aosdl-ga` command directly from your terminal:

```powershell
(venv) admin:~/$ aosdl-ga
```

This will prompt you to enter the AOS version and platform family. The script will then look up the GA build information and display it.

### Example

```powershell
(venv) admin:~/$ aosdl-ga
Enter the switch family name to lookup the GA build (e.g., shasta) [exit]: yukon
Provide the AOS version & Release for the lookup (e.g., 8.10R02) [exit]: 8.10R02
GA Build: .105
```

The `aosdl-ga` command simplifies the process of finding GA builds for specific AOS versions and platform families.

