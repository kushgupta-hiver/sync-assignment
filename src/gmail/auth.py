from google.oauth2 import service_account
from googleapiclient.discovery import build


SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.insert",
    "https://www.googleapis.com/auth/gmail.readonly",
]


def gmail_client_for(user_email: str, sa_path: str):
    creds = service_account.Credentials.from_service_account_file(sa_path, scopes=SCOPES)
    delegated = creds.with_subject(user_email)
    return build("gmail", "v1", credentials=delegated, cache_discovery=False)

