"""Extract a personal writing-style fingerprint from Obsidian chat exports.

Input:  vault folder with `## You` / `## Assistant` / `## Claude` blocks
        (Obsidian "export chat to note" format).
Output: style_profile.json (stats) + report.txt (readable summary).

Pure stdlib. No ML.
"""
import os, re, json, sys
from collections import Counter
from statistics import mean, median, stdev

sys.stdout.reconfigure(encoding="utf-8")

VAULT = r"W:\2nd brain\2nd brain - Clean"
OUT_JSON = r"W:\voice-match\style_profile.json"
OUT_REPORT = r"W:\voice-match\report.txt"

USER_HDR = {"you"}
AI_HDR = {"assistant", "claude", "chatgpt", "gpt", "gemini", "copilot", "ai"}

HDR_RE = re.compile(r"^#{2,4}\s+(.+?)\s*$")
EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\U0001F680-\U0001F6FF\U00002700-\U000027BF"
    "\U00002600-\U000026FF\U00002B00-\U00002BFF\U0001F900-\U0001F9FF"
    "\U00002190-\U000021FF\U00002300-\U000023FF\U000024C2-\U000024C2"
    "\U0000FE0F\u200d\u2600-\u27BF\U0001FA70-\U0001FAFF]+")

# --- casual-speak / informal tokens (per-100-word signals) ---
INFORMAL = {
    "bc", "bcz", "cuz", "cos", "coz", "yk", "idk", "tbh", "ig", "nvm",
    "tho", "rly", "rlly", "rrly", "smth", "smt", "smtn", "sumt", "sumth",
    "u", "ur", "r", "n", "2", "4", "pls", "plz", "omw", "lol", "lmao", "lmk",
    "ik", "iirc", "afaik", "fyi", "btw", "im", "dont", "cant", "wont", "didnt",
    "isnt", "wasnt", "wouldnt", "couldnt", "shouldnt", "doesnt", "havent",
    "hasnt", "aint", "gonna", "wanna", "gotta", "kinda", "sorta", "gimme",
    "lemme", "yea", "yeah", "ya", "nah", "kk", "ok", "k", "dunno", "probs",
    "defo", "def", "prolly", "prob", "rn", "btw", "acc", "abt", "about2",
    "nvr", "sum", "sumthin", "srsly", "coz", "bcuz", "bro", "dude", "hmm",
    "huh", "oh", "okay", "idm", "idek", "wbu", "hbu", "gn", "g2g", "afk",
    "js", "jst", "ts", "dat", "dis", "wat", "wht", "cmon", "ima", "imma",
}
CONTRACTIONS = {
    "i'm", "i've", "i'd", "i'll", "you're", "you've", "you'd", "you'll",
    "he's", "she's", "it's", "that's", "there's", "here's", "what's",
    "who's", "where's", "when's", "why's", "don't", "can't", "won't",
    "wouldn't", "couldn't", "shouldn't", "aren't", "isn't", "wasn't",
    "weren't", "haven't", "hasn't", "hadn't", "doesn't", "didn't", "let's",
    "we're", "we've", "we'd", "we'll", "they're", "they've", "they'd",
    "they'll", "i'm", "gonna", "wanna", "gotta", "im", "dont", "cant",
    "wont", "didnt", "isnt", "wasnt", "wouldnt", "couldnt", "shouldnt",
    "doesnt", "havent", "hasnt", "let's", "ain't",
}
FILLERS = {"like", "just", "basically", "actually", "honestly", "literally",
           "kinda", "sorta", "probs", "probably", "tbh", "yk", "ig", "idk",
           "yeah", "yea", "ok", "okay", "so", "well", "anyway", "anyways",
           "honestly", "tbh"}
FIRST_PERSON = {"i", "im", "i'm", "i've", "i'd", "i'll", "my", "me", "mine",
                "myself", "we", "our", "ours", "we're", "we've"}

SENT_SPLIT = re.compile(r"[.!?](?:\s+|$)")
CODE_FENCE = re.compile(r"```.*?```", re.S)
INLINE_CODE = re.compile(r"`[^`]+`")
URL = re.compile(r"https?://\S+")
SLASH_CMD = re.compile(r"^\s*(?:/|>)\s*\S+")


def clean_block(text):
    text = CODE_FENCE.sub(" ", text)
    text = INLINE_CODE.sub(" ", text)
    text = URL.sub(" ", text)
    text = EMOJI.sub(" ", text)
    text = re.sub(r"^(?:\*N messages? (?:merged|imported|converted)[^\n]*|#.*|##.*)$", "", text, flags=re.M)
    lines = []
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln or re.match(r"^-{3,}$", ln):
            continue
        if SLASH_CMD.match(ln) and len(ln) < 60:
            continue
        lines.append(ln)
    return "\n".join(lines)


def split_sentences(text):
    """Split on sentence punctuation/newlines. Returns list of sentence strings."""
    parts = []
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        bits = [b.strip() for b in SENT_SPLIT.split(ln) if b.strip()]
        if not bits:
            parts.append(ln)
        else:
            parts.extend(bits)
    return parts


def tokens(text):
    return re.findall(r"[A-Za-z']+", text.lower())


def pick_files(vault):
    for root, dirs, files in os.walk(vault):
        if ".obsidian" in root:
            continue
        for f in files:
            if f.lower().endswith(".md"):
                yield os.path.join(root, f)


def parse_blocks(fp):
    """Yield (speaker, text) pairs with formatting stripped."""
    with open(fp, encoding="utf-8", errors="replace") as fh:
        lines = fh.readlines()
    cur = None
    buf = []
    for ln in lines:
        m = HDR_RE.match(ln)
        if m:
            name = m.group(1).strip().lower()
            if name in USER_HDR or name in AI_HDR:
                if cur:
                    yield cur, "\n".join(buf)
                cur = "user" if name in USER_HDR else "ai"
                buf = []
                continue
        if cur is not None:
            buf.append(ln)
    if cur and buf:
        yield cur, "\n".join(buf)


def block_stats(blocks):
    stats = {
        "n_messages": 0, "words_total": 0,
        "sentence_lens": [], "runon": 0, "fragments": 0,
        "lowercase_starts": 0, "n_sentences_punct": 0,
        "informal": 0, "contractions": 0, "fillers": 0, "first_person": 0,
        "informal_TYPES": Counter(), "wordfreq": Counter(),
        "bigrams": Counter(), "msg_lens": [],
    }
    for speaker, raw in blocks:
        if speaker != "user":
            continue
        text = clean_block(raw)
        if not text.strip():
            continue
        stats["n_messages"] += 1
        toks = tokens(text)
        wc = len(toks)
        stats["words_total"] += wc
        stats["msg_lens"].append(wc)
        stats["wordfreq"].update(toks)
        stats["bigrams"].update(zip(toks, toks[1:]))
        for t in toks:
            if t in INFORMAL:
                stats["informal"] += 1
                stats["informal_TYPES"][t] += 1
            if t in FILLERS:
                stats["fillers"] += 1
            if t in FIRST_PERSON:
                stats["first_person"] += 1
            if t in CONTRACTIONS:
                stats["contractions"] += 1
        for ln in text.splitlines():
            if not ln.strip():
                continue
            lnstripped = ln.lstrip()
            if re.match(r"^[\-*•\d.)]", lnstripped):
                stats["fragments"] += 1
                continue
        sentences = split_sentences(text)
        for s in sentences:
            sw = len(tokens(s))
            if sw >= 1:
                stats["sentence_lens"].append(sw)
                if s[0].isalpha() and s[0].islower():
                    stats["lowercase_starts"] += 1
                    stats["n_sentences_punct"] += 1
        # run-on check: any piece > 140 chars with no sentence punctuation
        for ln in text.splitlines():
            ln = ln.strip()
            if len(ln) > 140 and not re.search(r"[.!?]", ln):
                stats["runon"] += 1
    return stats


def rates(stats):
    w = max(stats["words_total"], 1)
    n_sent = max(len(stats["sentence_lens"]), 1)
    sl = sorted(stats["sentence_lens"])
    def pct(p):
        return sl[min(int(p * len(sl)), len(sl) - 1)]
    short = sum(1 for x in sl if x <= 8) / n_sent
    long = sum(1 for x in sl if x >= 24) / n_sent
    return {
        "word_count": stats["words_total"],
        "n_messages": stats["n_messages"],
        "sentence_length": {
            "mean": round(mean(sl), 2),
            "median": round(median(sl), 2),
            "std": round(stdev(sl), 2) if len(sl) > 1 else 0.0,
            "p10": pct(0.10), "p25": pct(0.25), "p75": pct(0.75), "p90": pct(0.90),
        },
        "short_rate": round(short, 3),
        "long_rate": round(long, 3),
        "avg_msg_len": round(mean(stats["msg_lens"]), 1) if stats["msg_lens"] else 0.0,
        "runon_per_100w": round(stats["runon"] / w * 100, 2),
        "fragment_rate": round(stats["fragments"] / max(stats["n_messages"], 1), 2),
        "lowercase_start_rate": round(stats["lowercase_starts"] / max(stats["n_sentences_punct"], 1), 2),
        "informal_per_100w": round(stats["informal"] / w * 100, 2),
        "contractions_per_100w": round(stats["contractions"] / w * 100, 2),
        "fillers_per_100w": round(stats["fillers"] / w * 100, 2),
        "first_person_per_100w": round(stats["first_person"] / w * 100, 2),
        "avg_word_len": round(sum(len(t) * c for t, c in stats["wordfreq"].items()) / max(sum(stats["wordfreq"].values()), 1), 2),
        "top_informal": dict(stats["informal_TYPES"].most_common(30)),
        "top_informal_types": {w: c for w, c in
                               stats["informal_TYPES"].most_common(15)},
    }


def text_features(raw_text):
    """Compute the same `casual` feature dict for arbitrary text (no headers)."""
    cleaned = clean_block(raw_text)
    s = block_stats([("user", cleaned)])
    if s["words_total"] == 0:
        return None
    return rates(s)


def main():
    blocks = []
    for fp in pick_files(VAULT):
        blocks.extend(parse_blocks(fp))
    usr = [b for b in blocks if b[0] == "user"]
    seen = set()
    dedup = []
    for _, t in usr:
        key = re.sub(r"\s+", " ", t.lower()).strip()
        if key not in seen:
            seen.add(key)
            dedup.append((_, t))
    print(f"raw user blocks: {len(usr)}  after dedup: {len(dedup)}")
    s = block_stats(dedup)
    prof = {"meta": {
        "name": "voice-match profile",
        "sources": [VAULT, "chat exports"],
        "n_messages": s["n_messages"],
        "n_words": s["words_total"],
        "registers": {
            "casual": "your raw fingerprint (chars/short-form)",
            "semi_formal": "full sentences, mild contractions, no slang",
            "formal": "clean prose — calibrated later from real samples",
        },
    }, "casual": rates(s)}
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(prof, f, indent=2, ensure_ascii=False)
    with open(OUT_REPORT, "w", encoding="utf-8") as f:
        f.write("voice-match profile report\n===========================\n")
        f.write(f"messages: {s['n_messages']}  words: {s['words_total']}\n\n")
        for k, v in prof["casual"].items():
            f.write(f"{k}: {v}\n")
    print("wrote", OUT_JSON)
    print("wrote", OUT_REPORT)


if __name__ == "__main__":
    main()