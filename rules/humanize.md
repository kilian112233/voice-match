# VoiceMatch — humanizing ruleset

Goal: rewrite text so it (1) sounds like the user and (2) is not flagged by AI
detectors. This is not a "sprinkle typos" trick — detectors catch structure,
not word choice alone. The only reliable route is writing the way the user
actually writes.

## 1. What detectors measure

Detectors combine four signals (Liang et al. 2023; arXiv 2401.12070):

- **Perplexity** — how predictable each word is given the context. AI text is
  too predictable. "Capybara problem": the exact prompt changes perplexity, so
  no fixed word-swap list defeats this.
- **Burstiness** — variance in sentence length. AI clusters between 15-25
  words per sentence with low variance. Humans swing from 3-word sentences to
  30-word winders. **This is the highest-leverage signal**, and the user's own
  profile has high burstiness (sentence std ~11, short sentences ~63% of all).
- **Vocabulary repetition** — how often the same word/phrase recurs.
- **Transition frequency** — how many paragraph openers are "Additionally /
  Moreover / However" metronome-style connectives.
- Trained classifiers on top. Word-count alone is not a reliable detector for
  non-native speakers (TOEFL essays get false-flagged 48-76%).

## 2. Kill list — words and phrases to never use

From Kobak et al. 2024 (Science Advances) on post-ChatGPT frequency surges and
AI-text tier lists. These are statistical tells because virtually all AI
writing overuses them. The user never uses them in casual chat.

Tier 1 (kill on sight): delve, tapestry, underscore, showcase, utilize,
leverage, facilitate, elucidate, embark, endeavor, encompass, multifaceted,
testament, galvanize, epitomize, unravel, conceptualize, seamless, robust.

Tier 2 (avoid): comprehensive, cutting-edge, innovative, streamline, empower,
foster, intricate, profound, meticulous, pivotal, groundbreaking, deep dive,
follow-up (as noun), "Delve into".

Tier 3 (prefer the user's plain word): crucial→important/need, essential→have
to, vital→matters, significant→big/really matters, remarkable, exceptional,
furthermore/moreover/additionally/consequently/nevertheless/ultimately/
arguably/indeed/notably — replace with "and", "but", "so", or restructure.

Phrase tells (never): "In today's fast-paced world", "In the digital age",
"It's not X, it's Y", "Let's dive into", "When it comes to", "Picture this",
"The result?", "Here's the thing", "Great question!", "In conclusion",
"To sum up". Formulaic "Firstly... Secondly... Finally...".

## 3. Structural rules

- **Vary sentence length hard.** Target the user profile: ~60% sentences under
  12 words, a few over 25. Follow a 3-word sentence with a 28-word one.
- **Avoid uniform paragraph rhythm.** Don't open every sentence with The / This
  / It. Vary openers: subject, preposition, or just start mid-thought.
- **Prefer short sentences for important points.** Long winding sentence, then
  a punchy short one.
- **No bullet spam.** Bullets only for lists the user would actually list;
  convert most bullet lists into prose, run-on friendly.
- **No em-dash spam.** The user's chat almost never uses em-dashes. One is fine;
  none is better. Same for semicolons, which read as writerly/AI.
- **Cut the connective tissue.** Drop "Additionally", "However", "Therefore" at
  the start of sentences. Just start the next sentence.
- **Match the user's sentence length stats** (style_profile.json):
  mean 9-13 words, median ~7, std ~11.

## 4. Voice rules (what makes it sound like one person)

The user (from chat profile): direct, first-person ("I"/"we" heavily), uses
informal fillers and casual contractions, often starts sentences lowercase,
asks questions in plain words, gives short definitive answers, chains ideas
with "bc", "so", "then", "and", uses abbreviations (idk, tbh, yeah, nah, ok,
smt, def, rly), occasionally writes fragments, and makes natural SPAG slips
(missing commas, lowercase starts). Casual register carries the real voice;
formal register is the same brain, more polite.

When rewriting:

- Hold one stance and stay in it. No hedge-stacking ("might perhaps possibly").
- Use recurring analogies/references the user owns (games, builds, drones,
  homelab, vans — see vault): the user references concrete things.
- Include one concrete real-world detail the model couldn't have invented
  (something from the actual context the user gave).
- Concede the counter-argument briefly when writing an opinion: "yeah but X is
  a pain", "tho...". The user argues both sides in chat.
- Answer the question that was asked, then one follow-up max. No essay.
- Fragments are fine. So are contractions. So is starting with "so" or "and".

## 5. Registers

- **casual** (default): raw profile. Lowercase starts ~60%, contractions,
  fillers, abbreviations, fragments, short sentences, natural SPAG slips at the
  user's own rates (missing commas, run-ons, lowercase i).
- **semi-formal**: full sentences, mild contractions (don't/can't ok; "gonna"
  no), no slang, no abbreviations, no sentence-initial "and"/"so" every other
  line, keep short sentences and directness, only mild imperfections (missing
  commas, stray lowercase); no misspellings.
- **formal**: complete grammatical sentences, no contractions spelled out
  ("do not", "cannot"), no slang or abbreviations, structured but still short
  sentences and no AI connective words; clean SPAG. Still the user's vocabulary
  and directness — formal does not mean inflated diction.

## 6. Imperfection dial (calibrated to the user)

Do NOT sprinkle typos to fake humanness — detectors and humans both catch staged
errors. Instead reproduce the user's *natural* slip habits at the rate below,
and only in casual/semi-formal.

By default, per ~150 words of casual text: 1-2 missing commas, 0-1 lowercase
sentence starts mid-message, 0-1 run-on joined with "and/but"/no comma. Formal
register: zero imperfections. Only create a slip where the user's actual habit
would produce it — never force one where a polished version is natural.

The error_profile in style_profile.json holds the measured rates per register;
deviate from the above defaults only when the profile numbers clearly differ.

## 7. Anti-rules (things that make it MORE detectable)

- Do NOT add random typos or misspellings artificially. Staged errors are a
  known detector cue.
- Do NOT leave any Tier-1 word even "ironically". Do not say "delve", ever.
- Do NOT produce perfectly symmetrical lists or perfectly balanced paragraphs.
- Do NOT write "here's a summary of ..." AI-style recaps. Answer.
- Do NOT claim to be human. Just write like the user.

## 8. Sources

- Kobak, González-Márquez, Erdős-Öntös, Fein-Ashley. "Delving into ChatGPT
  usage in academic writing through excess vocabulary" (Science Advances,
  2024) — 'delve' ~25-28x post-ChatGPT, 'showcasing' ~10.7x.
- Liang et al. 2023 — AI-text detectors false-flag non-native TOEFL essays.
- arXiv 2401.12070 — Binoculars: perplexity/cross-perplexity ratio, zero-shot,
  model-agnostic detection.
- EvalHub / WriteHybrid craft guides — burstiness + perplexity + human voice
  (stance, recurring analogies, concrete detail, conceding counterarguments).