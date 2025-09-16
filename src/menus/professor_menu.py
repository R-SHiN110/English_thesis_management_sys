import sys
import os
import subprocess
from src.utils.file_io import read_json, write_json, get_full_path
from src.utils.helpers import display_menu
from datetime import datetime, date


def get_available_internal_judges(exclude_professor_id=None):
    """دریافت لیست اساتید با ظرفیت داوری بجز استاد راهنما"""
    professors = read_json("data/users/professors.json")

    available_judges = [
        p for p in professors
        if p.get("judge_capacity", 0) > 0
           and p["user_id"] != exclude_professor_id
    ]
    return available_judges


def get_available_external_judges():
    """دریافت لیست داوران خارجی با ظرفیت موجود"""
    external_judges = read_json("data/users/external_judges.json")
    available_judges = [j for j in external_judges if j.get("judge_capacity", 0) > 0]
    return available_judges


def decrease_judge_capacity(judge_id, is_external=False):
    """کاهش ظرفیت داوری یک استاد یا داور خارجی"""
    try:
        if is_external:
            file_path = "data/users/external_judges.json"
            judges = read_json(file_path)
        else:
            file_path = "data/users/professors.json"
            judges = read_json(file_path)

        for judge in judges:
            if judge["user_id"] == judge_id and judge.get("judge_capacity", 0) > 0:
                judge["judge_capacity"] -= 1
                break

        write_json(file_path, judges)
        return True
    except Exception as e:
        print(f"❌ Error decreasing judge capacity: {e}")
        return False


def open_file(file_path):
    """باز کردن فایل با برنامه پیشفرض سیستم"""
    try:
        if os.name == 'nt':  # Windows
            os.startfile(file_path)
        elif os.name == 'posix':  # macOS, Linux
            if sys.platform == 'darwin':  # macOS
                subprocess.call(('open', file_path))
            else:  # Linux
                subprocess.call(('xdg-open', file_path))
        print(f"✅ File opened: {file_path}")
    except Exception as e:
        print(f"❌ Error opening file: {e}")


def show_professor_menu(professor):
    """نمایش منوی اصلی استاد"""
    while True:
        menu_title = f"Professor Menu - {professor.name}"
        options = [
            "View and review thesis enrollment requests",
            "Manage defense requests",
            "Grade defended sessions",
            "Search in thesis database",
            "Change password",
            "Logout"
        ]

        display_menu(menu_title, options)

        choice = input("Please select an option: ").strip()

        if choice == "1":
            review_enrollment_requests(professor)
        elif choice == "2":
            manage_defense_requests(professor)
        elif choice == "3":
            grade_defense_sessions(professor)
        elif choice == "4":
            search_theses()
        elif choice == "5":
            change_password(professor)
        elif choice == "6":
            print("Logging out...")
            break
        else:
            print("⚠️Invalid option!")
            input("Press Enter to continue...")


def review_enrollment_requests(professor):
    """بررسی درخواست‌های اخذ پایان‌نامه"""
    print("\n📋 Thesis Enrollment Requests")
    print("-" * 40)

    requests = read_json("data/requests/enrollment_requests.json")
    professor_requests = [r for r in requests if
                          r["professor_id"] == professor.user_id and r["status"] == "در انتظار تأیید استاد"]

    if not professor_requests:
        print("❌ No pending requests.")
        input("Press Enter to go back...")
        return

    # خواندن اطلاعات دانشجویان
    students = read_json("data/users/students.json")
    students_dict = {s["user_id"]: s for s in students} if students else {}

    # خواندن اطلاعات دروس
    courses = read_json("data/courses/thesis_courses.json")
    courses_dict = {c["course_id"]: c for c in courses} if courses else {}

    print(f"\n📝 List of thesis enrollment requests for you:")
    print("=" * 60)

    for i, req in enumerate(professor_requests, 1):
        student_info = students_dict.get(req["student_id"], {})
        student_name = student_info.get("name", "نامشخص")
        student_id = req["student_id"]
        request_date = req.get("created_at", "تاریخ نامشخص")

        print(f"\n{i}. 👨‍🎓 Student: {student_name}")
        print(f"   🔢 Student ID: {student_id}")
        print(f"   📅 Request Date: {request_date}")
        print("-" * 40)

    try:
        choice = int(input("\nSelect a request: ")) - 1
        selected_request = professor_requests[choice]

        # نمایش اطلاعات کامل درخواست
        student_info = students_dict.get(selected_request["student_id"], {})
        student_name = student_info.get("name", "نامشخص")
        course_info = courses_dict.get(selected_request["course_id"], {})
        course_title = course_info.get("title", "نامشخص")

        print(f"\n 🔍 Student {selected_request['student_id']} request for thesis course")
        action = input("Approve (y) or Reject (n)? [y/n]: ").strip().lower()

        if action == 'y':
            selected_request["status"] = "Approved"
            selected_request["approved_date"] = date.today().strftime("%Y-%m-%d")
            print("✅ Request approved.")

        elif action == 'n':
            selected_request["status"] = "Rejected"
            selected_request["rejected_date"] = date.today().strftime("%Y-%m-%d")
            print("❌ Request rejected.")

            for course in courses:
                if course["course_id"] == selected_request["course_id"]:
                    course["capacity"] += 1
                    print(f"✅ Course '{course_title}' capacity increased to {course['capacity']}.")
                    break

        else:
            print("⚠️Invalid action!")
            return

        # آپدیت فایل درخواست‌ها
        for i, req in enumerate(requests):
            if req["student_id"] == selected_request["student_id"]:
                if req["status"] == "در انتظار تأیید استاد":
                    requests[i] = selected_request
                break

        if write_json("data/requests/enrollment_requests.json", requests):
            if action == 'n':  # فقط اگر درخواست رد شده باشد
                if write_json("data/courses/thesis_courses.json", courses):
                    print("✅ Course capacity changes saved.")
                else:
                    print("❌ Error saving course capacity changes!")
        else:
            print("❌ Error saving course capacity changes!")

    except (ValueError, IndexError):
        print("⚠️Invalid action!")

    input("Press Enter to go back...")


def manage_defense_requests(professor):
    """مدیریت درخواست‌های دفاع ارسالی برای استاد"""
    print("\n📅 Defense Requests Management")
    print("=" * 50)

    # خواندن درخواست‌های دفاع
    defense_requests = read_json("data/requests/defense_requests.json")

    # فیلتر کردن درخواست‌های مربوط به این استاد و با وضعیت "در انتظار تأیید استاد"
    professor_defense_requests = [
        r for r in defense_requests
        if r["professor_id"] == professor.user_id
           and r["status"] == "در انتظار تأیید استاد"
    ]

    if not professor_defense_requests:
        print("❌ No defense requests found.")
        input("Press Enter to return...")
        return

    # Read students data
    students = read_json("data/users/students.json")
    students_dict = {s["user_id"]: s for s in students} if students else {}

    print("\n📋 List of pending defense requests:")
    print("=" * 60)

    for i, req in enumerate(professor_defense_requests, 1):
        student_info = students_dict.get(req["student_id"], {})
        student_name = student_info.get("name", "Unknown")

        print(f"\n{i}. 👨‍🎓 Student: {student_name}")
        print(f"   🔢 Student ID: {req['student_id']}")
        print(f"   📚 Thesis Title: {req.get('title', 'Unknown')}")
        print(f"   📅 Submission Date: {req.get('submission_date', 'Unknown')}")
        print("-" * 40)

    try:
        choice = int(input("\n🎯 Select request number to review: ")) - 1

        if choice < 0 or choice >= len(professor_defense_requests):
            print("❌ Invalid request number!")
            input("\nPress Enter to continue...")
            return

        selected_request = professor_defense_requests[choice]

        # Show management menu
        while True:
            print(
                f"\n📋 Manage defense request for student: {students_dict.get(selected_request['student_id'], {}).get('name', 'Unknown')}")
            print("=" * 50)
            print("1. 📄 Open Thesis PDF")
            print("2. 🖼️ Open First Page Image")
            print("3. 🖼️ Open Last Page Image")
            print("4. ❌ Reject Request")
            print("5. ✅ Approve Request & Set Defense Date")
            print("6. ↩️ Back to Previous Menu")

            action = input("\nPlease select an option: ").strip()

            if action == "1":
                # Open PDF
                pdf_path = get_full_path(selected_request["file_path"])
                if os.path.exists(pdf_path):
                    open_file(pdf_path)
                else:
                    print("❌ PDF file not found!")

            elif action == "2":
                # Open first page image
                image_path = get_full_path(selected_request["image_path"][0])
                if os.path.exists(image_path):
                    open_file(image_path)
                else:
                    print("❌ First page image not found!")

            elif action == "3":
                # Open last page image
                image_path = get_full_path(selected_request["image_path"][1])
                if os.path.exists(image_path):
                    open_file(image_path)
                else:
                    print("❌ Last page image not found!")

            elif action == "4":
                # Reject request
                confirm = input("❓ Are you sure you want to reject this request? (y/n): ").strip().lower()
                if confirm == 'y':
                    selected_request["status"] = "Rejected"
                    selected_request["rejected_date"] = date.today().strftime("%Y-%m-%d")

                    # Update requests file
                    for i, req in enumerate(defense_requests):
                        if req["student_id"] == selected_request["student_id"]:
                            defense_requests[i] = selected_request
                            break

                    if write_json("data/requests/defense_requests.json", defense_requests):
                        print("✅ Defense request rejected.")
                    else:
                        print("❌ Error saving changes!")

                    input("\nPress Enter to continue...")
                    break
                else:
                    print("⚠️ Rejection cancelled.")

            elif action == "5":

                # Approve request & set defense date
                print("\n✅ Approve defense request and set details:")
                print("-" * 40)

                # Get defense date
                defense_date = input("Defense Date (YYYY-MM-DD): ").strip()

                # Select internal judge
                print("\n👨‍🏫 Select Internal Judge:")
                print("-" * 30)

                internal_judges = get_available_internal_judges(professor.user_id)

                if not internal_judges:
                    print("❌ No internal judge available!")
                    all_judges = get_available_internal_judges()
                    if all_judges and len(all_judges) == 1 and all_judges[0]["user_id"] == professor.user_id:
                        print("ℹ️ Only you (advisor) are available, which cannot be selected.")
                    input("\nPress Enter to continue...")
                    continue

                print("\nAvailable Internal Judges:")
                for i, judge in enumerate(internal_judges, 1):
                    print(f"{i}. {judge['name']} - Capacity: {judge.get('judge_capacity', 0)}")

                all_judges = get_available_internal_judges()
                professor_judge = next((j for j in all_judges if j["user_id"] == professor.user_id), None)
                if professor_judge:
                    print(f"👑 You (Advisor) - Capacity: {professor_judge.get('judge_capacity', 0)} - Not selectable")

                try:
                    choice = int(input("\nSelect internal judge number: ")) - 1
                    if choice < 0 or choice >= len(internal_judges):
                        print("❌ Invalid selection!")
                        continue

                    internal_judge = internal_judges[choice]["user_id"]
                    internal_judge_name = internal_judges[choice]["name"]
                    print(f"✅ Internal Judge Selected: {internal_judge_name}")

                except (ValueError, IndexError):
                    print("❌ Invalid selection!")
                    continue

                # Select external judge
                print("\n👨‍🏫 Select External Judge:")
                print("-" * 30)

                external_judges = get_available_external_judges()

                if not external_judges:
                    print("❌ No external judge available!")
                    input("\nPress Enter to continue...")
                    continue

                print("\nAvailable External Judges:")
                for i, judge in enumerate(external_judges, 1):
                    print(f"{i}. {judge['name']} - Capacity: {judge.get('judge_capacity', 0)}")

                try:
                    choice = int(input("\nSelect external judge number: ")) - 1
                    if choice < 0 or choice >= len(external_judges):
                        print("❌ Invalid selection!")
                        continue

                    external_judge = external_judges[choice]["user_id"]
                    external_judge_name = external_judges[choice]["name"]
                    print(f"✅ External Judge Selected: {external_judge_name}")

                except (ValueError, IndexError):
                    print("❌ Invalid selection!")
                    continue

                # Update request
                selected_request["status"] = "Approved"
                selected_request["approved_date"] = date.today().strftime("%Y-%m-%d")
                selected_request["defense_date"] = defense_date
                selected_request["internal_judge_id"] = internal_judge
                selected_request["external_judge_id"] = external_judge

                for i, req in enumerate(defense_requests):
                    if req["student_id"] == selected_request["student_id"]:
                        defense_requests[i] = selected_request
                        break

                if write_json("data/requests/defense_requests.json", defense_requests):
                    if decrease_judge_capacity(internal_judge, is_external=False) and decrease_judge_capacity(
                            external_judge, is_external=True):

                        print("✅ Defense request approved and details saved.")
                        print("✅ Judge capacities updated.")

                        print(f"\n📋 Defense Information:")
                        print(f"   📅 Defense Date: {defense_date}")
                        print(f"   👨‍🏫 Internal Judge: {internal_judge_name}")
                        print(f"   👨‍🏫 External Judge: {external_judge_name}")

                    else:
                        print("⚠️ Approved, but judge capacity update failed!")

                else:
                    print("❌ Error saving changes!")

                input("\nPress Enter to continue...")
                break

            elif action == "6":
                # Back
                print("Returning to main menu...")
                break

            else:
                print("❌ Invalid option!")

            input("\nPress Enter to continue...")

    except (ValueError, IndexError):
        print("❌ Invalid selection!")

    input("\nPress Enter to go back...")


def grade_defense_sessions(professor):
    """Grading defended sessions"""
    print("\n📝 Grade Defended Sessions")
    print("=" * 50)

    defense_requests = read_json("data/requests/defense_requests.json")
    today = date.today()

    professor_defense_requests = [
        r for r in defense_requests
        if (r.get("internal_judge_id") == professor.user_id or r.get("external_judge_id") == professor.user_id)
           and r.get("status") == "تایید شده"
           and "defense_date" in r
    ]

    graded_defenses = []
    for req in professor_defense_requests:
        try:
            defense_date = datetime.strptime(req["defense_date"], "%Y-%m-%d").date()
            if defense_date <= today:
                graded_defenses.append(req)
        except ValueError:
            continue

    if not graded_defenses:
        print("✅ No defense sessions available for grading.")
        input("\nPress Enter to return...")
        return

    print("\n📝 List of defended sessions for grading:")
    print("=" * 60)

    students = read_json("data/users/students.json")
    students_dict = {s["user_id"]: s for s in students} if students else {}

    for i, req in enumerate(graded_defenses, 1):
        student_info = students_dict.get(req["student_id"], {})
        student_name = student_info.get("name", "Unknown")

        role = "Internal Judge" if req.get("internal_judge_id") == professor.user_id else "External Judge"

        if role == "Internal Judge":
            already_graded = "internal_grade" in req
            grade_display = f"Previous grade: {req['internal_grade']}" if already_graded else "Needs grading"
        else:
            already_graded = "external_grade" in req
            grade_display = f"Previous grade: {req['external_grade']}" if already_graded else "Needs grading"

        print(f"\n{i}. 👨‍🎓 Student: {student_name}")
        print(f"   🔢 Student ID: {req['student_id']}")
        print(f"   📚 Title: {req.get('title', 'Unknown')}")
        print(f"   📅 Defense Date: {req.get('defense_date', 'Unknown')}")
        print(f"   👨‍🏫 Your Role: {role}")
        print(f"   📊 Status: {grade_display}")
        print("-" * 40)

    try:
        choice = int(input("\n🎯 Enter defense number to grade: ")) - 1

        if choice < 0 or choice >= len(graded_defenses):
            print("❌ Invalid defense number!")
            input("\nPress Enter to return...")
            return

        selected_defense = graded_defenses[choice]
        student_info = students_dict.get(selected_defense["student_id"], {})
        student_name = student_info.get("name", "Unknown")

        is_internal_judge = selected_defense.get("internal_judge_id") == professor.user_id
        role = "Internal Judge" if is_internal_judge else "External Judge"

        print(f"\n📋 Grading defense for student {student_name} ({role}):")
        print("=" * 50)
        print(f"📚 Title: {selected_defense.get('title', 'Unknown')}")
        print(f"📅 Defense Date: {selected_defense.get('defense_date', 'Unknown')}")

        if (is_internal_judge and "internal_grade" in selected_defense) or (
                not is_internal_judge and "external_grade" in selected_defense):
            print("⚠️  You have already graded this defense.")
            change_grade = input("Do you want to change the grade? (y/n): ").strip().lower()
            if change_grade != 'y':
                print("❌ Grading canceled.")
                input("\nPress Enter to return...")
                return

        while True:
            try:
                grade = input("\n💯 Enter grade (0-20): ").strip()
                grade_value = float(grade)

                if 0 <= grade_value <= 20:
                    break
                else:
                    print("❌ Grade must be between 0 and 20!")
            except ValueError:
                print("❌ Please enter a valid number!")

        if grade_value >= 17:
            letter_grade = "A"
        elif grade_value >= 14:
            letter_grade = "B"
        elif grade_value >= 10:
            letter_grade = "C"
        else:
            letter_grade = "D"

        print(f"📊 Letter Grade: {letter_grade}")

        confirm = input("\n❓ Are you sure about the entered grade? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ Grading canceled.")
            input("\nPress Enter to return...")
            return

        if is_internal_judge:
            selected_defense["internal_grade"] = grade_value
            selected_defense["internal_grade_date"] = today.strftime("%Y-%m-%d")
        else:
            selected_defense["external_grade"] = grade_value
            selected_defense["external_grade_date"] = today.strftime("%Y-%m-%d")

        both_graded = "internal_grade" in selected_defense and "external_grade" in selected_defense

        if both_graded:
            print("✅ Both judges have graded.")

            internal_grade = selected_defense["internal_grade"]
            external_grade = selected_defense["external_grade"]
            final_grade = (internal_grade + external_grade) / 2

            if final_grade >= 17:
                final_letter_grade = "A"
            elif final_grade >= 14:
                final_letter_grade = "B"
            elif final_grade >= 10:
                final_letter_grade = "C"
            else:
                final_letter_grade = "D"

            selected_defense["final_grade"] = final_grade
            selected_defense["final_letter_grade"] = final_letter_grade
            selected_defense["status"] = "Closed"

            courses = read_json("data/courses/thesis_courses.json")
            for course in courses:
                if course["professor_id"] == selected_defense["professor_id"]:
                    course["capacity"] = course.get("capacity", 0) + 1
                    print(f"✅ Capacity of course '{course['title']}' increased to {course['capacity']}.")
                    break
            write_json("data/courses/thesis_courses.json", courses)

            print(f"🎯 Final Grade: {final_grade:.2f} ({final_letter_grade})")
            print("✅ Thesis closed.")

            defended_theses = read_json("data/theses/defended_theses.json")
            defended_theses.append(selected_defense.copy())
            write_json("data/theses/defended_theses.json", defended_theses)

            print("✅ Thesis information added to archive.")
        else:
            print("✅ Your grade has been recorded.")

        for i, req in enumerate(defense_requests):
            if req["student_id"] == selected_defense["student_id"]:
                defense_requests[i] = selected_defense
                break

        write_json("data/requests/defense_requests.json", defense_requests)
        print("✅ Grade saved successfully.")

    except (ValueError, IndexError):
        print("❌ Invalid selection!")

    professors = read_json("data/users/professors.json")
    for judge in professors:
        if judge["user_id"] == professor.user_id:
            judge["judge_capacity"] = judge.get("judge_capacity", 0) + 1
            print(f"✅ Your judging capacity increased to {judge['judge_capacity']}.")
            break

    write_json("data/users/professors.json", professors)

    input("\nPress Enter to return...")

def search_theses():
    """Search in thesis database"""
    print("\n🔍 Thesis Database Search")
    print("=" * 50)

    print("\n📋 Search types:")
    print("1. Thesis Title")
    print("2. Supervisor Name")
    print("3. Keywords")
    print("4. Author (Student) Name")
    print("5. Defense Year")
    print("6. Judges")

    try:
        choice = input("\n🎯 Select search type (1-6): ").strip()
        search_types = {
            "1": "title",
            "2": "professor",
            "3": "keywords",
            "4": "author",
            "5": "year",
            "6": "judges"
        }

        if choice not in search_types:
            print("❌ Invalid selection!")
            input("\nPress Enter to return...")
            return

        search_query = input("🔍 Enter search query: ").strip()

        if not search_query:
            print("❌ Search query cannot be empty!")
            input("\nPress Enter to return...")
            return

        from src.utils.helpers import search_theses, open_file
        results = search_theses(search_query, search_types[choice])

        print(f"\n✅ Number of results found: {len(results)}")
        print("=" * 60)

        if not results:
            print("❌ No results found.")
        else:
            students = read_json("data/users/students.json")
            professors = read_json("data/users/professors.json")
            external_judges = read_json("data/users/external_judges.json")

            students_dict = {s["user_id"]: s for s in students}
            professors_dict = {p["user_id"]: p for p in professors}
            external_judges_dict = {j["user_id"]: j for j in external_judges}

            for i, thesis in enumerate(results, 1):
                student_name = students_dict.get(thesis.get("student_id", ""), {}).get("name", "Unknown")
                professor_name = professors_dict.get(thesis.get("professor_id", ""), {}).get("name", "Unknown")
                internal_judge_name = professors_dict.get(thesis.get("internal_judge_id", ""), {}).get("name", "Unknown")
                external_judge_name = external_judges_dict.get(thesis.get("external_judge_id", ""), {}).get("name", "Unknown")

                from src.utils.helpers import get_semester_year

                if thesis.get("defense_date"):
                    semester_info = get_semester_year(thesis["defense_date"])

                print(f"\n{i}. 📚 Title: {thesis.get('title', 'Unknown')}")
                print(f"   📝 Abstract: {thesis.get('abstract', 'Unknown')[:100]}...")
                print(f"   🔖 Keywords: {', '.join(thesis.get('keywords', []))}")
                print(f"   👨‍🎓 Author: {student_name}")
                print(f"   📅 Year/Semester: {semester_info}")
                print(f"   👨‍🏫 Supervisor: {professor_name}")
                print(f"   👨‍⚖️ Internal Judge: {internal_judge_name}")
                print(f"   👨‍⚖️ External Judge: {external_judge_name}")
                print(f"   📊 Grade: {thesis.get('final_grade', 'Unknown')}")
                print(f"   🏆 Letter Grade: {thesis.get('final_letter_grade', 'Unknown')}")
                print(f"   📁 File: {thesis.get('file_path', 'Unknown')}")
                print("-" * 60)

        if results:
            print("\n📋 Results Management:")
            print("1. Open a thesis file")
            print("2. Return to main menu")

            manage_choice = input("Please select an option: ").strip()

            if manage_choice == "1":
                try:
                    thesis_choice = int(input("Enter thesis number to open file: ")) - 1
                    if 0 <= thesis_choice < len(results):
                        thesis = results[thesis_choice]
                        if thesis.get('file_path'):
                            file_path = get_full_path(thesis['file_path'])
                            if os.path.exists(file_path):
                                open_file(file_path)
                                print("✅ File opened.")
                            else:
                                print("❌ File not found!")
                        else:
                            print("❌ No file available for this thesis.")
                    else:
                        print("❌ Invalid number!")
                except ValueError:
                    print("❌ Please enter a number!")

    except Exception as e:
        print(f"❌ Search error: {e}")

    input("\nPress Enter to return...")

def change_password(professor):
    """تغییر رمز عبور"""
    print("\n🔑 Change Password")
    print("-" * 40)

    old_password = input("Enter current password: ").strip()
    new_password = input("Enter new password: ").strip()
    confirm_password = input("Confirm new password: ").strip()

    # استفاده از تابع change_password از auth.py
    from src.utils.auth import change_password as auth_change_password
    auth_change_password(professor, old_password, new_password, confirm_password)

    input("\nبرای بازگشت Enter بزنید...")