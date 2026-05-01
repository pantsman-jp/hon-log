import os
import sys
import requests


def resource_path(*path_parts):
    if hasattr(sys, "_MEIPASS"):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, *path_parts)


def get_latest_version(repo_url):
    try:
        url = f"https://api.github.com/repos/{repo_url}/releases/latest"
        headers = {"User-Agent": "hon-log-app"}
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        return response.json().get("tag_name")
    except Exception:
        return None
