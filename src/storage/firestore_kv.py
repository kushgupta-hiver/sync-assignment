from typing import Optional

from google.cloud import firestore


class FirestoreKV:
    def __init__(self, project_id: str, collection_prefix: str = "gts"):
        self._client = firestore.Client(project=project_id)
        self._collection = f"{collection_prefix}_kv"

    def get(self, key: str) -> Optional[str]:
        doc_ref = self._client.collection(self._collection).document(key)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict() or {}
            return data.get("value")
        return None

    def set(self, key: str, value: str) -> None:
        doc_ref = self._client.collection(self._collection).document(key)
        doc_ref.set({"value": value}, merge=True)

