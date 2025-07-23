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
        "Run tsbuddy",
        "Run extracttar",
        "Run aosdl",
        "Run aosdl-ga (GA Build Lookup)",
        "Run aosdl-up (AOS Upgrade)",
        #"Exit"
    ]
    functions = [
        tsbuddy_main,
        extracttar_main,
        aosdl_main,
        lookup_ga_build,
        aosup,
        lambda: (print("Exiting."), sys.exit(0))
    ]
    while True:
        #print("\n       (•‿•)  Hey there, buddy!")
        print(ale_ascii)
        print("\n   ( ^_^)ノ  Hey there, tsbuddy is at your service!")
        print("\n=== 🛎️  ===")
        for idx, option in enumerate(options, 1):
            print(f"{idx}. {option}")
        print("\n0. Exit  (つ﹏<) \n")
        choice = input("Select an option: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(functions):
            #print(f"\n   ( ^_^)ノ⌒☆   \n")
            print(f"\n   ( ^_^)ノ🛎️   \n")
            functions[int(choice) - 1]()
        elif choice == '0':
            print("Exiting...\n\n  (×_×) \n")
            sys.exit(0)
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    menu()