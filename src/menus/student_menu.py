from src.utils.helpers import display_menu
from src.utils.file_io import read_json, write_json
from src.utils.auth import find_user_by_id
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import shutil
import os
from src.utils.file_io import get_full_path


def show_student_menu(student):
    """Display main student menu"""
    while True:
        menu_title = f"Student Menu - {student.name}"
        options = [
            "Request Thesis Course",
            "Submit Defense Request",
            "View Request Status",
            "Search Thesis Database",
            "Change Password",
            "Logout"
        ]

        display_menu(menu_title, options)

        choice = input("Please select an option: ").strip()

        if choice == "1":
            request_thesis_course(student)
        elif choice == "2":
            request_defense(student)
        elif choice == "3":
            view_request_status(student)
        elif choice == "4":
            search_theses()
        elif choice == "5":
            change_password(student)
        elif choice == "6":
            print("Logging out...")
            break
        else:
            print("⚠️ Invalid option!")
            input("Press Enter to continue...")


def request_thesis_course(student):
    """Request thesis course"""
    print("\n📝 Thesis Course Request")
    print("=" * 50)

    courses = read_json("data/courses/thesis_courses.json")

    if not courses:
        print("❌ No courses available in the system.")
        input("\nPress Enter to go back...")
        return

    thesis_courses = [c for c in courses if c["title"].startswith("پایان نامه")]

    if not thesis_courses:
        print("❌ No thesis courses available in the system.")
        input("\nPress Enter to go back...")
        return

    available_courses = [c for c in courses if c["capacity"] > 0]

    if not available_courses:
        print("❌ No courses with available capacity.")
        input("\nPress Enter to go back...")
        return

    requests = read_json("data/requests/enrollment_requests.json")

    existing_thesis_request = next((r for r in requests
                                    if r["student_id"] == student.user_id
                                    and any(c["course_id"] == r["course_id"] for c in thesis_courses)), None)

    if existing_thesis_request:
        print("❌ You have already requested a thesis course!")
        print("⚠️ Only one thesis course can be requested.")
        input("\nPress Enter to go back...")
        return

    print("\n🎓 Available Thesis Courses:")

    for course in available_courses:
        professor_data = find_user_by_id(course["professor_id"], "professor")
        professor_name = professor_data["name"] if professor_data else "Unknown"
        print(f"\n🔹 Course ID: {course['course_id']}")
        print(f"   📚 Title: {course['title']}")
        print(f"   👨‍🏫 Professor: {professor_name}")
        print(f"   📅 Year/Semester: {course['year']} / {course['semester']}")
        print(f"   👥 Capacity: {course['capacity']}")
        print(f"   🕒 Sessions: {course['sessions_count']}")
        print(f"   📘 Units: {course['units']}")
        print(f"   📂 Resources: {course['resources']}")
        print("-" * 40)

    course_id = input("\n🎯 Please enter the Course ID: ").strip()

    selected_course = next((c for c in available_courses if c["course_id"] == course_id), None)

    if not selected_course:
        print("❌ Invalid Course ID!")
        input("\nPress Enter to go back...")
        return

    professor_data = find_user_by_id(selected_course["professor_id"], "professor")
    professor_name = professor_data["name"] if professor_data else "Unknown"

    print(f"\n📋 Selected Course Information:")
    print(f"   🔹 Course ID: {selected_course['course_id']}")
    print(f"   📚 Title: {selected_course['title']}")
    print(f"   👨‍🏫 Professor: {professor_name}")
    print(f"   📅 Year/Semester: {selected_course['year']} / {selected_course['semester']}")

    confirm = input("\n❓ Are you sure about your selection? (y/n): ").strip().lower()

    if confirm != 'y':
        print("❌ Request cancelled.")
        input("\nPress Enter to go back...")
        return

    from datetime import date
    new_request = {
        "student_id": student.user_id,
        "course_id": selected_course["course_id"],
        "professor_id": selected_course["professor_id"],
        "status": "Pending Professor Approval",
        "created_at": date.today().strftime("%Y-%m-%d"),
        "approved_date": "-",
        "rejected_date": "-"
    }

    requests.append(new_request)

    for course in courses:
        if course["course_id"] == selected_course["course_id"]:
            if course["capacity"] > 0:
                course["capacity"] -= 1
                print(f"✅ Course capacity reduced to {course['capacity']}.")
            else:
                print("❌ Error: Course capacity already full!")
                input("\nPress Enter to go back...")
                return
            break

    if write_json("data/requests/enrollment_requests.json", requests):
        if write_json("data/courses/thesis_courses.json", courses):
            print("\n✅ Your request has been successfully submitted and sent to the professor.")

        print(f"\n📋 Request Information:")
        print(f"   📚 Course: {selected_course['title']}")
        print(f"   👨‍🏫 Professor: {professor_name}")
        print(f"   📅 Request Date: {new_request['created_at']}")
        print(f"   📊 Status: {new_request['status']}")
    else:
        print("❌ Error in submitting request!")

    input("\nPress Enter to go back...")


def request_defense(student):
    """Submit defense request"""
    print("\n🎓 Submit Defense Request")
    print("=" * 50)

    # Read thesis enrollment requests
    enrollment_requests = read_json("data/requests/enrollment_requests.json")

    # Find student's approved enrollment request
    approved_request = next((r for r in enrollment_requests
                             if r["student_id"] == student.user_id
                             and r["status"] == "Approved"), None)

    if not approved_request:
        print("❌ You cannot submit a defense request due to course status.")
        print("ℹ️ Either you haven't submitted a request or it hasn't been approved yet.")
        input("\nPress Enter to go back...")
        return

    # Check if student already has a defense request that hasn't been rejected
    defense_requests = read_json("data/requests/defense_requests.json")
    existing_defense_request = next((r for r in defense_requests
                                     if r["student_id"] == student.user_id
                                     and r["status"] != "Rejected"), None)

    if existing_defense_request:
        print("❌ You have already submitted a defense request!")
        print(f"📊 Previous request status: {existing_defense_request['status']}")

        if existing_defense_request["status"] == "Pending Professor Approval":
            print("ℹ️ Please wait for the professor's review.")
        elif existing_defense_request["status"] == "Approved":
            print("ℹ️ Your defense request has already been approved.")

        input("\nPress Enter to go back...")
        return

    # Check approval date
    if approved_request.get("approved_date") == "-":
        print("❌ Error in request information! Approval date is missing.")
        print("ℹ️ Please contact your professor or support.")
        input("\nPress Enter to go back...")
        return

    try:
        approval_date = datetime.strptime(approved_request["approved_date"], "%Y-%m-%d").date()
        today = date.today()
        deadline = approval_date + relativedelta(months=3)

        if today < deadline:
            print("⏳ Warning: Three months have not passed since approval ⏳")

            time_passed = relativedelta(today, approval_date)
            time_remaining = relativedelta(deadline, today)

            print(f"📅 Approval Date: {approval_date}")
            print(f"⏰ Time passed: {time_passed.months} months and {time_passed.days} days")
            print(f"⏳ You can submit your defense request in {time_remaining.months} months and {time_remaining.days} days")

            input("\nPress Enter to go back...")
            return

        # If three months have passed
        print("✅ Three months have passed since your request approval")
        print(f"📅 Approval Date: {approval_date}")
        print("⬅️ Enter 1 if you are ready to submit your defense request:")

        choice = input("👉 ").strip()

        if choice == '1':
            print("\n📋 Please fill in the required information:")
            print("-" * 40)

            # Thesis information
            title = input("Thesis Title: ").strip()
            abstract = input("Thesis Abstract: ").strip()
            keywords_input = input("Keywords (separated by '-'): ").strip()
            keywords = [k.strip() for k in keywords_input.split('-')] if keywords_input else []

            # PDF upload
            print("\n📁 Upload Thesis PDF:")
            print("ℹ️ Enter the full path to your PDF file")
            pdf_path = input("PDF File Path: ").strip()

            # First page image
            print("\n📸 Upload First Page Image:")
            print("ℹ️ Enter the path to the first page image")
            first_page_path = input("First Page Image Path: ").strip()

            # Last page image
            print("\n📸 Upload Last Page Image:")
            print("ℹ️ Enter the path to the last page image")
            last_page_path = input("Last Page Image Path: ").strip()

            # Check images
            image_paths = [first_page_path, last_page_path]
            for img_path in image_paths:
                if not os.path.exists(img_path):
                    print(f"❌ Image file not found: {img_path}")
                    input("\nPress Enter to go back...")
                    return
                if not img_path.lower().endswith(('.jpg', '.jpeg', '.png')):
                    print(f"❌ Invalid image format: {img_path}")
                    print("ℹ️ Only JPG, JPEG, PNG are allowed!")
                    input("\nPress Enter to go back...")
                    return

            # Check PDF file
            if not os.path.exists(pdf_path):
                print("❌ PDF file not found! Please check the path.")
                input("\nPress Enter to go back...")
                return
            if not pdf_path.lower().endswith('.pdf'):
                print("❌ Only PDF files are allowed!")
                input("\nPress Enter to go back...")
                return

            # Generate filenames
            base_filename = f"{student.user_id}.{approved_request['course_id']}"
            pdf_filename = f"{base_filename}.pdf"
            first_page_filename = f"{base_filename}.page1.jpg"
            last_page_filename = f"{base_filename}.page2.jpg"

            documents_dir = get_full_path("documents")
            theses_dir = os.path.join(documents_dir, "theses")
            images_dir = os.path.join(documents_dir, "images")

            os.makedirs(theses_dir, exist_ok=True)
            os.makedirs(images_dir, exist_ok=True)

            pdf_destination = os.path.join(theses_dir, pdf_filename)
            first_page_destination = os.path.join(images_dir, first_page_filename)
            last_page_destination = os.path.join(images_dir, last_page_filename)

            try:
                shutil.copy2(pdf_path, pdf_destination)
                shutil.copy2(first_page_path, first_page_destination)
                shutil.copy2(last_page_path, last_page_destination)

                print("✅ All files uploaded successfully:")
                print(f"   📄 PDF: {pdf_filename}")
                print(f"   📸 First Page: {first_page_filename}")
                print(f"   📸 Last Page: {last_page_filename}")

                relative_pdf_path = f"documents/theses/{pdf_filename}"
                relative_image_path = [f"documents/images/{base_filename}.page1.jpg",
                                       f"documents/images/{base_filename}.page2.jpg"]

            except Exception as e:
                print(f"❌ File upload error: {e}")
                input("\nPress Enter to go back...")
                return

            # Create defense request
            defense_requests = read_json("data/requests/defense_requests.json")
            new_defense_request = {
                "student_id": student.user_id,
                "professor_id": approved_request["professor_id"],
                "title": title,
                "abstract": abstract,
                "keywords": keywords,
                "status": "Pending Professor Approval",
                "submission_date": today.strftime("%Y-%m-%d"),
                "file_path": relative_pdf_path,
                "image_path": relative_image_path
            }

            defense_requests.append(new_defense_request)

            if write_json("data/requests/defense_requests.json", defense_requests):
                print("\n✅ Your defense request has been successfully submitted.")
            else:
                print("❌ Error submitting defense request!")

        else:
            print("❌ Invalid option! Request cancelled.")

    except ValueError:
        print("❌ Date format error! Please contact support.")
    except Exception as e:
        print(f"❌ Unknown error: {e}")

    input("\nPress Enter to go back...")


def view_request_status(student):
    """View the status of the student's latest request"""
    # print("\n📊 Your latest requests status")
    # print("=" * 50)

    # Read enrollment requests
    requests = read_json("data/requests/enrollment_requests.json")

    # Search from the end to find the latest request
    latest_request = None
    for i in range(len(requests) - 1, -1, -1):
        if requests[i]["student_id"] == student.user_id:
            latest_request = requests[i]
            break

    if not latest_request:
        print("❌ No request has been submitted.")
        print("ℹ️  You can submit a request from 'Thesis Course Enrollment'.")
        input("\nPress Enter to go back...")
        return

    # Read courses info
    courses = read_json("data/courses/thesis_courses.json")
    courses_dict = {c["course_id"]: c for c in courses} if courses else {}

    # Read professors info
    professors = read_json("data/users/professors.json")
    professors_dict = {p["user_id"]: p for p in professors} if professors else {}

    # Display latest request info
    course_info = courses_dict.get(latest_request["course_id"], {})
    professor_info = professors_dict.get(latest_request["professor_id"], {})

    course_title = course_info.get("title", "Unknown")
    professor_name = professor_info.get("name", "Unknown")

    print()
    print("🔹 Thesis course request info: ")
    print(f"👨‍🏫 Professor: {professor_name}")
    print(f"📅 Request date: {latest_request.get('created_at', 'Unknown')}")
    print(f"📊 Status: {latest_request['status']}")
    print("-" * 50)

    # Guidance messages based on status
    # print("\n💡 Guidance:")
    # print("-" * 40)

    if latest_request["status"] == "رد شده":
        print("\n💡 Guidance:")
        print("-" * 40)
        print("❌ This request has been rejected.")
        print("ℹ️  To submit again, go to 'Thesis Course Enrollment'.")

    elif latest_request["status"] == "در انتظار تأیید استاد":
        print("\n💡 Guidance:")
        print("-" * 40)
        print("⏳ This request is under review.")
        print("ℹ️  Please wait for professor approval.")

    elif latest_request["status"] == "تایید شده":
        # print("✅ This request has been approved.")

        # Check defense request status
        defense_requests = read_json("data/requests/defense_requests.json")
        latest_defense_request = None

        for i in range(len(defense_requests) - 1, -1, -1):
            if defense_requests[i]["student_id"] == student.user_id:
                latest_defense_request = defense_requests[i]
                break

        if latest_defense_request:
            print(f"🎓 Defense request status: {latest_defense_request['status']}")

            if latest_defense_request["status"] == "در انتظار تأیید استاد":
                print("⏳ Your defense request is under review by your advisor.")
                print(f"📅 Defense request submission date: {latest_defense_request.get('submission_date', 'Unknown')}")
            elif latest_defense_request["status"] == "تایید شده":
                print("✅ Your defense request has been approved.")
                print("ℹ️  You can start preparing for your defense session.")
                print(f"📅 Defense approval date: {latest_defense_request.get('approved_date', 'Unknown')}")
            elif latest_defense_request["status"] == "رد شده":
                print("❌ Your defense request has been rejected.")
                print("ℹ️  You can submit a new defense request.")
                print(f"📅 Defense rejection date: {latest_defense_request.get('rejected_date', 'Unknown')}")

        else:
            if latest_request.get("approved_date") != "-":
                try:
                    approval_date = datetime.strptime(latest_request["approved_date"], "%Y-%m-%d").date()
                    today = date.today()
                    three_months_later = approval_date + relativedelta(months=3)

                    print(f"📅 Professor approval date: {approval_date}")

                    if today >= three_months_later:
                        print("🎯 Three months have passed since your approval. You can submit a defense request!")
                    else:
                        remaining = relativedelta(three_months_later, today)
                        print(f"⏳ Time left before defense request: {remaining.months} months and {remaining.days} days.")

                except ValueError:
                    print("ℹ️  Once three months have passed since approval, you can submit a defense request.")
            else:
                print("ℹ️  Waiting for professor approval date to be recorded...")

    input("\nPress Enter to go back...")


def search_theses():
    """Search in the thesis database"""
    print("\n🔍 Search in the completed theses database")
    print("=" * 50)

    print("\n📋 Search types:")
    print("1. Thesis title")
    print("2. Supervisor name")
    print("3. Keywords")
    print("4. Author (student) name")
    print("5. Defense year")
    print("6. Judges' names")

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
            print("❌ Invalid choice!")
            input("\nPress Enter to go back...")
            return

        search_query = input("🔍 Enter search query: ").strip()

        if not search_query:
            print("❌ Search query cannot be empty!")
            input("\nPress Enter to go back...")
            return

        # Perform search
        from src.utils.helpers import search_theses, open_file
        results = search_theses(search_query, search_types[choice])

        # Display results
        print(f"\n✅ Number of results found: {len(results)}")
        print("=" * 60)

        if not results:
            print("❌ No results found.")
        else:
            # Load user data
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
                print(f"   📅 Semester/Year: {semester_info}")
                print(f"   👨‍🏫 Supervisor: {professor_name}")
                print(f"   👨‍⚖️ Internal judge: {internal_judge_name}")
                print(f"   👨‍⚖️ External judge: {external_judge_name}")
                print(f"   📊 Grade: {thesis.get('final_grade', 'Unknown')}")
                print(f"   🏆 Letter grade: {thesis.get('final_letter_grade', 'Unknown')}")
                print(f"   📁 File: {thesis.get('file_path', 'Unknown')}")
                print("-" * 60)

        # Result management menu
        if results:
            print("\n📋 Manage results:")
            print("1. Open a thesis file")
            print("2. Return to main menu")

            manage_choice = input("Please select an option: ").strip()

            if manage_choice == "1":
                try:
                    thesis_choice = int(input("Thesis number to open file: ")) - 1
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
                            print("❌ No file for this thesis.")
                    else:
                        print("❌ Invalid number!")
                except ValueError:
                    print("❌ Please enter a number!")

    except Exception as e:
        print(f"❌ Search error: {e}")

    input("\nPress Enter to go back...")


def change_password(student):
    """Change password"""
    print("\n🔒 Change password")
    print("-" * 40)

    old_password = input("Current password: ")
    new_password = input("New password: ")
    confirm_password = input("Confirm new password: ")

    # Use auth.py's change_password function
    from src.utils.auth import change_password as auth_change_password
    auth_change_password(student, old_password, new_password, confirm_password)

    input("\nPress Enter to go back...")
