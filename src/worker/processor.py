from typing import List

from src.domain.rules import subject_matches
from src.gmail.messages import (
    get_metadata,
    get_raw,
    search_by_message_id,
    insert_raw,
    find_message_by_rfc822,
)
from src.gmail.labels import ensure_label, label_thread, label_message


class Processor:
    def __init__(self, cfg, kv, auth_factory):
        self.cfg = cfg
        self.kv = kv
        self.auth_factory = auth_factory

    def process_history_event(self, user_email: str, message_ids: List[str]):
        src_gmail = self.auth_factory(user_email)
        label_id_cache = {}

        for msg_id in message_ids:
            meta = get_metadata(src_gmail, msg_id)
            headers = {h["name"]: h["value"] for h in meta.get("payload", {}).get("headers", [])}
            subject = headers.get("Subject")
            if not subject_matches(subject):
                continue

            rfc822id = headers.get("Message-Id")
            if not rfc822id:
                continue

            raw_bytes = get_raw(src_gmail, msg_id)

            insert_results = {}

            # route to teammates
            for target in self.cfg.team_users:
                if target.lower() == user_email.lower():
                    continue
                tgt_gmail = self.auth_factory(target)
                processed_key = f"processed:{target}:{rfc822id}"
                if self.kv.get(processed_key):
                    continue
                if search_by_message_id(tgt_gmail, rfc822id):
                    # mark as processed to avoid repeated work next time
                    self.kv.set(processed_key, "1")
                    continue
                res = insert_raw(tgt_gmail, raw_bytes)
                insert_results[target] = res
                # mark processed for this target
                self.kv.set(processed_key, "1")

            # label all team threads
            for target in self.cfg.team_users:
                tgt_gmail = self.auth_factory(target)
                label_id = label_id_cache.get(target)
                if not label_id:
                    label_id = ensure_label(tgt_gmail, self.cfg.label_name)
                    label_id_cache[target] = label_id

                # Prefer thread-level if we have threadId
                res = insert_results.get(target)
                thread_id = res.get("threadId") if isinstance(res, dict) else None
                if thread_id:
                    label_thread(tgt_gmail, thread_id, label_id)
                else:
                    # If we inserted and got an id back, label that message.
                    msg_id = res.get("id") if isinstance(res, dict) else None
                    if msg_id:
                        label_message(tgt_gmail, msg_id, label_id)
                    else:
                        # We didn't insert (already present). Find it by rfc822 Message-Id and use thread-level.
                        found_msg_id, found_thread_id = find_message_by_rfc822(tgt_gmail, rfc822id)
                        if found_thread_id:
                            label_thread(tgt_gmail, found_thread_id, label_id)
                        elif found_msg_id:
                            label_message(tgt_gmail, found_msg_id, label_id)

