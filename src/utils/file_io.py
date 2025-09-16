import json
import os
from typing import Any, Dict, List

# Find project root path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_full_path(relative_path: str) -> str:
    """Convert relative path to absolute path relative to project root"""
    return os.path.join(PROJECT_ROOT, relative_path)


def read_json(file_path: str) -> List[Dict[str, Any]]:
    """
    Read data from a JSON file and return it as a list of dictionaries.
    If the file does not exist, returns an empty list.
    """
    try:
        full_path = get_full_path(file_path)

        if not os.path.exists(full_path):
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as file:
                json.dump([], file, ensure_ascii=False, indent=4)
            return []

        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1256']

        for encoding in encodings:
            try:
                with open(full_path, 'r', encoding=encoding) as file:
                    data = json.load(file)
                    # print(f"✅ File {file_path} read successfully with encoding {encoding}")
                    return data
            except UnicodeDecodeError:
                continue
            except json.JSONDecodeError:
                # If JSON is invalid, overwrite it
                # print(f"⚠️  File {file_path} is invalid JSON, rewriting...")
                with open(full_path, 'w', encoding='utf-8') as file:
                    json.dump([], file, ensure_ascii=False, indent=4)
                return []

        print(f"❌ Could not read file {file_path} with any encoding")
        return []

    except Exception as e:
        print(f"❌ Unknown error reading file {file_path}: {e}")
        return []


def write_json(file_path: str, data: List[Dict[str, Any]]) -> bool:
    """
    Write data (list of dictionaries) to a JSON file.
    Returns: True if successful, False if error
    """
    try:
        full_path = get_full_path(file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"❌ Error writing file {file_path}: {e}")
        return False


def get_next_id(existing_data: List[Dict[str, Any]], id_field: str = "id") -> str:
    """
    Generate a unique ID for a new record.
    Assumes IDs follow the pattern 'prefix_number' (e.g., 'request_1').
    """
    if not existing_data:
        return f"{id_field}_1"

    last_id = existing_data[-1].get(id_field, f"{id_field}_0")
    try:
        last_number = int(last_id.split('_')[-1])
        new_number = last_number + 1
    except (IndexError, ValueError):
        new_number = len(existing_data) + 1

    return f"{id_field}_{new_number}"


def save_uploaded_file(upload_folder: str, file_name: str, file_content: bytes) -> str:
    """
    Save an uploaded file (like PDF or JPG) to a specified folder.
    Returns: relative path of the saved file
    """
    try:
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, file_name)

        with open(file_path, 'wb') as file:
            file.write(file_content)

        return file_path
    except Exception as e:
        print(f"Error saving file {file_name}: {e}")
        return ""
