"""Trial-and-error voice checker: score any text against your style profile.

Usage:
  python score.py <file.txt>     score a text file
  cat file | python score.py     or score stdin
  python score.py --formal <f>   score against the formal register
  python score.py --selfcheck    validate profile vs held-out user/AI blocks
  python score.py --sample N     print N random user messages (see the voice)
"""
import os, sys, re, json, random
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import extract_profile as X

PROFILE = r"W:\voice-match\style_profile.json"

# feature: (profile key, weight, tolerance as fraction of profile value)
FEATURES = [
    ("sentence_length.mean", 3, 0.20),
    ("sentence_length.median", 2, 0.25),
    ("sentence_length.std", 2, 0.35),
    ("short_rate", 2, 0.30),
    ("long_rate", 1, 0.40),
    ("lowercase_start_rate", 3, 0.35),
    ("informal_per_100w", 3, 0.40),
    ("contractions_per_100w", 2, 0.40),
    ("fillers_per_100w", 1, 0.45),
    ("first_person_per_100w", 2, 0.40),
    ("avg_word_len", 1, 0.10),
]


def get_path(casual, key):
    cur = casual
    for k in key.split("."):
        cur = cur[k]
    return cur


def score_features(feats, register="casual"):
    with open(PROFILE, encoding="utf-8") as f:
        prof = json.load(f)
    refs = prof.get(register, prof["casual"])
    out = []
    totals = 0.0
    wsum = 0.0
    for key, w, tol in FEATURES:
        ref = get_path(refs, key)
        val = get_path(feats, key)
        if ref == 0:
            sim = 1.0 if abs(val - ref) < 1e-6 else max(0.0, 1.0 - abs(val - ref) / 2.0)
        else:
            err = abs(val - ref) / ref
            sim = 1.0 - min(1.0, err / tol)
        sim = max(0.0, min(1.0, sim))
        out.append((key, ref, val, round(sim * 100), w))
        totals += sim * w
        wsum += w
    return round(totals / wsum * 100), out


def score_text(text, register="casual"):
    c = X.text_features(text)
    if c is None:
        return None, None
    return score_features(c, register)


def main():
    args = sys.argv[1:]
    register = "casual"
    if "--formal" in args:
        register = "formal"
        args.remove("--formal")
    if not args or (args and args[0] in ("-h", "--help")):
        print(__doc__)
        return
    if args[0] == "--selfcheck":
        selfcheck()
        return
    if args[0] == "--sample":
        sample_user(int(args[1]) if len(args) > 1 else 10)
        return
    if args[0] == "-":
        text = sys.stdin.read()
    else:
        with open(args[0], encoding="utf-8", errors="replace") as f:
            text = f.read()
    score, rows = score_text(text, register)
    if score is None:
        print("no scorable text")
        return
    print(f"OVERALL VOICE MATCH ({register}): {score}/100")
    print("  (higher = closer to your writing)")
    print()
    for key, ref, val, sim, w in rows:
        bar = "#" * (sim // 5)
        print(f"{key:28s} ref={ref:8.3f}  yours={val:8.3f}  match={sim:3d}%  {bar}")


def selfcheck():
    import random
    random.seed(42)
    blocks = []
    for fp in X.pick_files(X.VAULT):
        blocks.extend(X.parse_blocks(fp))
    users = [X.clean_block(t).strip() for sp, t in blocks if sp == "user"]
    ais = [X.clean_block(t).strip() for sp, t in blocks if sp == "ai"]
    users = [u for u in users if u]
    ais = [a for a in ais if a]
    random.shuffle(users)
    random.shuffle(ais)

    def chunks(msgs, size=10000):
        buf, out = [], []
        for m in msgs:
            buf.append(m)
            if sum(len(b) for b in buf) >= size:
                out.append("\n\n".join(buf))
                buf = []
        if buf:
            out.append("\n\n".join(buf))
        return out

    us = score_many(chunks(users)[:40])
    as_ = score_many(chunks(ais)[:40])
    um = sum(us) / len(us)
    am = sum(as_) / len(as_)
    print(f"self-check on {len(us)} user chunks:  avg match {um:.1f}/100")
    print(f"self-check on {len(as_)} AI chunks:    avg match {am:.1f}/100")
    print(f"separation: {um - am:+.1f} points  (want clearly positive)")


def sample_user(n):
    blocks = []
    for fp in X.pick_files(X.VAULT):
        blocks.extend(X.parse_blocks(fp))
    users = [X.clean_block(t).strip() for sp, t in blocks if sp == "user"]
    users = [u for u in users if u]
    random.seed(1)
    random.shuffle(users)
    for i, u in enumerate(users[:n]):
        print(f"--- {i+1} ---")
        print(u[:400])


def score_many(texts):
    out = []
    for t in texts:
        s, _ = score_text(t)
        if s is not None:
            out.append(s)
    return out


if __name__ == "__main__":
    main()