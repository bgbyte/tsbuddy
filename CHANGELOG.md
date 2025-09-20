# Changelog

## 2025-09-18 [0.0.26]
- Added tcpdump file converter to Wireshark compatible file. Thank you @NathanielOrlina
- Fixed pandas import error (added to dependencies)
- Fixed tkinter import error on Linux
- Added more dependencies

## 2025-08-26 [0.0.25]
- tsbuddy can now be updated from...tsbuddy 🔄
- Auto-check for latest version during menu startup, update, or skip version
- New workflow for "Get GA Build, Family, & Upgrade (aosga)"

## 2025-08-18
- Added change directory function in `tsbuddy_menu` for improved usability.
- Introduced a new extractor script to accommodate `hmon` files.
- Moved the old extractor to `ts-extract-legacy` for legacy support.

## 2025-08-08
- Added change directory feature.
- Fixed crash when extracting corrupted files; now errors are ignored.

## 2025-08-06
- Added get tech support feature.

## 2025-08-04
- Introduced interactive menu for easier navigation of `tsbuddy` features.
- Added interactive menu and CLI tool documentation to README.
- Linked CLI commands and menu options to their respective modules.
- Added this changelog section and linked it in the Table of Contents.
- Created CLI commands for common tasks: `aosup`, `aosga`, `ts-extract`, `ts-log`.

## 2025-05-30
- Initial release and documentation for tsbuddy core features and parsers.
- Added aosdl CLI documentation and usage examples.
- Added initial parsing functions for temperature and system information.
- Created CLI commands for common tasks: `aosdl`, `ts-csv`.
- Added extensibility for future parser and feature additions.
