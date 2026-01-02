# Google Drive Setup Guide - Step by Step

## What is credentials.json?

This is a file that contains your authentication details for Google Drive API. Google requires this to allow the script to access your files.

## Detailed Instructions

### Step 1: Create a Project in Google Cloud Console

1. Go to: https://console.cloud.google.com/
2. Sign in with your Google account
3. If you don't have a project:
   - Click "Select a project" at the top
   - Click "New Project"
   - Give the project a name (e.g., "Mouse USV Metadata")
   - Click "Create"
4. If you have a project - select it

### Step 2: Enable Google Drive API

1. In the left menu, click "APIs & Services" > "Library"
2. Search for "Google Drive API"
3. Click on "Google Drive API"
4. Click "Enable" (if it's not already enabled)

### Step 3: Create OAuth 2.0 Credentials

1. In the left menu, go to: "APIs & Services" > "Credentials"
2. Click "Create Credentials" at the top
3. Select "OAuth client ID"
4. If this is the first time:
   - You'll be asked to configure "OAuth consent screen"
   - Select "External" (or "Internal" if you have Google Workspace)
   - Click "Create"
   - Fill in the basic details:
     - App name: "Mouse USV Metadata Generator" (or any name)
     - User support email: Your email
     - Developer contact: Your email
   - Click "Save and Continue"
   - In "Scopes" - click "Save and Continue" (no need to add scopes)
   - In "Test users" - click "Save and Continue"
   - Click "Back to Dashboard"
5. Go back to "Credentials" > "Create Credentials" > "OAuth client ID"
6. Select "Desktop app" as Application type
7. Give it a name (e.g., "Metadata Generator Desktop")
8. Click "Create"

### Step 4: Download credentials.json

1. You'll see a window with Client ID and Client Secret
2. Click "Download JSON" (or copy the content)
3. Save the file as `credentials.json` in the project folder (where `generate_metadata.py` is located)

### Step 5: Add Test Users (IMPORTANT!)

**This step is required for others to use the script with your Google Drive folders:**

1. In the left menu, go to: "APIs & Services" > "OAuth consent screen"
2. Scroll down to the "Test users" section
3. Click "ADD USERS"
4. Add the email addresses of anyone who needs to access the Google Drive folders:
   - Add your own email (the one you'll use to run the script)
   - Add emails of other team members who will use the script
5. Click "ADD"
6. **Important:** Each person must be added as a test user, otherwise they'll get "Error 403: access_denied"

### Step 6: Initial Authentication

When you run the script for the first time:
1. It will open a browser
2. You'll be asked to sign in to your Google account (must be one of the test users)
3. You'll see a warning "Google hasn't verified this app" - this is normal, click "Advanced" > "Go to [project name] (unsafe)"
4. Click "Allow" to grant permissions
5. The script will create a `token.json` file - this will allow it to work without asking you again

**Note:** Each user needs to go through this authentication process once. After that, the `token.json` file allows automatic access.

## Sharing with Team Members

If you want others to use the script with your Google Drive folders:

1. **Share the credentials.json file:**
   - The `credentials.json` file can be shared with team members
   - They should place it in the project folder (same location as `generate_metadata.py`)
   - **Important:** Make sure they are added as Test Users (Step 5 above)

2. **Each person needs their own token.json:**
   - Each team member must run the script once to create their own `token.json`
   - The `token.json` file is user-specific and should NOT be shared
   - Each person will authenticate with their own Google account

3. **Folder access:**
   - Make sure the Google Drive folder is shared with all team members
   - They need at least "Viewer" access to the folder
   - Share the folder URL or Folder ID with them

4. **Running the script:**
   - Each person runs: `python generate_metadata.py --drive --drive-folder-url "YOUR_FOLDER_URL"`
   - They use the same `credentials.json` but create their own `token.json`

## Troubleshooting

### "Access blocked: This app's request is invalid"
- Make sure you created OAuth client ID of type "Desktop app"
- Make sure you downloaded the correct file

### "Redirect URI mismatch"
- Make sure you selected "Desktop app" and not "Web application"

### "The OAuth client was not found"
- Make sure you downloaded the correct file from the correct project

### File not saved
- Make sure the file is named exactly `credentials.json` (not `credentials.json.txt`)
- Make sure it's in the project folder (where `generate_metadata.py` is)

### "Error 403: access_denied" when someone else tries to use it
- Make sure the person is added as a Test User in Google Cloud Console (Step 5)
- Make sure they are using the same `credentials.json` file
- Make sure they have access to the Google Drive folder
- Each person must authenticate once to create their own `token.json`

## Security

⚠️ **Important:**
- Do not upload `credentials.json` to GitHub or public places
- If you did this by mistake, go to Google Cloud Console and delete the credentials and create new ones
- The `token.json` file is also sensitive - do not upload it

## Verification

After setting everything up, run:
```bash
python generate_metadata.py --drive --drive-folder-url "https://drive.google.com/drive/folders/YOUR_FOLDER_ID"
```

If everything works, you'll see: "Successfully authenticated with Google Drive"
