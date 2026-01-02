"""
Google Drive integration module for scanning WAV files.

This module provides functionality to:
1. Authenticate with Google Drive
2. Scan folders recursively for WAV files
3. Download files temporarily if needed for processing
"""

import os
import io
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import pandas as pd

# Scopes required for Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


class DriveFile:
    """Represents a file in Google Drive with path-like interface."""
    
    def __init__(self, file_id: str, name: str, parents: List[str], mime_type: str):
        self.file_id = file_id
        self.name = name
        self.parents = parents
        self.mime_type = mime_type
        self._path_str = None
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return f"DriveFile(id={self.file_id}, name={self.name})"
    
    def set_path(self, path_str: str):
        """Set the full path string for this file."""
        self._path_str = path_str
    
    @property
    def path_str(self) -> str:
        return self._path_str or self.name


class GoogleDriveScanner:
    """Scanner for Google Drive folders."""
    
    def __init__(self, credentials_path: str = "credentials.json", token_path: str = "token.json"):
        """
        Initialize Google Drive scanner.
        
        Args:
            credentials_path: Path to OAuth2 credentials JSON file
            token_path: Path to store/load authentication token
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Drive API."""
        creds = None
        
        # Load existing token if available
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.credentials_path}\n\n"
                        "Please download credentials.json from Google Cloud Console.\n"
                        "See GOOGLE_DRIVE_SETUP.md for detailed step-by-step instructions.\n\n"
                        "Quick steps:\n"
                        "1. Go to https://console.cloud.google.com/\n"
                        "2. Create a project (or select existing)\n"
                        "3. Enable Google Drive API\n"
                        "4. Create OAuth 2.0 credentials (Desktop app)\n"
                        "5. Download as credentials.json and place it in the project folder"
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('drive', 'v3', credentials=creds)
        print("Successfully authenticated with Google Drive")
    
    def find_folder_by_name(self, folder_name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """
        Find a folder by name in Google Drive.
        
        Args:
            folder_name: Name of the folder to find
            parent_id: Optional parent folder ID to search within
            
        Returns:
            Folder ID if found, None otherwise
        """
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        
        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        items = results.get('files', [])
        
        if items:
            return items[0]['id']
        return None
    
    def get_folder_id_from_url(self, url: str) -> Optional[str]:
        """
        Extract folder ID from Google Drive URL.
        
        Args:
            url: Google Drive folder URL
            
        Returns:
            Folder ID if found in URL
        """
        # Handle different URL formats
        if '/folders/' in url:
            folder_id = url.split('/folders/')[1].split('/')[0].split('?')[0]
            return folder_id
        elif 'id=' in url:
            folder_id = url.split('id=')[1].split('&')[0]
            return folder_id
        return None
    
    def list_files_in_folder(self, folder_id: str, mime_type: Optional[str] = None) -> List[Dict]:
        """
        List all files in a folder.
        
        Args:
            folder_id: Google Drive folder ID
            mime_type: Optional MIME type filter (e.g., 'audio/wav')
            
        Returns:
            List of file metadata dictionaries
        """
        query = f"'{folder_id}' in parents and trashed=false"
        if mime_type:
            query += f" and mimeType='{mime_type}'"
        
        files = []
        page_token = None
        
        while True:
            results = self.service.files().list(
                q=query,
                fields="nextPageToken, files(id, name, mimeType, parents)",
                pageToken=page_token
            ).execute()
            
            items = results.get('files', [])
            files.extend(items)
            
            page_token = results.get('nextPageToken')
            if not page_token:
                break
        
        return files
    
    def build_path_for_file(self, file_id: str, file_name: str, root_folder_id: str) -> str:
        """
        Build full path string for a file by traversing up the folder hierarchy.
        
        Args:
            file_id: File ID
            file_name: File name
            root_folder_id: Root folder ID to stop at
            
        Returns:
            Full path string
        """
        path_parts = [file_name]
        current_id = file_id
        
        # Get file metadata to find parents
        try:
            file_meta = self.service.files().get(fileId=current_id, fields="parents, name").execute()
            parents = file_meta.get('parents', [])
        except:
            return file_name
        
        # Traverse up the folder tree
        visited = set()
        while parents and current_id != root_folder_id:
            parent_id = parents[0]
            if parent_id in visited or parent_id == root_folder_id:
                break
            visited.add(parent_id)
            
            try:
                parent_meta = self.service.files().get(fileId=parent_id, fields="name, parents").execute()
                parent_name = parent_meta.get('name')
                path_parts.insert(0, parent_name)
                parents = parent_meta.get('parents', [])
                current_id = parent_id
            except:
                break
        
        return '/'.join(path_parts)
    
    def find_all_wav_files(self, root_folder_id: str) -> List[DriveFile]:
        """
        Recursively find all WAV files in a folder and its subfolders.
        
        Args:
            root_folder_id: Root folder ID to start scanning from
            
        Returns:
            List of DriveFile objects representing WAV files
        """
        wav_files = []
        folders_to_process = [(root_folder_id, "")]
        
        print(f"Scanning Google Drive folder (ID: {root_folder_id})...")
        
        while folders_to_process:
            folder_id, parent_path = folders_to_process.pop(0)
            
            # List all items in current folder
            try:
                items = self.list_files_in_folder(folder_id)
            except Exception as e:
                print(f"Error listing folder {folder_id}: {e}")
                continue
            
            for item in items:
                item_name = item['name']
                item_id = item['id']
                item_mime = item.get('mimeType', '')
                current_path = f"{parent_path}/{item_name}" if parent_path else item_name
                
                # Check if it's a folder
                if item_mime == 'application/vnd.google-apps.folder':
                    folders_to_process.append((item_id, current_path))
                # Check if it's a WAV file
                elif item_name.lower().endswith(('.wav', '.wave')):
                    drive_file = DriveFile(
                        file_id=item_id,
                        name=item_name,
                        parents=item.get('parents', []),
                        mime_type=item_mime
                    )
                    drive_file.set_path(current_path)
                    wav_files.append(drive_file)
            
            if len(folders_to_process) % 10 == 0 and folders_to_process:
                print(f"  Processed folders, found {len(wav_files)} WAV files so far...")
        
        print(f"Found {len(wav_files)} WAV files total")
        return wav_files
    
    def find_year_folders(self, root_folder_id: str) -> Dict[str, str]:
        """
        Find all year folders (e.g., 2015, 2018, 2022) in the root folder.
        Returns a dictionary mapping year to folder ID.
        
        Args:
            root_folder_id: Root folder ID to start scanning from
            
        Returns:
            Dictionary mapping year (as string) to folder ID
        """
        year_folders = {}
        
        # Find all folders that are direct children of root
        try:
            folders = self.list_files_in_folder(root_folder_id)
        except Exception as e:
            print(f"Error listing root folder: {e}")
            return year_folders
        
        # For each folder, check if it's a year folder
        for folder in folders:
            if folder.get('mimeType') != 'application/vnd.google-apps.folder':
                continue
            
            folder_name = folder['name']
            folder_id = folder['id']
            
            # Check if folder name is a year (4 digits)
            if folder_name.isdigit() and len(folder_name) == 4:
                year = folder_name
                year_folders[year] = folder_id
        
        return year_folders
    
    def find_excel_files_in_year_folders(self, root_folder_id: str) -> Dict[str, str]:
        """
        Find Excel files in year folders (e.g., 2015, 2018, 2022).
        Returns a dictionary mapping year to Excel file ID.
        
        Args:
            root_folder_id: Root folder ID to start scanning from
            
        Returns:
            Dictionary mapping year (as string) to Excel file ID
        """
        year_excel_files = {}
        
        # Get all year folders
        year_folders = self.find_year_folders(root_folder_id)
        
        # For each year folder, look for Excel files
        for year, folder_id in year_folders.items():
            # Look for Excel files in this year folder
            try:
                files_in_year = self.list_files_in_folder(folder_id)
                for file_item in files_in_year:
                    file_name = file_item['name']
                    file_mime = file_item.get('mimeType', '')
                    
                    # Check if it's an Excel file
                    if (file_name.lower().endswith(('.xlsx', '.xls')) or 
                        'spreadsheet' in file_mime.lower() or
                        file_mime == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'):
                        year_excel_files[year] = file_item['id']
                        print(f"  Found Excel file for year {year}: {file_name}")
                        break  # Take first Excel file found in year folder
            except Exception as e:
                print(f"  Warning: Could not search for Excel files in year folder {year}: {e}")
        
        return year_excel_files
    
    def find_all_wav_files_in_year_folder(self, year_folder_id: str, year: str) -> List[DriveFile]:
        """
        Recursively find all WAV files in a specific year folder.
        
        Args:
            year_folder_id: Google Drive folder ID for the year
            year: Year as string (for path construction)
            
        Returns:
            List of DriveFile objects
        """
        wav_files = []
        folders_to_process = [(year_folder_id, year)]
        
        while folders_to_process:
            folder_id, parent_path = folders_to_process.pop(0)
            
            try:
                items = self.list_files_in_folder(folder_id)
            except Exception as e:
                print(f"Error listing folder {folder_id}: {e}")
                continue
            
            for item in items:
                item_name = item['name']
                item_id = item['id']
                item_mime = item.get('mimeType', '')
                current_path = f"{parent_path}/{item_name}" if parent_path else item_name
                
                if item_mime == 'application/vnd.google-apps.folder':
                    folders_to_process.append((item_id, current_path))
                elif (item_name.lower().endswith(('.wav', '.wave', '.WAV', '.WAVE')) or 
                      item_mime in ('audio/wav', 'audio/x-wav', 'audio/wave', 'audio/vnd.wave', 'audio/mpeg')):
                    drive_file = DriveFile(
                        file_id=item_id,
                        name=item_name,
                        parents=item.get('parents', []),
                        mime_type=item_mime
                    )
                    drive_file.set_path(current_path)
                    wav_files.append(drive_file)
        
        return wav_files
    
    def download_file(self, file_id: str, output_path: Path) -> bool:
        """
        Download a file from Google Drive to local path.
        
        Args:
            file_id: Google Drive file ID
            output_path: Local path to save the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(fh.getvalue())
            
            return True
        except Exception as e:
            print(f"Error downloading file {file_id}: {e}")
            return False
    
    def download_excel_file(self, file_id: str) -> Optional[pd.DataFrame]:
        """
        Download and read an Excel file from Google Drive.
        
        Args:
            file_id: Google Drive file ID
            
        Returns:
            DataFrame if successful, None otherwise
        """
        try:
            request = self.service.files().export_media(
                fileId=file_id,
                mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            fh.seek(0)
            df = pd.read_excel(fh, engine='openpyxl')
            return df
        except Exception as e:
            # Try direct download if export fails
            try:
                request = self.service.files().get_media(fileId=file_id)
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                
                fh.seek(0)
                df = pd.read_excel(fh, engine='openpyxl')
                return df
            except Exception as e2:
                print(f"Error reading Excel file {file_id}: {e2}")
                return None

