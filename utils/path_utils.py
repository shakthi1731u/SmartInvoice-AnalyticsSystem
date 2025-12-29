import os
import datetime

def get_invoice_and_challan_paths(base_dir):
    today = datetime.date.today()
    year = str(today.year)
    month = today.strftime("%B")
    day = today.strftime("%d")

    invoice_path = os.path.join(
        base_dir, "bills", "invoice",
        year, f"{month}-{year}", f"{day}-{month}"
    )

    challan_path = os.path.join(
        base_dir, "bills", "deliverychallan",
        year, f"{month}-{year}", f"{day}-{month}"
    )

    os.makedirs(invoice_path, exist_ok=True)
    os.makedirs(challan_path, exist_ok=True)

    return invoice_path, challan_path
