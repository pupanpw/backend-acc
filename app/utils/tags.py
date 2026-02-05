import re


def normalize_tag_name(name: str) -> str:
    return re.sub(r"\s+", " ", (name or "").strip())


def make_slug(name: str) -> str:
    return normalize_tag_name(name).lower()
