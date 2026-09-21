import os, re, sys, json
from collections import Counter, defaultdict

VAULT = r"W:\2nd brain\2nd brain - Clean"

SPEAKER_HEADER = re.compile(r"^#+\s*(.+?)\s*$")
KNOWN_USER = {"you", "user", "human", "me", "us"}
KNOWN_AI = {"assistant", "claude", "chatgpt", "gpt", "ai", "gemini",
            "copilot", "qwen", "llm", "bard", "grok", "mistral", "llama"}

def classify_header(name):
    n = name.lower().strip().lstrip("#").strip()
    # strip trailing markdown artifacts
    n = re.sub(r"[*_`#]+$", "", n).strip()
    if n in KNOWN_USER: return "user"
    if n in KNOWN_AI: return "ai"
    # maybe 'chatgpt 4', 'claude 3.5'
    base = n.split()[0] if n.split() else n
    if base in KNOWN_USER: return "user"
    if base in KNOWN_AI: return "ai"
    return None

def scan():
    md_files = []
    for root, dirs, files in os.walk(VAULT):
        if ".obsidian" in root: continue
        for f in files:
            if f.lower().endswith(".md"):
                md_files.append(os.path.join(root, f))
    print(f"total md files: {len(md_files)}")

    header_hist = Counter()
    block_hist = Counter()          # first speaker seen per file
    inline_user = Counter()         # files w/ inline 'You:' / 'User:' markers
    merged_artifacts = 0
    no_speaker_markers = 0
    user_block_files = 0
    ai_block_files = 0
    size_dist = []
    examples = defaultdict(list)

    for fp in md_files:
        try:
            with open(fp, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except Exception:
            continue
        size_dist.append(len(text))
        lines = text.splitlines()
        seen = []
        for ln in lines:
            m = SPEAKER_HEADER.match(ln)
            if m:
                cls = classify_header(m.group(1))
                header_hist[m.group(1).strip()] += 1
                if cls:
                    block_hist[cls] += 1
                    seen.append(cls)
        # inline markers
        if re.search(r"^\*\*?You:?\*\*|^\*\*?User:?\*\*|^\*\*?Me:?\*\*", text, re.M | re.I):
            inline_user[fp] += 1
        if re.search(r"\*?\d+ messages? (merged|imported|converted)", text, re.I):
            merged_artifacts += 1
        if re.search(r"\b(?:The user|The human)\b", text) and "assistant" not in [l.lower() for l in lines[:8]]:
            examples["ai_preamble"].append(os.path.basename(fp))
        if re.search(r"^## +You\b", text, re.M):
            user_block_files += 1
            if len(examples["user_block"]) < 8:
                examples["user_block"].append(os.path.relpath(fp, VAULT))
        if re.search(r"^## +(?:Assistant|Claude|ChatGPT|AI)\b", text, re.M):
            ai_block_files += 1
        if not seen and not re.search(r"^\*\*?You:?\*\*", text, re.M | re.I):
            no_speaker_markers += 1
            if len(examples["bare"]) < 12 and len(lines) < 60:
                examples["bare"].append(os.path.relpath(fp, VAULT))

    print("\nheader histogram (count - header):")
    for h, c in header_hist.most_common(25):
        print(f"  {c:5d}  {h}")
    print(f"\nfiles with >=1 USER block: {user_block_files}")
    print(f"files with >=1 AI block:   {ai_block_files}")
    print(f"files w/ inline User:/You: markers: {len(inline_user)}")
    print(f"files w/ 'N messages merged' artifact: {merged_artifacts}")
    print(f"files w/ no speaker markers at all: {no_speaker_markers}")
    print(f"\nuser_block examples:")
    for e in examples["user_block"]: print("  ", e)
    print(f"\nbare (no markers) examples:")
    for e in examples["bare"]: print("  ", e)
    print(f"\nai_preamble examples (AI paraphrasing user):")
    for e in examples["ai_preamble"][:8]: print("  ", e)

    small = [s for s in size_dist if s < 200]
    print(f"\nsize: files<200B (small/note files): {len(small)} / {len(size_dist)}")

if __name__ == "__main__":
    scan()