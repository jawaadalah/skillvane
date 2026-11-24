<p align="center">
  <img src="assets/logo.png" alt="skillvane logo" width="160">
</p>

<h1 align="center">skillvane</h1>

<p align="center">
  <strong>GitHub Trending, turned into installable agent skills — updated weekly, curated, vendor-neutral.</strong>
</p>

<p align="center">
  <img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-blue.svg">
  <img alt="Python 3.9+" src="https://img.shields.io/badge/python-3.9%2B-3776AB.svg">
  <img alt="Dependencies: none" src="https://img.shields.io/badge/dependencies-0-brightgreen.svg">
  <img alt="API key: not required" src="https://img.shields.io/badge/API%20key-none-brightgreen.svg">
  <img alt="Works with Claude Code, Codex, Cursor, Gemini CLI, Copilot" src="https://img.shields.io/badge/agents-Claude%20Code%20%C2%B7%20Codex%20%C2%B7%20Cursor%20%C2%B7%20Gemini%20%C2%B7%20Copilot-orange.svg">
</p>

---

## What is skillvane?

Every week, a handful of repositories explode on GitHub Trending.
Most developers bookmark them, skim the README, and forget them.
Coding agents could learn from those repos — but nobody has time to
read five new codebases every Monday.

**skillvane** does the reading for you. It is a small, deterministic
command-line tool (pure Python standard library, zero dependencies,
no API key) that:

1. **Fetches** the current GitHub Trending snapshot (daily, weekly, or monthly).
2. **Explains** each top repository in exactly five lines: velocity,
   scale, stack, positioning, and the reusable pattern behind it.
3. **Packs** the result into a *skill pack* — a `SKILL.md` briefing plus
   one original, MIT-licensed starter template per winning pattern —
   that you can drop into Claude Code, Codex, Cursor, Gemini CLI,
   Copilot, or any agent that reads skill files.

Think of a weather vane: it does not create the wind, it shows you
which way the wind is blowing. skillvane points at the direction
open source is moving this week, and hands your agent a starter kit
for that direction.

## Why not just read Trending yourself?

| You, manually | skillvane |
|---|---|
| Open trending page, skim 25 repos | One command, top 5 distilled |
| Guess why a repo is viral | Five data-backed reasons per repo |
| Copy ideas ad-hoc, license unclear | Original templates, MIT, attribution included |
| Repeat from scratch next week | Re-run two commands; pack is updated weekly |
| Notes scattered in bookmarks | One folder your agent can read directly |

## Quickstart

Install in one command (no pip package, no dependencies — it is a
single-file tool):

```bash
curl -O https://raw.githubusercontent.com/kontenlaris-studio/skillvane/main/skillvane.py
```

Then fetch this week's trend and build your first pack:

```bash
python3 skillvane.py fetch --period weekly
python3 skillvane.py pack
```

That is it. Your pack lands in `packs/<date>-weekly/`:

```
packs/2026-11-24-weekly/
├── SKILL.md            # the briefing your agent reads
├── patterns.md         # winning patterns, grouped
├── ATTRIBUTION.md      # sources, links, licenses
├── LICENSE             # MIT, for everything skillvane generated
├── manifest.json       # machine-readable pack index
└── templates/
    ├── plan-annotation/SKILL.md
    ├── code-review/SKILL.md
    └── research-synthesis/SKILL.md
```

Verify the tool any time with the built-in, offline test suite:

```bash
python3 skillvane.py selftest
# selftest: 14/14 passed
```

## Demo output

Real output from a live weekly run (November 2026):

```text
$ python3 skillvane.py fetch --period weekly
fetch: 13 repos (weekly) -> data/trending-weekly-2026-11-24.json
  #1 backnotprop/plannotator +2395 stars/weekly
  #2 google-labs-code/stitch-skills +2572 stars/weekly
  #3 GoogleChrome/modern-web-guidance-src +2694 stars/weekly
  #4 alibaba/open-code-review +3015 stars/weekly
  #5 mvanhorn/last30days-skill +5448 stars/weekly

$ python3 skillvane.py pack
pack: 10 files -> packs/2026-11-24-weekly (digest c480ffd79f970595)
```

And inside the generated `SKILL.md`, each repo gets a five-line brief:

```text
### #1 backnotprop/plannotator
- Velocity: +2,395 stars this week — rank #1 on GitHub Trending (weekly).
- Scale: 14,877 total stars and 1,437 forks (fork ratio 0.10;
  ~0.10+ signals real adoption, not just clicks).
- Stack: TypeScript — matches the language mix currently winning.
- Positioning: "The workspace to stay in the loop and on top of agents…"
- Pattern: fits the 'Human-in-the-loop plan annotation' pattern.
```

A full real pack is included in [`examples/sample-pack/`](examples/sample-pack/).

## Using a pack with your agent

Copy the pack folder into your agent's skills directory:

| Agent | Where to put the pack |
|---|---|
| Claude Code | `.claude/skills/trending-weekly-pack/` |
| Codex | your project's skills / instructions folder |
| Cursor | `.cursor/rules/` or your skills folder |
| Gemini CLI | your extensions / context folder |
| Copilot | your repository's custom instructions folder |

Then ask your agent things like:

- "Apply the code-review starter template to this repository."
- "Which pattern from this week's pack fits a research tool?"
- "Scaffold a new skill following the plan-annotation template."

Because a pack is plain Markdown plus JSON, it also works as a
human-readable weekly briefing — no agent required.

## How it works

```
github.com/trending ──fetch──▶ snapshot JSON (data/)
                                    │
                                    ▼
                        deterministic classifier
                        (keyword rules, no LLM)
                                    │
              ┌─────────────────────┼─────────────────────┐
              ▼                     ▼                     ▼
        five-line briefs     pattern grouping     starter templates
              └─────────────────────┼─────────────────────┘
                                    ▼
                              skill pack folder
```

Design principles:

- **Deterministic first.** The same snapshot always produces the
  same pack (packs carry a content digest). No LLM is involved, so
  there is nothing to hallucinate and nothing to pay for.
- **Metadata only.** skillvane reads public trending metadata —
  names, descriptions, star counts. It never downloads or copies
  code from trending repositories.
- **Original templates.** Every starter template is written from
  scratch by the skillvane project and released under MIT. The
  trending repos are credited in `ATTRIBUTION.md` and governed by
  their own licenses.
- **Weekly cadence.** Trending is a moving target; packs are meant
  to be regenerated weekly and curated by you before use.

## Commands

| Command | What it does |
|---|---|
| `skillvane fetch [--period daily\|weekly\|monthly] [--out FILE]` | Download a trending snapshot to `data/` |
| `skillvane pack [--snapshot FILE] [--top N] [--out DIR]` | Build a skill pack from a snapshot |
| `skillvane selftest` | Run the offline test suite (14 checks) |

## How skillvane compares

Vendor-neutral by design. Stitch skills serve Google's Stitch MCP
ecosystem; Plannotator is a full annotation workspace. skillvane is
neither a vendor catalog nor a workspace — it is the weekly briefing
layer in front of all of them.

| | skillvane | Stitch Skills (Google Labs) | Plannotator |
|---|---|---|---|
| Purpose | Trending → skill packs | Skill library for Stitch MCP | Plan/spec annotation workspace |
| Vendor lock-in | None — any agent | Stitch / Google ecosystem | Own workspace app |
| API key required | No | Depends on setup | No (app) |
| Dependencies | 0 (Python stdlib) | Varies per skill | Full application |
| Works offline | After fetch, yes | Partially | Yes (local app) |
| Output | Markdown skill pack | Skills for one MCP server | Annotations & feedback |
| Updated | Weekly, curated packs | Per release | Per release |
| License | MIT | Apache-2.0 | Apache-2.0 |

## Roadmap

- [x] Weekly / daily / monthly trending snapshots
- [x] Deterministic five-line briefs and pattern grouping
- [x] Original MIT starter templates per pattern
- [ ] Hacker News as a second signal source
- [ ] Pack diffing: what changed since last week's pack
- [ ] Optional one-command installers per agent
- [ ] Scheduled weekly pack published as a GitHub Release

## Contributing

Issues and pull requests are welcome. Please keep the tool
dependency-free (Python standard library only) and deterministic:
new pattern rules need a selftest case. Run
`python3 skillvane.py selftest` before submitting.

## Bahasa Indonesia (singkat)

skillvane mengubah snapshot GitHub Trending mingguan menjadi
*skill pack* siap pasang untuk coding agent apa pun (Claude Code,
Codex, Cursor, Gemini CLI, Copilot). Tanpa dependensi, tanpa API
key, deterministik. Jalankan `skillvane fetch` lalu `skillvane pack`
setiap minggu; pack diperbarui mingguan dan dikurasi dari snapshot
terbaru. Template starter-nya original dan berlisensi MIT; repo
trending hanya diambil metadatanya dan selalu dicantumkan
atribusinya.

## License

MIT — see [LICENSE](LICENSE). Generated packs carry their own MIT
license; referenced trending repositories remain under their
respective licenses (see each pack's `ATTRIBUTION.md`).
