"""The bounded description scalar shared by repository-only catalog tooling."""
import json
import re

DESCRIPTION = re.compile(r"^description:([^\n]*(?:\n[ \t]+[^\n]*)*)", re.M)
MAX_DESCRIPTION = 250


def description(text):
    front = re.match(r"^---\n(.*?)\n---(?:\n|$)", text, re.S)
    match = DESCRIPTION.search(front.group(1)) if front else None
    if not match:
        raise ValueError("missing description scalar")
    raw = match.group(1).strip()
    if raw.startswith('"') and raw.endswith('"'):
        value = json.loads(raw)
    elif raw.startswith("'") and raw.endswith("'"):
        value = raw[1:-1].replace("''", "'")
    else:
        lines = raw.splitlines()
        if lines and lines[0] in (">", ">-", "|", "|-"):
            lines = lines[1:]
        value = " ".join(line.strip() for line in lines)
    if not isinstance(value, str) or not value.strip() or len(value) > MAX_DESCRIPTION:
        raise ValueError("description must contain 1–250 characters")
    return value


def replace_description(text, value):
    if not isinstance(value, str) or not value.strip() or len(value) > MAX_DESCRIPTION:
        raise ValueError("description must contain 1–250 characters")
    front = re.match(r"^---\n(.*?)\n---(?:\n|$)", text, re.S)
    if not front or not DESCRIPTION.search(front.group(1)):
        raise ValueError("missing description scalar")
    body = DESCRIPTION.sub(lambda _: "description: " + json.dumps(value, ensure_ascii=False), front.group(1), count=1)
    return "---\n" + body + "\n---\n" + text[front.end():]
