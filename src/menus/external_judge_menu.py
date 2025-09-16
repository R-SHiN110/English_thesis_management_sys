from datetime import datetime, date
from src.utils.file_io import read_json, write_json
from src.utils.helpers import display_menu


DEFENSE_REQUESTS_FILE = "data/requests/defense_requests.json"
DEFENDED_THESES_FILE = "data/theses/defended_theses.json"


def external_judge_menu(user):
    """External Judge Main Menu"""
    while True:
        menu_title = f"Professor Menu - {user.name}"
        options = [
            "Grade defended theses",
            "Change password",
            "Logout"
        ]

        display_menu(menu_title, options)

        choice = input("Please select an option: ").strip()

        if choice == "1":
            grade_theses_as_external(user)
        elif choice == "2":
            change_password(user)
        elif choice == "3":
            print("Logging out...")
            break
        else:
            print("⚠️ Invalid option!")
            input("Press Enter to continue...")


def grade_theses_as_external(user):
    """Grade theses as external judge"""
    print("\n📊 Grading defended theses")
    print("=" * 50)

    defense_requests = read_json(DEFENSE_REQUESTS_FILE)
    today = date.today()

    theses_for_judge = [
        th for th in defense_requests
        if th.get("external_judge_id") == user.user_id and "external_grade" not in th
    ]

    if not theses_for_judge:
        print("📂 No thesis found for grading.")
        input("Press Enter to continue...")
        return

    students = read_json("data/users/students.json")
    students_dict = {s["user_id"]: s for s in students} if students else {}

    print("\n📚 List of theses awaiting grading (External Judge):")
    for idx, thesis in enumerate(theses_for_judge, start=1):
        student_info = students_dict.get(thesis["student_id"], {})
        student_name = student_info.get("name", "Unknown")

        print(f"\n{idx}. 👨‍🎓 Student: {student_name}")
        print(f"   🔢 Student ID: {thesis['student_id']}")
        print(f"   📚 Title: {thesis.get('title', 'Unknown')}")
        print(f"   📅 Defense Date: {thesis.get('defense_date', 'Unknown')}")
        print("-" * 40)

    try:
        choice = int(input("Select thesis number: ").strip())
        if choice < 1 or choice > len(theses_for_judge):
            print("⚠️ Invalid choice!")
            input("Press Enter to continue...")
            return
    except ValueError:
        print("⚠️ Please enter a number.")
        input("Press Enter to continue...")
        return

    thesis = theses_for_judge[choice - 1]

    try:
        grade = float(input("Enter external judge grade (0 to 20): ").strip())
        if grade < 0 or grade > 20:
            print("⚠️ Grade must be between 0 and 20.")
            input("Press Enter to continue...")
            return
    except ValueError:
        print("⚠️ Invalid grade!")
        input("Press Enter to continue...")
        return

    for th in defense_requests:
        if th["student_id"] == thesis["student_id"] and th["title"] == thesis["title"]:
            th["external_grade"] = grade
            th["external_grade_date"] = today.strftime("%Y-%m-%d")
            print("✅ External grade recorded.")

            if "internal_grade" in th and "internal_grade_date" in th:
                internal_grade = th["internal_grade"]
                external_grade = th["external_grade"]
                final_grade = (internal_grade + external_grade) / 2

                if final_grade >= 17:
                    final_letter = "A"
                elif final_grade >= 14:
                    final_letter = "B"
                elif final_grade >= 10:
                    final_letter = "C"
                else:
                    final_letter = "D"

                th["final_grade"] = final_grade
                th["final_letter_grade"] = final_letter
                th["status"] = "Closed"

                courses = read_json("data/courses/thesis_courses.json")
                for course in courses:
                    if course["professor_id"] == th["professor_id"]:
                        course["capacity"] = course.get("capacity", 0) + 1
                        print(f"✅ Course '{course['title']}' capacity increased to {course['capacity']}.")
                        break
                write_json("data/courses/thesis_courses.json", courses)

                print(f"🎯 Final grade: {final_grade:.2f} ({final_letter})")

                defended = read_json(DEFENDED_THESES_FILE)
                defended.append(th.copy())
                write_json(DEFENDED_THESES_FILE, defended)

                print("📂 Thesis added to final list.")

            break

    write_json(DEFENSE_REQUESTS_FILE, defense_requests)

    external_judges = read_json("data/users/external_judges.json")
    for judge in external_judges:
        if judge["user_id"] == user.user_id:
            judge["judge_capacity"] = judge.get("judge_capacity", 0) + 1
            print(f"✅ Your judging capacity increased to {judge['judge_capacity']}.")
            break

    write_json("data/users/external_judges.json", external_judges)

    input("Press Enter to continue...")


def change_password(user):
    """Change password"""
    print("\n🔒 Change Password")
    print("-" * 40)

    old_password = input("Current password: ")
    new_password = input("New password: ")
    confirm_password = input("Confirm new password: ")

    from src.utils.auth import change_password as auth_change_password
    auth_change_password(user, old_password, new_password, confirm_password)

    input("\nPress Enter to go back...")
