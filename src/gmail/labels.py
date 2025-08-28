from typing import Dict
from src.utils.retry import exponential_backoff_retry, is_retryable_googleapi_error


_CACHE: Dict[str, str] = {}


def ensure_label(gmail, label_name: str) -> str:
    if label_name in _CACHE:
        return _CACHE[label_name]
    def _list():
        return gmail.users().labels().list(userId="me").execute()

    labels = exponential_backoff_retry(_list, is_retryable=is_retryable_googleapi_error).get("labels", [])
    for lb in labels:
        if lb.get("name") == label_name:
            _CACHE[label_name] = lb["id"]
            return lb["id"]
    body = {"name": label_name, "labelListVisibility": "labelShow", "messageListVisibility": "show"}
    def _create():
        return gmail.users().labels().create(userId="me", body=body).execute()

    res = exponential_backoff_retry(_create, is_retryable=is_retryable_googleapi_error)
    _CACHE[label_name] = res["id"]
    return res["id"]


def label_message(gmail, msg_id: str, label_id: str):
    def _call():
        return gmail.users().messages().modify(userId="me", id=msg_id, body={"addLabelIds": [label_id]}).execute()

    exponential_backoff_retry(_call, is_retryable=is_retryable_googleapi_error)


def label_thread(gmail, thread_id: str, label_id: str):
    def _call():
        return gmail.users().threads().modify(userId="me", id=thread_id, body={"addLabelIds": [label_id]}).execute()

    exponential_backoff_retry(_call, is_retryable=is_retryable_googleapi_error)

