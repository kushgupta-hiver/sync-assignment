from typing import Dict, Optional, List
from src.utils.retry import exponential_backoff_retry, is_retryable_googleapi_error


def register_watch(gmail, topic_name: str, label_ids: Optional[List[str]] = None) -> Dict:
    body = {
        "topicName": topic_name,
        # labelIds optional; omit to watch all labels
    }
    if label_ids:
        body["labelIds"] = label_ids

    def _call():
        return gmail.users().watch(userId="me", body=body).execute()

    return exponential_backoff_retry(_call, is_retryable=is_retryable_googleapi_error)


def stop_watch(gmail) -> None:
    def _call():
        return gmail.users().stop(userId="me").execute()

    exponential_backoff_retry(_call, is_retryable=is_retryable_googleapi_error)

