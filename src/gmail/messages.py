from base64 import urlsafe_b64decode, urlsafe_b64encode
from typing import Dict, Tuple, Optional, List
from src.utils.retry import exponential_backoff_retry, is_retryable_googleapi_error


def get_metadata(gmail, msg_id: str) -> Dict:
    def _call():
        return (
            gmail.users()
            .messages()
            .get(
                userId="me",
                id=msg_id,
                format="metadata",
                metadataHeaders=[
                    "Subject",
                    "Message-Id",
                    "References",
                    "In-Reply-To",
                    "From",
                    "To",
                    "Cc",
                ],
            )
            .execute()
        )

    return exponential_backoff_retry(_call, is_retryable=is_retryable_googleapi_error)


def get_raw(gmail, msg_id: str) -> bytes:
    def _call():
        return gmail.users().messages().get(userId="me", id=msg_id, format="raw").execute()

    res = exponential_backoff_retry(_call, is_retryable=is_retryable_googleapi_error)
    return urlsafe_b64decode(res["raw"])  # bytes of RFC822


def search_by_message_id(gmail, rfc822_msgid: str) -> bool:
    q = f"rfc822msgid:{rfc822_msgid}"

    def _call():
        return gmail.users().messages().list(userId="me", q=q, maxResults=1).execute()

    res = exponential_backoff_retry(_call, is_retryable=is_retryable_googleapi_error)
    return res.get("resultSizeEstimate", 0) > 0


def insert_raw(gmail, raw_bytes: bytes) -> Dict:
    body = {"raw": urlsafe_b64encode(raw_bytes).decode("ascii")}

    def _call():
        return gmail.users().messages().insert(userId="me", body=body).execute()

    return exponential_backoff_retry(_call, is_retryable=is_retryable_googleapi_error)


def find_message_by_rfc822(gmail, rfc822_msgid: str) -> Tuple[Optional[str], Optional[str]]:
    """Return (message_id, thread_id) for a message matching rfc822 Message-Id, if present."""
    q = f"rfc822msgid:{rfc822_msgid}"

    def _call():
        return gmail.users().messages().list(userId="me", q=q, maxResults=1).execute()

    res = exponential_backoff_retry(_call, is_retryable=is_retryable_googleapi_error)
    msgs = res.get("messages", []) or []
    if not msgs:
        return None, None
    m = msgs[0]
    return m.get("id"), m.get("threadId")


def search_subject_training_exercise(gmail) -> List[str]:
    """Return message ids for messages with subject matching Training Exercise flavor."""
    q = 'subject:"Training Exercise"'
    message_ids: List[str] = []
    page_token = None
    while True:
        def _call():
            req = gmail.users().messages().list(userId="me", q=q, maxResults=100)
            if page_token:
                req = req.pageToken(page_token)
            return req.execute()

        res = exponential_backoff_retry(_call, is_retryable=is_retryable_googleapi_error)
        for m in res.get("messages", []) or []:
            if m.get("id"):
                message_ids.append(m["id"])
        page_token = res.get("nextPageToken")
        if not page_token:
            break
    return message_ids


def get_latest_history_id(gmail) -> Optional[str]:
    """Best-effort: fetch the most recent message and return its historyId."""
    def _list():
        return gmail.users().messages().list(userId="me", maxResults=1).execute()

    res = exponential_backoff_retry(_list, is_retryable=is_retryable_googleapi_error)
    msgs = res.get("messages", []) or []
    if not msgs:
        return None
    mid = msgs[0].get("id")
    if not mid:
        return None

    def _get():
        return gmail.users().messages().get(userId="me", id=mid, format="metadata").execute()

    msg = exponential_backoff_retry(_get, is_retryable=is_retryable_googleapi_error)
    hid = msg.get("historyId")
    return str(hid) if hid is not None else None

