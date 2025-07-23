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
    options = [
        "Run AOS Upgrader",
        "Run GA Build Lookup",
        "Run AOS Downloader",
        "Run tech_support_complete.tar Extractor",
        "Run tech_support.log to CSV Converter",
        #"Exit"
    ]
    functions = [
        aosup,
        lookup_ga_build,
        aosdl_main,
        extracttar_main,
        tsbuddy_main,
        lambda: (print("Exiting."), sys.exit(0))
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
        for idx, option in enumerate(options, 1):
            print(f"{idx}. {option}")
        try:
            print("\n0. Exit  (つ﹏<) \n")
        except:
            print("\n0. Exit  (T_T) \n")
        choice = input("Select an option: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(functions):
            try:
                #print(f"\n   ( ^_^)ノ⌒☆   \n")
                print(f"\n   ( ^_^)ノ🛎️   \n")
            except:
                print(f"\n   ( ^_^)/🕭   \n")
            functions[int(choice) - 1]()
        elif choice == '0':
            print("Exiting...\n\n  (x_x) \n")
            sys.exit(0)
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    menu()