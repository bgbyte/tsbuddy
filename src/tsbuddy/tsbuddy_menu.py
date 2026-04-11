print("\nLoading tsbuddy menu...First run will take extra time.\n")
import os
import sys
import time

# Checks if we're in the private repo environment and sets a global variable accordingly
from tsbuddy import IS_PRIVATE
                                                                
def check_private():
    if IS_PRIVATE:
        print("🤫 Running ALE Employee only version, do not share.\n")
    else:
        print("Running Public TSBuddy version.\n")

check_private()

from .utils.tsbuddy_version import main as check_version
# Ensure the tsbuddy_version check runs first
check_version()

# from .utils.tsbuddy_version import update_package_safe as update_package
# from .utils.tsbuddy_version import choice_form as upgrade_downgrade_choice
# from .tslog2csv.tslog2csv import main as tsbuddy_main
# #from .extract.extracttar import main as extracttar_main
# from .extracttar.extract_ts_tar import main as extract_all_main
# from .aos.aosdl import main as aosdl_main, lookup_ga_build, aosup
# from .log_analyzer.logparser_v2 import main as logparser_main
# from .log_analyzer.get_techsupport import main as get_techsupport_main
# from .hmon.graph_cpu import main as graph_hmon_main
# #from .clean_pycache import clean_pycache_and_pyc

print("\n" * 15)  # Clear screen by printing new lines

# def update_tsbuddy():
#     update_package("tsbuddy")

def print_help():
    help_text = """
\nHelp: Menu Option Details

1. Lookup GA Build & Upgrade (aosga):
   - Looks up the latest GA build for your switch and provides options for upgrading.
   - If you want a custom build, choose the AOS Upgrader (aosup) option to upgrade to a specific build.
   - If you only want to download an AOS image to /flash for later processing, use the AOS Downloader (aosdl) option.

2. Run tech support gatherer (ts-get):
   - Generates & gathers tech_support_complete.tar from your device, automating the collection process.

3. Run tech_support_complete.tar Extractor (ts-extract):
   - Extracts the contents of a tech_support_complete.tar archive, making logs and files accessible for analysis.
   - Use the legacy ts-extract-legacy command if you encounter issues with the new extractor.
   - The legacy extractor requires 7zip to be installed on your system and does not extract hmon data.

4. Run tech_support.log to CSV Converter (ts-csv):
   - Converts tech_support.log files into a CSV file for easier viewing and analysis.

5. Run Log Analyzer (logbuddy):
   - Creates DB of switch log & console log files
   - Interactive menu for filtering 
   - Option to output the results to Excel (.xlsx)

6. Run AOS Upgrader (aosup):
   - Upgrades your OmniSwitch to the requested AOS build #, automating the upgrade process.

7. Run AOS Downloader (aosdl):
   - Downloads the requested AOS version to /flash for later processing.

8. Run HMON Graph Generator (ts-graph-cpu):
   - Generates graphs from HMON data using the new script graph_hmon.py. Must be in the same directory as HMON data files.

9. Change current directory:
   - Allows you to view and change the current working directory. Lists available directories and files, and lets you navigate to a new directory for file operations.

10. Employees Only - Upgrade to private version or Replace Token:
   - Prompts ALE employees to enter their auth token provided by Brian. This token is used to check for private tsbuddy updates and perform upgrades if available.

11. Upgrade or Downgrade public tsbuddy Version:
   - Allows you to upgrade to the latest public version of tsbuddy or downgrade to a previous version if you encounter issues. This will remove the private version if you have it, so only use this if you want to switch back to the public version.

12. Print Help (help):
   - Shows this help text describing each menu option in detail.

🤫 Secrets and ⚙️ Settings:
- The ~/.tsbuddy_secrets file is used to store sensitive information like API keys.
- The ~/.tsbuddy_settings file is used to store user preferences and settings.

\n
"""
    print(help_text)
    time.sleep(1)  # Pause to allow user to read

def update_package():
    from .utils.tsbuddy_version import update_package_safe
    update_package_safe("tsbuddy")

def upgrade_downgrade_choice():
    from .utils.tsbuddy_version import choice_form
    print("\n########\nThis feature is unreliable.\nTo properly upgrade use `pip install tsbuddy --upgrade`\nIf you want to revert to a previous public version, you can run `pip install tsbuddy==<version>` with the desired version number.\n ########\n")
    choice_form()

def ale_auth_and_upgrade():
    from .utils.ale_auth import main
    print("\n###########\n\nThis option is for ALE employees only. It will prompt you to enter your ALE token provided by Brian, which will then be used to check for private tsbuddy updates and perform upgrades if available.\n\nIMPORTANT:\nIf the upgrade doesn't work, you can try running `pip uninstall tsbuddy -y`,\n then `pip cache purge`,\n then `pip install tsbuddy`,\n then try this menu option again.\n\n###########\n")
    main()

def tsbuddy_main():
    from .tslog2csv.tslog2csv import main
    main()

def extract_all_main():
    from .extracttar.extract_ts_tar import main
    main()

def aosdl_main():
    from .aos.aosdl import main
    main()

def lookup_ga_build():
    from .aos.aosdl import lookup_ga_build
    print("\n###########\n\nWithout your own repo, this script is just a memory aid for: Model/AOS image name, latest AOS/latest GA #, old AOS/prev GA build #, Model/Family, Model Variants.\n\nThis option will look up the latest GA build for your switch and provide options for upgrading (requires your own AOS image repo). If you want a custom build, choose the AOS Upgrader (aosup) option to upgrade to a specific build. If you only want to download an AOS image to /flash for later processing, use the AOS Downloader (aosdl) option.\n\n###########\n")
    lookup_ga_build()

def aosup():
    from .aos.aosdl import aosup
    aosup()

def logparser_main():
    import importlib
    from .log_analyzer import logparser_v2 as logbuddy
    importlib.reload(logbuddy)
    logbuddy.main()

def get_techsupport_main():
    from .log_analyzer.get_techsupport import main
    main()

def graph_hmon_main():
    from .hmon.graph_cpu import main
    main()

def list_directory_contents(path="."):
    """List directories and files in the given path. Returns (dirs, files)."""
    dirs = []
    files = []
    for item in os.listdir(path):
        if os.path.isdir(os.path.join(path, item)):
            dirs.append(item)
        elif os.path.isfile(os.path.join(path, item)):
            files.append(item)
    print("Directories:")
    for i in dirs:
        print(f"- {i}/")
    print("Files:")
    for i in files:
        print(f"- {i}")
    return dirs, files

def change_directory():
    # Print current directory
    print(f"Current directory: {os.getcwd()}\n")
    list_directory_contents()
    # Prompt user for new directory
    print("\nEnter the path to the new directory (or press Enter to keep current):")
    print("You can also use relative paths like '../' to go up a directory.")
    new_dir = input("Enter the path to the new directory: ").strip()
    if os.path.isdir(new_dir):
        os.chdir(new_dir)
        print(f"Directory changed to: {os.getcwd()}")
        list_directory_contents()
    else:
        print("Current directory remains unchanged: ", os.getcwd())

def menu():
    menu_options = [
        {" Get GA Build, Family, or Upgrade (aosga)": lookup_ga_build},
        {" Run tech support gatherer (ts-get)": get_techsupport_main},
        {" Run tech_support_complete.tar Extractor (ts-extract) (ts-extract-legacy)": extract_all_main},
        {" Run tech_support.log to CSV Converter (ts-csv)": tsbuddy_main},
        {" Run Log Analyzer -DEPRECATED- (logbuddy)": logparser_main},
        {" Run AOS Upgrader (aosup)": aosup},
        {" Run AOS Downloader (aosdl)": aosdl_main},
        {" Run CPU Graph (ts-graph-cpu)": graph_hmon_main},
        {" Change current directory or list contents (cd)": change_directory},
        # {"Clear pycache and .pyc files (ts-clean)": clean_pycache_and_pyc},
        {("✅ Employees Only - Upgrade or Replace Token" if IS_PRIVATE else "🚪 Employees Only - Upgrade to private tsbuddy version"): ale_auth_and_upgrade},
        {"Upgrade or downgrade public tsbuddy version": upgrade_downgrade_choice},
        {"Show help info": print_help},
    ]
    #print("\n       (•‿•)  Hey there, buddy!")
    #print(ale_ascii)
    try:
        if IS_PRIVATE:
            print("\n   ( ^_^)ノ  Hey there, tsbuddy is at your service!\n" \
            # "\n 🤫 Running ALE Employee only version, do not share."
            )
        else:
            print("\n   ( ^_^)ノ  Hey there, tsbuddy is at your service!")
    except:
        print("\n   ( ^_^)/  Hey there, tsbuddy is at your service!")
    print("\n Skip this menu by running the CLI commands directly (provided in parentheses below), e.g. `ts-get`.\n")
    while True:
        try:
            print("\n=== 🛎️  ===")
        except:
            print("\n=== Menu ===")
        for idx, opt in enumerate(menu_options, 1):
            print(f"{idx}. {list(opt.keys())[0]}")
        try:
            print("\n0. Exit  (つ﹏<) \n")
        except:
            print("\n0. Exit  (T_T) \n")
        choice = input("Select an option: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(menu_options):
            try:
                #print(f"\n   ( ^_^)ノ⌒☆   \n")
                print(f"\n   ( ^_^)ノ🛎️   \n")
            except:
                #print(f"\n   ( ^_^)/🕭   \n")
                pass
            # Get the function from the selected option
            selected_func = list(menu_options[int(choice)-1].values())[0]
            try:
                selected_func()
            except Exception as e:
                print(f"\nError: {e}\nReturning to menu...\n")
        elif choice.lower() == 'cd' or choice.lower() == 'ls':
            change_directory()
        elif choice == '0':
            print("Exiting...\n\n  (x_x) \n")
            sys.exit(0)
        else:
            print("\nInvalid choice. Please try again.")

if __name__ == "__main__":
    menu()