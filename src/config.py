import os
from dataclasses import dataclass
from typing import List


@dataclass
class Config:
    project_id: str = os.getenv("GCP_PROJECT_ID", "")
    topic: str = os.getenv("GCP_PUBSUB_TOPIC", "")
    subscription: str = os.getenv("GCP_PUBSUB_SUBSCRIPTION", "")
    dlq_topic: str = os.getenv("GCP_PUBSUB_DLQ_TOPIC", "")
    team_users: List[str] = None
    label_name: str = os.getenv("GMAIL_LABEL_NAME", "Training Exercise")
    store_backend: str = os.getenv("STORE_BACKEND", "firestore")
    firestore_collection_prefix: str = os.getenv("FIRESTORE_COLLECTION_PREFIX", "gts")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    google_application_credentials: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")

    pull_max_messages: int = int(os.getenv("PULL_MAX_MESSAGES", "50"))
    pull_concurrency: int = int(os.getenv("PULL_CONCURRENCY", "10"))
    ack_deadline_seconds: int = int(os.getenv("ACK_DEADLINE_SECONDS", "60"))
    max_delivery_attempts: int = int(os.getenv("MAX_DELIVERY_ATTEMPTS", "10"))

    def __post_init__(self):
        self.team_users = [u.strip() for u in os.getenv("TEAM_USERS", "").split(",") if u.strip()]

