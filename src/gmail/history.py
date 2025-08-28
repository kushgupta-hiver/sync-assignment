from typing import List, Tuple, Optional


def list_new_message_ids(gmail, start_history_id: str) -> List[str]:
    """Return message IDs from MessagesAdded since start_history_id.

    Caller should handle 404 (historyId too old) by triggering a full resync.
    """
    message_ids: List[str] = []
    page_token = None
    while True:
        req = gmail.users().history().list(userId="me", startHistoryId=start_history_id)
        if page_token:
            req = req.pageToken(page_token)
        resp = req.execute()
        for hist in resp.get("history", []):
            for added in hist.get("messagesAdded", []):
                msg = added.get("message", {})
                mid = msg.get("id")
                if mid:
                    message_ids.append(mid)
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return message_ids


def list_new_message_ids_and_last(gmail, start_history_id: str) -> Tuple[List[str], Optional[str]]:
    """Return (message IDs, last historyId seen) since start_history_id.

    last historyId is the maximum history record id observed in the scan.
    """
    message_ids: List[str] = []
    last_history_id: Optional[int] = None
    page_token = None
    while True:
        req = gmail.users().history().list(userId="me", startHistoryId=start_history_id)
        if page_token:
            req = req.pageToken(page_token)
        resp = req.execute()
        for hist in resp.get("history", []):
            try:
                hid = int(hist.get("id"))
                last_history_id = hid if last_history_id is None else max(last_history_id, hid)
            except Exception:
                pass
            for added in hist.get("messagesAdded", []):
                msg = added.get("message", {})
                mid = msg.get("id")
                if mid:
                    message_ids.append(mid)
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return message_ids, (str(last_history_id) if last_history_id is not None else None)

