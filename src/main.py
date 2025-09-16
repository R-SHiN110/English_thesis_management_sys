from src.menus.main_menu import show_main_menu


def main():
    """Main function to run the program"""
    print("=" * 60)
    print("       Thesis Management System - Welcome")
    print("=" * 60)

    while True:
        show_main_menu()


if __name__ == "__main__":
    main()
    input()
