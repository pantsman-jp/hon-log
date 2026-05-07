import os
import sys
import requests


def resource_path(*parts):
    base = getattr(
        sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    return os.path.join(base, *parts)


def get_latest_version(repo):
    try:
        r = requests.get(
            f"https://api.github.com/repos/{repo}/releases/latest",
            headers={"User-Agent": "hon-log-app"},
            timeout=5,
        )
        return r.json().get("tag_name") if r.status_code == 200 else None
    except Exception:
        return None
