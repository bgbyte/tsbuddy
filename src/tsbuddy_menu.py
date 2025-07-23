import sys

from src.tsbuddy import main as tsbuddy_main
from src.extracttar.extracttar import main as extracttar_main
from src.aosdl.aosdl import main as aosdl_main, lookup_ga_build, aosup

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
        {"Run AOS Upgrader": aosup},
        {"Run GA Build Lookup": lookup_ga_build},
        {"Run AOS Downloader": aosdl_main},
        {"Run tech_support_complete.tar Extractor": extracttar_main},
        {"Run tech_support.log to CSV Converter": tsbuddy_main},
    ]
    while True:
        #print("\n       (•‿•)  Hey there, buddy!")
        print(ale_ascii)
        try:
            print("\n   ( ^_^)ノ  Hey there, tsbuddy is at your service!")
        except:
            print("\n   ( ^_^)/  Hey there, tsbuddy is at your service!")
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
                print(f"\n   ( ^_^)/🕭   \n")
            # Get the function from the selected option
            selected_func = list(menu_options[int(choice)-1].values())[0]
            selected_func()
        elif choice == '0':
            print("Exiting...\n\n  (x_x) \n")
            sys.exit(0)
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    menu()