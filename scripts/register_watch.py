import os
from dotenv import load_dotenv
from src.config import Config
from src.gmail.auth import gmail_client_for
from src.gmail.watch import register_watch


def main():
    load_dotenv()
    cfg = Config()
    topic = f"projects/{cfg.project_id}/topics/{cfg.topic}"
    for user in cfg.team_users:
        gmail = gmail_client_for(user, cfg.google_application_credentials)
        res = register_watch(gmail, topic)
        print(user, res.get("historyId"))


if __name__ == "__main__":
    main()

