TARGET_SUBJECT = "Training Exercise"


def subject_matches(subject: str) -> bool:
    if subject is None:
        return False
    s = subject.strip()
    return s == TARGET_SUBJECT or s.endswith(TARGET_SUBJECT)

