import os
import sys


def get_data_path(*path_segments):
    if getattr(sys, "frozen", False):
        base_dir = os.path.join(os.path.expanduser("~"), "hon-log")
    else:
        base_dir = os.path.dirname(os.path.dirname(__file__))
    result = os.path.normpath(os.path.join(base_dir, *path_segments))
    return result


def resource_path(relative_path):
    if os.path.isabs(relative_path):
        return relative_path
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(__file__))
    result = os.path.normpath(os.path.join(base_path, relative_path))
    return result
