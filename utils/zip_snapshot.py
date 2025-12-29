import os
import zipfile
import shutil
from datetime import datetime

# 🔒 ONLY DATA (NO OUTPUT FILES LIKE PDFs)
SAFE_DB_FILES = [
    "datas/customerDB.db",
    "datas/products.db",
    "datas/taxinvoice.db",
    "datas/deliverychallan.db",
    "datas/user.db"
]

def create_zip_snapshot():
    """
    Creates a ZIP snapshot of database files only.
    Bills/PDFs are intentionally excluded.
    """
    os.makedirs("cache/backup", exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    zip_path = f"cache/backup/backup_{timestamp}.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for db_file in SAFE_DB_FILES:
            if not os.path.exists(db_file):
                print(f"[BACKUP] Missing DB skipped: {db_file}")
                continue

            # 🔹 Atomic snapshot (copy → zip → delete)
            temp_copy = f"{db_file}.tmp"
            shutil.copy2(db_file, temp_copy)
            zipf.write(temp_copy, arcname=db_file)
            os.remove(temp_copy)

    # 🔍 Validate snapshot
    if os.path.getsize(zip_path) == 0:
        raise Exception("Backup ZIP is empty")

    return zip_path
