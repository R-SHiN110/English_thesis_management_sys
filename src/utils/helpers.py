from datetime import datetime, timedelta
import re
from src.utils.file_io import read_json, write_json

def validate_email(email: str) -> bool:
    """Check if email format is valid"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone: str) -> bool:
    """Check if Iranian phone number format is valid"""
    pattern = r'^09[0-9]{9}$'
    return re.match(pattern, phone) is not None


def is_valid_date(date_string: str, date_format: str = "%Y-%m-%d") -> bool:
    """Check if a date string is valid"""
    try:
        datetime.strptime(date_string, date_format)
        return True
    except ValueError:
        return False


def is_three_months_passed(start_date: str, date_format: str = "%Y-%m-%d") -> bool:
    """Check if three months have passed since the given date"""
    try:
        start = datetime.strptime(start_date, date_format)
        three_months_later = start + timedelta(days=90)  # approx. 3 months
        return datetime.now() >= three_months_later
    except ValueError:
        return False


def format_date(date_string: str, input_format: str = "%Y-%m-%d", output_format: str = "%Y/%m/%d") -> str:
    """Reformat a date string"""
    try:
        date_obj = datetime.strptime(date_string, input_format)
        return date_obj.strftime(output_format)
    except ValueError:
        return date_string


def display_menu(menu_title: str, options: list) -> None:
    """Display a nice menu in the console"""
    print(f"\n{'-' * 50}")
    print(f" {menu_title} ")
    print(f"{'-' * 50}")

    for i, option in enumerate(options, 1):
        print(f" {i}. {option}")

    print(f"{'-' * 50}")


def get_semester_year(defense_date: str, date_format: str = "%Y-%m-%d") -> str:
    """Calculate semester-year string based on thesis defense date"""
    date_obj = datetime.strptime(defense_date, date_format)
    year = date_obj.year
    month = date_obj.month

    if 1 <= month <= 6:
        return f"{year - 1}-{year} (Second Semester)"
    else:
        return f"{year}-{year + 1} (First Semester)"


def search_theses(search_query: str, search_type: str):
    """Search in defended theses"""
    try:
        theses = read_json("data/theses/defended_theses.json")

        if not theses:
            return []

        search_query = search_query.strip().lower()
        results = []

        for thesis in theses:
            if search_type == "title" and search_query in thesis.get("title", "").lower():
                results.append(thesis)

            elif search_type == "professor":
                prof_id = thesis.get("professor_id", "")
                professors = read_json("data/users/professors.json")
                professor = next((p for p in professors if p["user_id"] == prof_id), {})
                if search_query in professor.get("name", "").lower():
                    results.append(thesis)

            elif search_type == "keywords":
                keywords = thesis.get("keywords", [])
                if any(search_query in keyword.lower() for keyword in keywords):
                    results.append(thesis)

            elif search_type == "author":
                student_id = thesis.get("student_id", "")
                students = read_json("data/users/students.json")
                student = next((s for s in students if s["user_id"] == student_id), {})
                if search_query in student.get("name", "").lower():
                    results.append(thesis)

            elif search_type == "year":
                defense_date = thesis.get("defense_date", "")
                if defense_date.startswith(search_query):
                    results.append(thesis)

            elif search_type == "judges":
                internal_judge_id = thesis.get("internal_judge_id", "")
                external_judge_id = thesis.get("external_judge_id", "")

                professors = read_json("data/users/professors.json")
                external_judges = read_json("data/users/external_judges.json")

                internal_judge = next((p for p in professors if p["user_id"] == internal_judge_id), {})
                external_judge = next((j for j in external_judges if j["user_id"] == external_judge_id), {})

                if (search_query in internal_judge.get("name", "").lower() or
                        search_query in external_judge.get("name", "").lower()):
                    results.append(thesis)

        return results

    except Exception as e:
        print(f"❌ Error during search: {e}")
        return []


def open_file(file_path):
    """Open a file with the system's default program"""
    import os
    import subprocess
    import sys
    try:
        if os.name == 'nt':  # Windows
            os.startfile(file_path)
        elif os.name == 'posix':  # macOS, Linux
            if sys.platform == 'darwin':  # macOS
                subprocess.call(('open', file_path))
            else:  # Linux
                subprocess.call(('xdg-open', file_path))
        return True
    except Exception as e:
        print(f"❌ Error opening file: {e}")
        return False
