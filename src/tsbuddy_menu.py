import sys

from src.tsbuddy import main as tsbuddy_main
from src.extracttar.extracttar import main as extracttar_main
from src.aosdl.aosdl import main as aosdl_main, lookup_ga_build, aosup

def menu():
    while True:
        print("\n=== tsbuddy Menu ===")
        print("1. Run tsbuddy")
        print("2. Run extracttar")
        print("3. Run aosdl")
        print("4. Run aosdl-ga (GA Build Lookup)")
        print("5. Run aosdl-up (AOS Upgrade)")
        print("6. Exit")
        choice = input("Select an option: ").strip()
        if choice == '1':
            tsbuddy_main()
        elif choice == '2':
            extracttar_main()
        elif choice == '3':
            aosdl_main()
        elif choice == '4':
            lookup_ga_build()
        elif choice == '5':
            aosup()
        elif choice == '6':
            print("Exiting.")
            sys.exit(0)
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    menu() 