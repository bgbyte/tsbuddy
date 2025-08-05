import sys

from src.tsbuddy import main as tsbuddy_main
from src.extracttar.extracttar import main as extracttar_main
from src.aosdl.aosdl import main as aosdl_main, lookup_ga_build, aosup
from src.logparser import main as logparser_main

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

def menu():
    menu_options = [
        {"Run AOS Upgrader (aosup)": aosup},
        {"Run GA Build Lookup (aosga)": lookup_ga_build},
        {"Run AOS Downloader (aosdl)": aosdl_main},
        {"Run tech_support_complete.tar Extractor (ts-extract)": extracttar_main},
        {"Run swlog parser (to CSV & JSON) (ts-log)": logparser_main},
        {"Run tech_support.log to CSV Converter (ts-csv)": tsbuddy_main},
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