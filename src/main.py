import json
import logging
from typing import Any, Dict

from src.config import Config
from src.gmail.auth import gmail_client_for
from src.gmail.history import list_new_message_ids, list_new_message_ids_and_last
from src.gmail.messages import get_latest_history_id, search_subject_training_exercise
from src.storage.memory_kv import InMemoryKV
from src.storage.firestore_kv import FirestoreKV
from src.utils.logging import setup_logging
from src.worker.processor import Processor


def parse_pubsub_payload(data_bytes: bytes, attributes: Dict[str, str]) -> Dict[str, Any]:
    payload = json.loads(data_bytes.decode("utf-8"))
    version = attributes.get("version")
    if version is None:
        version = 1
    else:
        try:
            version = int(version)
        except ValueError:
            version = 1

    source = payload.get("source")
    if source != "gmail":
        logging.warning("Non-gmail source payload received; skipping")
        return {"action": "skip"}

    email = payload.get("emailAddress")
    hist = payload.get("historyId")
    if not email or not hist:
        logging.error("Invalid payload missing required fields; skipping")
        return {"action": "skip"}

    return {
        "action": "process",
        "emailAddress": email,
        "historyId": str(hist),
        "version": version,
    }


def build_auth_factory(cfg: Config):
    def factory(user_email: str):
        return gmail_client_for(user_email, cfg.google_application_credentials)

    return factory


def handle_pubsub_message(message):
    cfg = Config()
    setup_logging(cfg.log_level)

    kv = InMemoryKV() if cfg.store_backend == "memory" else FirestoreKV(cfg.project_id, cfg.firestore_collection_prefix)

    auth_factory = build_auth_factory(cfg)
    processor = Processor(cfg, kv, auth_factory)

    parsed = parse_pubsub_payload(message.data, dict(message.attributes or {}))
    if parsed.get("action") != "process":
        return

    user_email = parsed["emailAddress"]
    history_id = parsed["historyId"]
    # Prefer stored cursor if available (can be newer); otherwise use incoming
    stored_cursor = kv.get(f"history_cursor:{user_email}")
    if stored_cursor:
        history_id = stored_cursor
    gmail = auth_factory(user_email)
    try:
        message_ids, last_hid = list_new_message_ids_and_last(gmail, history_id)
    except Exception as exc:  # noqa: BLE001
        # Fallback resync path: subject query and reset cursor to latest
        message_ids = search_subject_training_exercise(gmail)
        last_hid = get_latest_history_id(gmail)
    processor.process_history_event(user_email, message_ids)
    # Persist last history cursor when available
    if last_hid:
        key = f"history_cursor:{user_email}"
        kv.set(key, str(last_hid))


if __name__ == "__main__":
    from src.gcp.pubsub import Subscriber

    cfg = Config()
    setup_logging(cfg.log_level)

    sub = Subscriber(cfg.project_id, cfg.subscription, handle_pubsub_message)
    sub.start()

