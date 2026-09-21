"""Build the formal-register fingerprint from handwritten-schoolbook transcriptions.

Input:  folder (or files) of plain .txt, e.g. output of transcribe.py.
Output: merges the `formal` register into style_profile.json, keeps `casual`.

Usage:
  python build_formal.py <folder-or-file> [...]

Pure stdlib, reuses extract_profile's feature pipeline.
"""
import os, sys, json

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_profile as X

PROFILE = X.OUT_JSON


def gather(paths):
    blocks = []
    for p in paths:
        if os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                for f in files:
                    if f.lower().endswith(".txt"):
                        blocks.append(os.path.join(root, f))
        else:
            blocks.append(p)
    out = []
    for fp in blocks:
        with open(fp, encoding="utf-8", errors="replace") as fh:
            out.append(("user", fh.read()))
    return out


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    raw = gather(sys.argv[1:])
    stats = X.block_stats(raw)
    if stats["words_total"] == 0:
        print(f"no text found in {sys.argv[1:]}")
        sys.exit(1)
    formal = X.rates(stats)

    with open(PROFILE, encoding="utf-8") as f:
        prof = json.load(f)
    prof["formal"] = formal
    prof["meta"]["registers"]["formal"] = (
        "schoolbook transcription fingerprint "
        f"({formal['word_count']} words, {formal['n_messages']} samples)"
    )
    with open(PROFILE, "w", encoding="utf-8") as f:
        json.dump(prof, f, indent=2, ensure_ascii=False)
    print(f"added formal register to {PROFILE}")
    print(f"  words: {formal['word_count']}  messages: {formal['n_messages']}")
    for k, v in formal.items():
        if isinstance(v, (int, float)):
            print(f"  {k}: {v}")
    print("\ntry it:  python tools\\score.py --formal <your-text.txt>")


if __name__ == "__main__":
    main()