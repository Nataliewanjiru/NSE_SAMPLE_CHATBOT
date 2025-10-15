from google.oauth2 import service_account
from googleapiclient.discovery import build
import io
from googleapiclient.http import MediaIoBaseDownload

def get_drive_service(service_account_json_path):
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    creds = service_account.Credentials.from_service_account_file(
        service_account_json_path,
        scopes=SCOPES
    )
    return build('drive', 'v3', credentials=creds)



def list_pdf_files(service):
    results = service.files().list(
        q="mimeType='application/pdf'",
        pageSize=100,
        fields="files(id, name)"
    ).execute()
    print(results.get("files,[]"))
    return results.get('files', [])


def download_pdf(service, file_id, destination_path):
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(destination_path, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()

