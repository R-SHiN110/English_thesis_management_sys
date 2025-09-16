import hashlib
from typing import Optional, Dict, Any
from src.models.user import Student, Professor, User, external_judge
from src.utils.file_io import read_json, write_json


def hash_password(password: str) -> str:
    """
    Hash the password using SHA-256
    """
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def change_password(user: User, old_password: str, new_password: str, confirm_password: str) -> bool:
    """
    Change user password
    Returns: True if successful, False if failed
    """
    try:
        role = user.get_role()
        file_path = f"data/users/{role}s.json"

        users_data = read_json(file_path)

        if not users_data:
            print("❌ Error reading users data!")
            return False

        user_data = next((u for u in users_data if u["user_id"] == user.user_id), None)

        if not user_data:
            print("❌ User not found!")
            return False

        hashed_old_password = hash_password(old_password)
        if user_data["password"] != hashed_old_password:
            print("❌ Current password is incorrect!")
            return False

        if new_password != confirm_password:
            print("❌ New passwords do not match!")
            return False

        hashed_new_password = hash_password(new_password)

        user_data["password"] = hashed_new_password
        user._password = hashed_new_password

        if write_json(file_path, users_data):
            print("✅ Password changed successfully.")
            return True
        else:
            print("❌ Error saving changes!")
            return False

    except Exception as e:
        print(f"❌ Unknown error: {e}")
        return False


def verify_user(user_id: str, password: str, role: str) -> Optional[User]:
    """
    Verify user credentials and return a User object if successful
    """
    try:
        if role == "student":
            file_path = "data/users/students.json"
        elif role == "professor":
            file_path = "data/users/professors.json"
        else:
            file_path = "data/users/external_judges.json"

        users_data = read_json(file_path)

        user_data = next((u for u in users_data if u["user_id"] == user_id), None)

        if user_data:
            hashed_input_password = hash_password(password)
            if user_data["password"] == hashed_input_password:
                if role == "student":
                    return Student(
                        user_data["user_id"],
                        user_data["national_id"],
                        user_data["name"],
                        user_data["password"]
                    )
                elif role == "professor":
                    return Professor(
                        user_data["user_id"],
                        user_data["national_id"],
                        user_data["name"],
                        user_data["password"]
                    )
                else:
                    return external_judge(
                        user_data["user_id"],
                        user_data["national_id"],
                        user_data["name"],
                        user_data["password"]
                    )
        return None
    except Exception as e:
        print(f"Error verifying user: {e}")
        return None


def find_user_by_id(user_id: str, role: str) -> Optional[Dict[str, Any]]:
    """
    Find user by ID and role
    Returns: user data dictionary or None
    """
    try:
        file_path = "data/users/students.json" if role == "student" else "data/users/professors.json"
        users_data = read_json(file_path)
        return next((u for u in users_data if u["user_id"] == user_id), None)
    except Exception as e:
        print(f"Error finding user: {e}")
        return None


def get_user_name(user_id: str, role: str) -> str:
    """
    Get user's name by ID and role
    Returns: user's name or 'Unknown'
    """
    user_data = find_user_by_id(user_id, role)
    return user_data.get("name", "Unknown") if user_data else "Unknown"


def get_all_professors() -> list:
    """
    Get list of all professors
    Returns: list of professor data dictionaries
    """
    try:
        return read_json("data/users/professors.json")
    except Exception as e:
        print(f"Error fetching professors list: {e}")
        return []


def get_all_students() -> list:
    """
    Get list of all students
    Returns: list of student data dictionaries
    """
    try:
        return read_json("data/users/students.json")
    except Exception as e:
        print(f"Error fetching students list: {e}")
        return []
