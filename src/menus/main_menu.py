from src.utils.helpers import display_menu
from src.menus.student_menu import show_student_menu
from src.menus.professor_menu import show_professor_menu
from src.menus.external_judge_menu import external_judge_menu


def show_main_menu():
    """Display main menu and role selection"""
    menu_title = "Main Menu"
    options = [
        "Login as Student",
        "Login as Professor",
        "Login as External Judge",
        "Exit"
    ]

    display_menu(menu_title, options)

    choice = input("Please select an option: ").strip()

    if choice == "1":
        show_login_menu("student")
    elif choice == "2":
        show_login_menu("professor")
    elif choice == "3":
        show_login_menu("external_judge")
    elif choice == "4":
        print("Thank you for using the system. Goodbye!")
        exit()
    else:
        print("⚠️ Invalid option! Please enter a number between 1 and 4.")
        input("Press Enter to continue...")


def show_login_menu(role: str):
    """Display login menu for a specific role"""
    role_name = "Student" if role == "student" else "Professor" if role == "professor" else "External Judge"

    print(f"\nLogin as {role_name}")
    print("-" * 40)

    user_id = input("User ID: ").strip()
    password = input("Password: ").strip()

    from src.utils.auth import verify_user
    user = verify_user(user_id, password, role)

    if user:
        print(f"\n✅ Login successful! Welcome {user.name}")
        input("Press Enter to continue...")

        if role == "student":
            show_student_menu(user)
        elif role == "professor":
            show_professor_menu(user)
        else:
            external_judge_menu(user)
    else:
        print("\n❌ Incorrect User ID or Password!")
        input("Press Enter to go back...")
