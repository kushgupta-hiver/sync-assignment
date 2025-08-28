import base64
import json
import os
from typing import Dict, Optional

from dotenv import load_dotenv

import src.main as main_module


class FakeMessage:
    def __init__(self, data: bytes, attributes: Optional[dict] = None):
        self.data = data
        self.attributes = attributes or {}

    def ack(self):
        pass

    def nack(self):
        pass


class _Exec:
    def __init__(self, fn):
        self._fn = fn

    def execute(self):
        return self._fn()


class _MessagesAPI:
    def __init__(self, user_store: Dict):
        self.store = user_store

    def get(self, userId: str, id: str, format: str = "metadata", metadataHeaders=None):
        def _run():
            if id == "src-msg-1":
                if format == "metadata":
                    return {
                        "id": id,
                        "historyId": "100",
                        "payload": {
                            "headers": [
                                {"name": "Subject", "value": "Training Exercise"},
                                {"name": "Message-Id", "value": "<mid-1>"},
                            ]
                        },
                    }
                if format == "raw":
                    raw = base64.urlsafe_b64encode(b"raw-bytes").decode("ascii")
                    return {"raw": raw}
            # fallback minimal
            return {"id": id, "payload": {"headers": []}}

        return _Exec(_run)

    def list(self, userId: str, q: str = "", maxResults: int = 1):
        def _run():
            # Very small rfc822msgid support
            if q.startswith("rfc822msgid:"):
                rid = q.split(":", 1)[1]
                present = rid in self.store.get("rfc_by_id", {})
                if present:
                    mid = self.store["rfc_by_id"][rid]
                    return {"resultSizeEstimate": 1, "messages": [{"id": mid, "threadId": "tgt-thread-1"}]}
                return {"resultSizeEstimate": 0}
            # default empty
            return {"resultSizeEstimate": 0}

        return _Exec(_run)

    def insert(self, userId: str, body: Dict):
        def _run():
            # record that we now have this rfc822 id for this user
            rid = "<mid-1>"
            self.store.setdefault("rfc_by_id", {})[rid] = "tgt-msg-1"
            return {"id": "tgt-msg-1", "threadId": "tgt-thread-1"}

        return _Exec(_run)

    def modify(self, userId: str, id: str, body: Dict):
        def _run():
            return {}

        return _Exec(_run)


class _LabelsAPI:
    def __init__(self, user_store: Dict):
        self.store = user_store

    def list(self, userId: str):
        def _run():
            labels = self.store.get("labels", [])
            return {"labels": labels}

        return _Exec(_run)

    def create(self, userId: str, body: Dict):
        def _run():
            lid = "LBL1"
            entry = {"id": lid, "name": body.get("name", "Training Exercise")}
            self.store.setdefault("labels", []).append(entry)
            return entry

        return _Exec(_run)


class _ThreadsAPI:
    def __init__(self, user_store: Dict):
        self.store = user_store

    def modify(self, userId: str, id: str, body: Dict):
        def _run():
            return {}

        return _Exec(_run)


class _HistoryAPI:
    def __init__(self, user_store: Dict):
        self.store = user_store

    def list(self, userId: str, startHistoryId: str):
        def _run():
            # Always return one new message for simplicity
            return {"history": [{"id": "101", "messagesAdded": [{"message": {"id": "src-msg-1"}}]}]}

        return _Exec(_run)


class _UsersAPI:
    def __init__(self, user_store: Dict):
        self.store = user_store

    def messages(self):
        return _MessagesAPI(self.store)

    def labels(self):
        return _LabelsAPI(self.store)

    def threads(self):
        return _ThreadsAPI(self.store)

    def history(self):
        return _HistoryAPI(self.store)

    def watch(self, userId: str, body: Dict):
        return _Exec(lambda: {"historyId": "100"})

    def stop(self, userId: str):
        return _Exec(lambda: {})


class StubGmail:
    def __init__(self, user_email: str, backing_store: Dict[str, Dict]):
        self.user_email = user_email
        self.backing_store = backing_store

    def users(self):
        user_store = self.backing_store.setdefault(self.user_email, {})
        return _UsersAPI(user_store)


def _stub_gmail_client_for(backing_store: Dict[str, Dict]):
    def factory(user_email: str, _sa_path: str):
        return StubGmail(user_email, backing_store)

    return factory


def main():
    load_dotenv()
    # Force memory KV and a small team for the dry run
    os.environ["STORE_BACKEND"] = "memory"
    os.environ.setdefault("TEAM_USERS", "user@example.com,B@example.com")

    # Monkey-patch gmail_client_for in main module to our stub
    backing_store: Dict[str, Dict] = {}
    main_module.gmail_client_for = _stub_gmail_client_for(backing_store)

    payload = {
        "source": "gmail",
        "emailAddress": "user@example.com",
        "historyId": "123456",
        "eventTime": "2025-08-26T10:11:12Z",
        "projectId": "dev-project",
    }
    msg = FakeMessage(json.dumps(payload).encode("utf-8"), {"version": "1"})
    main_module.handle_pubsub_message(msg)
    print("Dry run completed successfully.")


if __name__ == "__main__":
    main()


