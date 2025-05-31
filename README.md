# Tech Support Buddy (`tsbuddy`)

[![PyPI version](https://badge.fury.io/py/tsbuddy.svg)](https://badge.fury.io/py/tsbuddy)
<!-- Add other badges as appropriate: build status, coverage, etc. -->
<!-- e.g., [![Build Status](https://travis-ci.org/YOUR_USERNAME/tsbuddy.svg?branch=main)](https://travis-ci.org/YOUR_USERNAME/tsbuddy) -->

Tech Support Buddy is a versatile Python module built to empower developers and IT professionals in resolving technical issues. It provides a suite of Python functions designed to efficiently diagnose and resolve technical issues by parsing raw text into structured data, enabling automation and data-driven decision-making.

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Installation](#installation)
- [Usage](#usage)
  - [Basic Example: Parsing Temperature Data](#basic-example-parsing-temperature-data)
- [Future Enhancements (Ideas)](#future-enhancements-examples)
- [Contributing](#contributing)

## Overview

Dealing with raw text output can be tedious and time-consuming. `tsbuddy` parsing aims to simplify this by providing tools to:

1.  **Extract** relevant sections from log files or command output.
2.  **Parse** this raw text into structured Python objects.
3.  **Enable** programmatic analysis and decision-making based on the parsed data.

This allows you to quickly turn unstructured command output into actionable insights.

## Key Features

*   **Log Section Extraction:** Easily isolate specific command output or sections from larger support files.
*   **Structured Data Parsing:** Convert unstructured command output into Python objects for easy manipulation. (Simple example below).
*   **Simplified Diagnostics:** Build custom logic on top of parsed data to automate checks, generate reports, trigger alerts or actions.
*   **Developer-Friendly:** Designed to be easily integrated into existing Python scripts and workflows.

## Installation

You can install `tsbuddy` via pip:

```bash
pip install tsbuddy
```

## Usage

tsbuddy can be run directly from your preferred terminal. Doing so will run the main() function where tsbuddy will search for tech_support.log in your working directory & output its contents to a CSV.

```powershell
(venv) admin:~/tech_support_complete$ tsbuddy
✅ CSV exported to parsed_sections_2025-05-30_220933.csv
```

Here's a basic example demonstrating how to use `tsbuddy` within Python to parse temperature information from command output. 

### Basic Example: Parsing Temperature Data

For this example, we will use a file named `tech_support.log` in your working directory.

**1. Import `tsbuddy` and `pprint`:**

```python
import tsbuddy as ts
from pprint import pprint
```

**2. Read your log file:**

(For this example, we'll simulate reading from the file. `tsbuddy` itself can work on any source of text.)

```python
# Example content for 'tech_support.log' stored in the file_text variable
# This would typically be read from the actual file
file_text = """
Some initial lines...
show system, show chassis, etc

show temperature
Chassis/Device   Current Range      Danger Thresh Status
---------------- ------- ---------- ------ ------ ---------------
1/CMMA       47      15 to 60   68     60     UNDER THRESHOLD
3/CMMA       46      15 to 60   68     60     UNDER THRESHOLD
4/CMMA       46      15 to 60   68     60     UNDER THRESHOLD


Some other lines...
show ip interface, etc
...
"""
```
<!-- # If you were reading from a file:
# file = "tech_support.log"
# with open(file, encoding='utf-8') as f:
#     file_text = f.read()
-->

**3. Extract the relevant section:**

The `extract_section` function helps you get the raw text for a specific command or section.

```python
# Extract the section containing "show temperature" output
temp_section_text = ts.extract_section(file_text, "show temperature")

# print("--- Raw Extracted Text ---")
# print(temp_section_text)
## Seen above, without other section output
```

**4. Parse the raw text into a structured format:**

`tsbuddy` provides parsers for specific commands. Here, we use `parse_temperature`.

```python
# Parse the raw temperature text to structured data
parsed_temps = ts.parse_temperature(temp_section_text)

print("--- Parsed Temperature Data ---")
pprint(parsed_temps, sort_dicts=False)
```

This will output:

```
--- Parsed Temperature Data ---
[{'Chassis/Device': '1/CMMA',
  'Current': '47',
  'Range': '15 to 60',
  'Danger': '68',
  'Thresh': '60',
  'Status': 'UNDER THRESHOLD'},
 {'Chassis/Device': '3/CMMA',
  'Current': '46',
  'Range': '15 to 60',
  'Danger': '68',
  'Thresh': '60',
  'Status': 'UNDER THRESHOLD'},
 {'Chassis/Device': '4/CMMA',
  'Current': '46',
  'Range': '15 to 60',
  'Danger': '68',
  'Thresh': '60',
  'Status': 'UNDER THRESHOLD'}]
```

**5. Work with the structured data:**

Now that the data is structured, you can easily access and process specific fields.

```python
# Request data from specific fields
print("\n--- Device Statuses ---")
for chassis in parsed_temps:
    print(chassis["Status"])
```

Output:

```
--- Device Statuses ---
UNDER THRESHOLD
UNDER THRESHOLD
UNDER THRESHOLD
```

**6. Add custom logic:**

You can build more complex logic based on the values of specific fields.

```python
print("\n--- Devices with Current Temperature greater than 46°C ---")
for chassis in parsed_temps:
    if int(chassis["Current"]) > 46:
        print(chassis["Chassis/Device"] + " is greater than 46°C")
```
<!--        pprint(chassis, sort_dicts=False)
-->

Output:

```
--- Devices with Current Temperature greater than 46°C ---
1/CMMA is greater than 46°C
```
<!--
{'Chassis/Device': '1/CMMA',
 'Current': '47',
 'Range': '15 to 60',
 'Danger': '68',
 'Thresh': '60',
 'Status': 'UNDER THRESHOLD'}
-->

## Future Enhancements (Examples)

The `tsbuddy` module is designed to be extensible. Future development could include:

*   More parsers for common log outputs (e.g., `show fabric`, `vrf ... show ...`, `debug show ...`).
*   Functions to compare states (e.g., before/after changes).
*   Integration with alerting systems.
*   Parse configuration.
*   Convert configurations.
*   Auto-detect parsing function.
*   Generate tech-support & validate generation.
*   Support outputting to MS Excel.
*   Support for different log formats & devices.
*   More sophisticated section extraction logic.

## Contributing

Contributions are welcome! If you have ideas for improvements or new features, or if you've found a bug, please feel free to:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/YourFeature` or `bugfix/YourBugfix`).
3.  Make your changes.
4.  Commit your changes (`git commit -m 'Add some feature'`).
5.  Push to the branch (`git push origin feature/YourFeature`).
6.  Open a Pull Request.

Please ensure your code adheres to any existing style guidelines and includes tests where appropriate.
