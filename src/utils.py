import os
import sys


def resource_path(*path_parts):
    if hasattr(sys, "_MEIPASS"):
        base_directory = sys._MEIPASS
    else:
        base_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_directory, *path_parts)
