from __future__ import print_function
from main import (extract_video_id, channel_ids, get_uploads_playlist_id, 
                  videos_from_playlist, comments_from_channels, save_dataframes_to_excel,
                  clean_excel_string)
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from secret import API_KEY
import requests
import re
import os
import pickle
import io






# Example YouTube URLs
urls = [
    "https://www.youtube.com/watch?v=cO5g5qLrLSo",
    'https://www.youtube.com/watch?v=2AQKmw14mHM&list=PLblh5JKOoLUIzaEkCLIUxQFjPIlapw8nU'
]

video_id = extract_video_id(urls, API_KEY)
channel_ids_ = channel_ids(video_id)
playlist_id = get_uploads_playlist_id(channel_ids_)
result = videos_from_playlist(playlist_id)
comments = comments_from_channels(result)

# Save the year dataframes to an Excel file
# youtube = os.makedirs('youtube')
for video in video_id:
    save_dataframes_to_excel(clean_excel_string(comments), os.path.join('youtube', f'{video}.xlsx'))




# If modifying these SCOPES, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']

def authenticate_google_drive():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials, prompt the user to log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('drive', 'v3', credentials=creds)

def upload_file_to_google_drive(file_path, file_name):
    # Authenticate to Google Drive
    service = authenticate_google_drive()

    # File metadata
    file_metadata = {
        'name': file_name
    }

    # Upload the file
    media = MediaFileUpload(file_path, mimetype='application/vnd.google-apps.document')

    # Perform the file upload
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"File uploaded successfully with file ID: {file.get('id')}")

if __name__ == '__main__':
    file_path = 'youtube/'  # Replace with your local file path
    file_name = 'Data'  # Replace with the name you want for the file in Google Drive
    upload_file_to_google_drive(file_path, file_name)
