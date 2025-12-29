import sys
import os

def app_root():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__ + "/.."))

def resource_path(*paths):
    return os.path.join(app_root(), *paths)
