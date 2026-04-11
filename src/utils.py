import os
import sys


def resource_path(*paths):
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, *paths)


def get_data_path(*paths):
    return resource_path(*paths)
