import os
import pickle
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from tkinter import messagebox

SCOPES = ['https://www.googleapis.com/auth/drive.file']

class backupGDrive:
    def __init__(self, file_path):
        self.file_path = file_path
        self.creds = None

    #AUTH
    def get_creds(self):
        if os.path.exists("token.pickle"):
            with open("token.pickle", "rb") as token:
                self.creds = pickle.load(token)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                self.creds = flow.run_console()

            with open("token.pickle", "wb") as token:
                pickle.dump(self.creds, token)

    #UPLOAD ZIP
    def initiateBackup(self):
        try:
            if not os.path.exists(self.file_path):
                messagebox.showerror("ERROR", "Backup ZIP not found")
                raise FileNotFoundError("Backup ZIP not found")

            service = build("drive", "v3", credentials=self.creds)

            folder_id = self._get_or_create_backup_folder(service)

            file_name = os.path.basename(self.file_path)

            # STEP 1: Upload to Drive (root)
            media = MediaFileUpload(self.file_path, resumable=True)
            file = service.files().create(
                body={"name": file_name},
                media_body=media,
                fields="id, parents"
            ).execute()

            file_id = file["id"]
            previous_parents = ",".join(file.get("parents", []))

            # STEP 2: MOVE file into folder
            service.files().update(
                fileId=file_id,
                addParents=folder_id,
                removeParents=previous_parents,
                fields="id, parents"
            ).execute()

            return True

        except HttpError as e:
            print(f"[GDRIVE ERROR] {e}")
            return False
        except Exception as e:
            print(f"[BACKUP ERROR] {e}")
            return False

    
    #FOLDER HANDLING
    def _get_or_create_backup_folder(self, service):
        folder_name = "LatestBackup_SIAS"

        response = service.files().list(
            q=(
                f"name='{folder_name}' "
                "and mimeType='application/vnd.google-apps.folder' "
                "and 'root' in parents "
                "and trashed=false"
            ),
            spaces="drive",
            fields="files(id)"
        ).execute()

        if response.get("files"):
            return response["files"][0]["id"]

        folder = service.files().create(
            body={
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": ["root"]
            },
            fields="id"
        ).execute()

        return folder["id"]

