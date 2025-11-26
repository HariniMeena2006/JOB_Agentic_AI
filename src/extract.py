from __future__ import print_function
import base64
import os.path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def gmail_login():
    creds = None

    token_path = "credentials/token.json"
    cred_path = "credentials/credentials.json"

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(cred_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def get_latest_emails(service, max_results=10):
    results = service.users().messages().list(
        userId="me", maxResults=max_results
    ).execute()

    messages = results.get("messages", [])

    emails = []

    for msg in messages:
        msg_data = service.users().messages().get(
            userId="me", id=msg["id"]
        ).execute()

        payload = msg_data["payload"]
        headers = payload.get("headers", [])

        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
        date = next((h["value"] for h in headers if h["name"] == "Date"), "")

        # Extract body
        body = ""
        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain":
                    data = part["body"].get("data")
                    if data:
                        body = base64.urlsafe_b64decode(data).decode("utf-8")
        else:
            data = payload["body"].get("data")
            if data:
                body = base64.urlsafe_b64decode(data).decode("utf-8")

        emails.append({
            "subject": subject,
            "date": date,
            "body": body
        })

    return emails
