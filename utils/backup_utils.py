import os
from datetime import date

from utils.zip_snapshot import create_zip_snapshot
from gdbackup import backupGDrive

MARKER_FILE = "cache/last_backup.txt"


def should_run_backup_today():
    today = date.today().isoformat()

    if not os.path.exists(MARKER_FILE):
        return True

    with open(MARKER_FILE, "r") as f:
        last = f.read().strip()

    return last != today


def update_last_backup_info(zip_path):
    os.makedirs("cache", exist_ok=True)
    with open(MARKER_FILE, "w") as f:
        f.write(date.today().isoformat())


def run_backup(force=False):
    # Auto backup → respect once-per-day
    if not force and not should_run_backup_today():
        return False

    # Create ZIP snapshot
    zip_path = create_zip_snapshot()

    # Upload to Google Drive
    backup = backupGDrive(zip_path)
    backup.get_creds()
    success = backup.initiateBackup()

    # Update marker only on success
    if success:
        update_last_backup_info(zip_path)

    return success

# Backward compatibility
def mark_backup_done(zip_path=None):
    update_last_backup_info(zip_path)

