# voice-match

Rewrites text so it reads like you wrote it — and passes AI detectors, because the two are the same thing. No LLM post-processing needed. Your own writing style is the anti-AI-detector.

Built from a real chat-export fingerprint (9,800+ of one user's messages across ~760 Obsidian chat files), not from a generic "human" template.

## What it is

Two pieces:

1. **A fingerprint.** `tools/extract_profile.py` scans an Obsidian vault for your messages (`## You` / `## Assistant` / `## Claude` headers), separates your words from the model's, and writes `style_profile.json` — sentence-length distribution, contraction rate, informal tokens (`yk`, `idk`, `bc`, `rrly`...), fillers, first-person rate, lowercase-start rate, average word length. Pure stdlib, counts only, no ML.
2. **A checker.** `tools/score.py` scores any text against the profile (0-100), broken down per signal, so you can iterate until your rewrites actually match. Self-validation shows real user writing scores ~50 while AI writing scores ~21 — a real gap, on 10k-character documents.

Raw output: `report.txt`.

## Why it works

AI detectors measure things like perplexity (word predictability) and burstiness (sentence-length variation). Uniform 15-25 word sentences, predictable transitions (`furthermore`, `moreover`), and vocabulary spikes (`delve` exploded ~25x after ChatGPT — Kobak et al. 2024, Science Advances) are what get flagged. Word swaps alone don't beat detectors — structure and authentic rhythm do. The ruleset in `rules/humanize.md` documents every tell with sources and turns it into concrete rules.

## Registers

- **casual** — your raw fingerprint: lowercase starts, contractions, fillers, abbreviations, natural SPAG at your measured rates.
- **semi-formal** — whole sentences, mild contractions, no slang, no `and`/`so` chains. Mild imperfections only.
- **formal** — no contractions, complete grammar, still short sentences and direct voice. Zero imperfections.

The imperfection dial is calibrated to habits measured from your own messages (missing commas, lowercase starts, run-ons). Staged/random typos are detectable and banned.

## Usage

Score any text (paste ≥1000 words for a meaningful result):

```
python tools/score.py my-draft.txt
python tools/score.py -            # stdin
```

Validate the profile against held-out samples:

```
python tools/score.py --selfcheck
```

Inside opencode, the `voice-match` agent + `/voice` command rewrite text in your voice (casual by default; prefix with `semi-formal:` or `formal:` to switch register). The agent reads `style_profile.json` + `rules/humanize.md` as ground truth and prints a 3-5 line confirmation before rewriting.

## Demo

`demo/input.txt` is an AI-style paragraph. `demo/casual.txt`, `demo/semi-formal.txt`, `demo/formal.txt` are the same content rewritten in your voice at each register.

## Status / roadmap

- [x] vault chat format survey
- [x] profile extractor + style_profile.json
- [x] scorer + self-validation (separation ~+29)
- [x] detector ruleset
- [x] opencode agent + `/voice`
- [x] `tools/transcribe.py` — photos of old handwritten schoolbooks → text via any OpenAI-compatible vision endpoint (local Qwen-VL / Ollama default, or Gemini via URL+key). Model flags uncertain words inline as `[unclear]`; `--report` aggregates flagged spans for escalation instead of silently guessing. Run: `transcribe.py <dir> --dry-run` to preview, then without the flag. Classic OCR can't read messy handwriting, so this is the route to a real formal-register fingerprint.
- [ ] v2: scan the schoolbooks, run `transcribe.py`, rebuild the profile with the formal fingerprint.