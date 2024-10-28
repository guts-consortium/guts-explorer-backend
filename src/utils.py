import json
from datetime import datetime
from flask import abort

# Functions
def sort_by_datetime(items, dt_key):
    return sorted(items, key=lambda x: datetime.fromisoformat(x[dt_key]), reverse=True)

def load_json_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        abort(404, description="Metadata file not found.")
    except json.JSONDecodeError:
        abort(500, description="Error decoding metadata file.")

def write_json_to_file(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def find_element_in_list(arr, key, val, mode='equals'):
    if mode == 'contains':
        found_el = [el for el in arr if val in el[key]]
    else:
        found_el = [el for el in arr if el[key] == val]
    if len(found_el) == 0:
        return found_el
    elif len(found_el) == 1:
        return found_el[0]
    else:
        raise ValueError(f"Multiple elements found in list where 'el[{key}]' {mode} '{val}'")