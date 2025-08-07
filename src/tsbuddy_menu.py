import sys
import time

from src.tsbuddy import main as tsbuddy_main
from src.extracttar.extracttar import main as extracttar_main
from src.aosdl.aosdl import main as aosdl_main, lookup_ga_build, aosup
from src.logparser import main as logparser_main
from src.get_techsupport import main as get_techsupport_main
from src.clean_pycache import clean_pycache_and_pyc

ale_ascii = '''
                  ...                   
            .+@@@@@@@@@@@%=             
         .#@@@@@@@@@@@@@@@@@@*.         
       .%@@@@@@@@@@+. :%@@@@@@@#.       
      *@@@@@@@@@@:  ++  @@@@@@@@@+      
     #@@@@@@@@@=  =@@  -@@@@@@@@@@*     
    %@@@@@@@@%. .%@@=  @@@@@@@@@@@@+    
   =@@@@@@@@+  -@@@%. =@@@@%#%@@@@@@:   
   #@@@@@@@.  -%  %#  #@@@@@@#@@@@@@*   
   @@@@@@@.    =@@@  .@@@@@@@@+@@@@@#   
   @@@@@%    -@@@@:  %@@@@@@@*#@@@@@#   
   %@@@%.  .@@@@@@.  @@@@@@@@-@@@@@@*   
   +@@@%- =@@@@@@*  +@@@@@@@@%@@@@@@=   
   .@@@@@@@@@@@@@+  #@@@@@-.@@@@@@@@    
    :@@@@@@@@@@@@+  #@@*: -@@@@@@@%.    
     :@@@@@@@@@@@+      -@@@@@@@@%.     
       +@@@@@@@@@@+..+%@@@@@@@@@=       
        .*@@@@@@@@@@@@@@@@@@@@+         
           .#@@@@@@@@@@@@@@*            
               .-=++++=-.               
'''

def print_help():
    help_text = """
\nHelp: Menu Option Details

1. Get GA Build & Upgrade (aosga):
   - Looks up the latest GA build for your switch and provides options for upgrading.
   - If you want a custom build, choose the AOS Upgrader (aosup) option to upgrade to a specific build.
   - If you only want to download an AOS image to /flash for later processing, use the AOS Downloader (aosdl) option.

2. Run tech support gatherer (ts-get):
   - Generates & gathers tech_support_complete.tar from your device, automating the collection process.

3. Run tech_support_complete.tar Extractor (ts-extract):
   - Extracts the contents of a tech_support_complete.tar archive, making logs and files accessible for analysis.

4. Run tech_support.log to CSV Converter (ts-csv):
   - Converts tech_support.log files into a CSV file for easier viewing and analysis.

5. Run swlog parser (to CSV & JSON) (ts-log):
   - Parses switch log & console log files and outputs the results in both CSV and JSON files.

6. Run AOS Upgrader (aosup):
   - Upgrades your OmniSwitch to the requested AOS build #, automating the upgrade process.

7. Run AOS Downloader (aosdl):
   - Downloads the requested AOS version to /flash for later processing.

8. Print Help (help):
   - Shows this help text describing each menu option in detail.
\n
"""
    print(help_text)
    time.sleep(1)  # Pause to allow user to read

def menu():
    menu_options = [
        {"Get GA Build & Upgrade (aosga)": lookup_ga_build},
        {"Run tech support gatherer (ts-get)": get_techsupport_main},
        {"Run tech_support_complete.tar Extractor (ts-extract)": extracttar_main},
        {"Run tech_support.log to CSV Converter (ts-csv)": tsbuddy_main},
        {"Run swlog parser to CSV & JSON (ts-log)": logparser_main},
        {"Run AOS Upgrader (aosup)": aosup},
        {"Run AOS Downloader (aosdl)": aosdl_main},
        #{"Clear pycache and .pyc files (ts-clean)": clean_pycache_and_pyc},
        {"Show help info": print_help},
    ]
    #print("\n       (•‿•)  Hey there, buddy!")
    #print(ale_ascii)
    try:
        print("\n   ( ^_^)ノ  Hey there, tsbuddy is at your service!")
    except:
        print("\n   ( ^_^)/  Hey there, tsbuddy is at your service!")
    print("\n Skip this menu by running the CLI commands directly (in parentheses below), e.g. `ts-extract`.\n")
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
        elif choice == '0':
            print("Exiting...\n\n  (x_x) \n")
            sys.exit(0)
        else:
            print("\nInvalid choice. Please try again.")

if __name__ == "__main__":
    menu()