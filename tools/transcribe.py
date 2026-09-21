import base64
import json
import os
import sys
import urllib.request

URL = os.environ.get("VOICE_VL_URL", "http://localhost:11434/v1/chat/completions")
KEY = os.environ.get("VOICE_VL_KEY", "")
MODEL = os.environ.get("VOICE_VL_MODEL", "qwen2.5vl:7b")

SYSTEM = (
    "You transcribe handwritten notes to plain text. Read every word you can and "
    "transcribe it exactly as written, keeping line breaks as line breaks. Do NOT fix "
    "grammar, spelling, or fill in blanks on your own. If a word or phrase is too "
    "messy or damaged to read with confidence, write it anyway but wrap it as "
    "[unclear]. Never silently skip blurred or cut-off text."
)

PROMPT = "Transcribe this handwritten page. Emit only the transcribed text with the original line breaks."


def payload(image_b64):
    return {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                    },
                ],
            },
        ],
        "temperature": 0,
    }


def transcribe(image_b64):
    req = urllib.request.Request(
        URL,
        data=json.dumps(payload(image_b64)).encode(),
        headers={
            "Content-Type": "application/json",
            **({"Authorization": f"Bearer {KEY}"} if KEY else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.load(resp)
    return data["choices"][0]["message"]["content"]


def flag_report(entries):
    flagged = [e for e in entries if "[unclear" in e["text"]]
    if not flagged:
        print("no [unclear] flags across all images")
        return
    print(f"{len(flagged)} image(s) contain uncertain spans:")
    for e in flagged:
        n = e["text"].count("[unclear")
        print(f"  {os.path.basename(e['image'])}: {n} uncertain span(s)")


def main():
    if len(sys.argv) < 2:
        print("usage: transcribe.py <image-or-dir> [--dry-run] [--report]")
        sys.exit(1)
    target, rest = sys.argv[1], sys.argv[2:]
    dry, report = "--dry-run" in rest, "--report" in rest
    if os.path.isdir(target):
        imgs = sorted(
            f for f in os.listdir(target)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        )
    else:
        imgs = [target]
    if not imgs:
        print("no jpg/png images found")
        sys.exit(1)
    if dry:
        for f in imgs:
            size = os.path.getsize(f) if os.path.isabs(f) else os.path.getsize(
                os.path.join(target, f)
            )
            print(f"{f}  {size // 1024} KiB")
        print("dry-run only: no API calls made")
        return
    entries = []
    for f in imgs:
        path = f if os.path.isabs(f) else os.path.join(target, f)
        with open(path, "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode()
        text = transcribe(b64)
        out = os.path.splitext(path)[0] + ".txt"
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(text)
        entries.append({"image": path, "text": text})
        print(f"{os.path.basename(path)} -> {os.path.basename(out)} ({len(text.split())} words)")
    if report:
        flag_report(entries)


if __name__ == "__main__":
    main()