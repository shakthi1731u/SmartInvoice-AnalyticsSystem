import sys
import os

def get_app_data_dir():
    base = os.getenv("LOCALAPPDATA")
    app_dir = os.path.join(base, "SmartInvoice")
    os.makedirs(app_dir, exist_ok=True)
    return app_dir

def get_google_dir():
    google_dir = os.path.join(get_app_data_dir(), "google")
    os.makedirs(google_dir, exist_ok=True)
    return google_dir

def get_google_token_path():
    return os.path.join(get_google_dir(), "token.json")

def get_google_credentials_path():
    return os.path.join(get_google_dir(), "credentials.json")

def app_root():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__ + "/.."))

def resource_path(*paths):
    return os.path.join(app_root(), *paths)
