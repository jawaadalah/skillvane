#!/usr/bin/env python3
"""skillvane — turn GitHub Trending snapshots into installable agent skill packs.

Deterministic, Python stdlib only, no API key. Commands:
  skillvane fetch [--period weekly|daily|monthly] [--out DIR]
  skillvane pack  [--snapshot FILE] [--top N] [--out DIR]
  skillvane selftest
A "skill pack" is a folder any coding agent (Claude Code, Codex, Cursor,
Gemini CLI, Copilot, ...) can consume: a SKILL.md briefing on what is
trending and why, plus one original MIT-licensed starter template per
dominant pattern found in the top repos.
"""
import argparse, hashlib, html, json, re, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
VERSION = "0.1.0"
UA = {"User-Agent": f"skillvane/{VERSION} (trending research tool)"}
PERIODS = ("daily", "weekly", "monthly")

# ---------------------------------------------------------------- fetch ----
def _clean(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()

def _num(s):
    m = re.search(r"([\d,]+)", s or "")
    return int(m.group(1).replace(",", "")) if m else 0

def parse_trending(page, period="weekly"):
    """Parse github.com/trending HTML into repo dicts, rank order kept."""
    repos = []
    for chunk in page.split("<article")[1:]:
        m = re.search(r'<h2[^>]*>\s*<a[^>]+href="/([^"/\s]+/[^"/\s]+)"', chunk, re.S)
        if not m:
            continue
        full = m.group(1)
        if full.count("/") != 1 or " " in full:
            continue
        desc_m = re.search(r'<p class="col-9[^"]*"[^>]*>(.*?)</p>', chunk, re.S)
        lang_m = re.search(r'itemprop="programmingLanguage">([^<]+)<', chunk)
        star_m = re.search(r'href="/[^"]+/stargazers"[^>]*>(.*?)</a>', chunk, re.S)
        fork_m = re.search(r'href="/[^"]+/forks"[^>]*>(.*?)</a>', chunk, re.S)
        per_m = re.search(r"([\d,]+)\s+stars?\s+(today|this week|this month)", chunk)
        repos.append({
            "rank": len(repos) + 1, "full_name": full,
            "owner": full.split("/")[0], "name": full.split("/")[1],
            "url": f"https://github.com/{full}",
            "description": _clean(desc_m.group(1)) if desc_m else "",
            "language": lang_m.group(1).strip() if lang_m else None,
            "stars": _num(_clean(star_m.group(1))) if star_m else 0,
            "forks": _num(_clean(fork_m.group(1))) if fork_m else 0,
            "stars_in_period": _num(per_m.group(1)) if per_m else 0,
            "period": period,
        })
        if len(repos) >= 25:
            break
    return repos

def fetch_snapshot(period="weekly", timeout=25):
    if period not in PERIODS:
        raise ValueError(f"period must be one of {PERIODS}")
    url = f"https://github.com/trending?since={period}"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        repos = parse_trending(r.read().decode("utf-8", "replace"), period)
    now = datetime.now(timezone.utc)
    return {"tool": "skillvane", "version": VERSION, "period": period,
            "source_url": url, "fetched_at": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"), "count": len(repos), "repos": repos}

def cmd_fetch(args):
    DATA.mkdir(parents=True, exist_ok=True)
    snap = fetch_snapshot(args.period)
    out = Path(args.out) if args.out else DATA / f"trending-{args.period}-{snap['date']}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snap, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"fetch: {snap['count']} repos ({args.period}) -> {out}")
    for r in snap["repos"][:5]:
        print(f"  #{r['rank']} {r['full_name']} +{r['stars_in_period']} stars/{args.period}")
    return 0

# ----------------------------------------------------------------- pack ----
# Deterministic keyword -> pattern rules. Order matters; first match wins
# per repo, and every distinct pattern across the top-N becomes a template.
PATTERN_RULES = [  # specific patterns first; the generic agent-skills bucket last
    ("plan-annotation",     ("plan", "annotat", "spec"), "Human-in-the-loop plan annotation"),
    ("code-review",         ("review", "lint", "audit"), "Deterministic code review pipeline"),
    ("research-synthesis",  ("research", "search", "news"), "Multi-source research synthesis"),
    ("web-guidance",        ("web", "browser", "css", "frontend"), "Web best-practice guidance"),
    ("cli-anything",        ("cli", "terminal", "command"), "CLI wrapper for an existing tool"),
    ("agent-skills",        ("skill", "skills", "agent"), "Reusable agent skill library"),
]
FALLBACK_PATTERN = ("agent-tooling", (), "General agent-native tooling")

def classify(repo):
    text = f"{repo.get('name','')} {repo.get('description','')}".lower()
    for slug, keys, _label in PATTERN_RULES:
        if any(k in text for k in keys):
            return slug
    return FALLBACK_PATTERN[0]

def pattern_label(slug):
    for s, _k, label in PATTERN_RULES + [FALLBACK_PATTERN]:
        if s == slug:
            return label
    return slug

def why_viral(repo, period):
    """Exactly 5 deterministic lines explaining the repo's momentum."""
    stars_p = repo.get("stars_in_period", 0)
    forks = repo.get("forks", 0)
    stars = repo.get("stars", 0)
    ratio = (forks / stars) if stars else 0.0
    unit = {"daily": "today", "weekly": "this week", "monthly": "this month"}[period]
    return [
        f"Velocity: +{stars_p:,} stars {unit} — rank #{repo['rank']} on GitHub Trending ({period}).",
        f"Scale: {stars:,} total stars and {forks:,} forks (fork ratio {ratio:.2f}; ~0.10+ signals real adoption, not just clicks).",
        f"Stack: {repo.get('language') or 'multi-language'} — matches the language mix currently winning its category.",
        f"Positioning: \"{repo.get('description','')[:110]}\" — one clear promise, readable in a single line.",
        f"Pattern: fits the '{pattern_label(classify(repo))}' pattern (slug: {classify(repo)}).",
    ]

def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "repo"

STARTER_SKILL = """---
name: {slug}-starter
description: Original MIT starter template for the "{label}" pattern, generated by skillvane from public GitHub Trending metadata. No code was copied from any trending repository.
license: MIT
---

# {label} — starter skill

## When to use
Use this skill when the user asks for work matching the "{label}" pattern
that is currently trending on GitHub (pattern slug: `{slug}`).

## Workflow
1. Restate the user's goal in one line and confirm the deliverable.
2. Gather inputs deterministically first (files, commands, public metadata);
   only call an LLM or external API when a step truly needs judgement.
3. Produce the smallest useful artifact, then a short summary of what changed.
4. Verify: run the project's own checks/tests and report the real output.
5. Close with next steps the user can accept or reject in one reply.

## Guardrails
- Never copy code, text, or assets from the trending repositories that
  inspired this pattern; write original implementations.
- No fake engagement (stars, forks, reviews) — growth must be earned.
- Keep secrets out of files, logs, and prompts.

## Source pattern (attribution)
Pattern distilled from public trending metadata, notably:
{attribution}
"""

def build_pack(snapshot, top=5):
    """Return {relative_path: content} for the whole pack. Pure & deterministic."""
    repos = snapshot["repos"][:top]
    period = snapshot.get("period", "weekly")
    date = snapshot.get("date", "unknown")
    patterns = {}
    for r in repos:
        patterns.setdefault(classify(r), []).append(r)

    files = {}
    lines = [
        "---",
        f"name: trending-{period}-pack",
        f"description: What is trending on GitHub ({period}, {date}), why it is viral, and original starter skills per winning pattern. Generated by skillvane {VERSION}.",
        "license: MIT",
        "---",
        "",
        f"# GitHub Trending Skill Pack — {period} · {date}",
        "",
        f"Source: {snapshot.get('source_url','https://github.com/trending')} "
        f"(fetched {snapshot.get('fetched_at','')}). Metadata only; no code copied.",
        "",
        "## Top repos and why they are viral",
        "",
    ]
    for r in repos:
        lines += [f"### #{r['rank']} [{r['full_name']}]({r['url']})",
                  f"_{r.get('description','')}_", ""]
        lines += [f"- {w}" for w in why_viral(r, period)]
        lines += ["", f"Starter template: `templates/{classify(r)}/SKILL.md`", ""]
    lines += ["## How to use this pack", "",
              "1. Copy this folder into your agent's skills directory "
              "(Claude Code: `.claude/skills/`, Codex/Cursor: your skills or rules folder).",
              "2. Ask your agent to apply the matching starter template.",
              "3. Re-run `skillvane fetch && skillvane pack` next week — packs are updated weekly and curated from the latest snapshot.",
              ""]
    files["SKILL.md"] = "\n".join(lines)

    plines = [f"# Patterns — {period} · {date}", ""]
    for slug, members in sorted(patterns.items()):
        plines += [f"## {pattern_label(slug)} (`{slug}`)",
                   f"Seen in {len(members)} of the top {len(repos)}: "
                   + ", ".join(m["full_name"] for m in members), ""]
    files["patterns.md"] = "\n".join(plines)

    for slug, members in sorted(patterns.items()):
        attribution = "\n".join(
            f"- [{m['full_name']}]({m['url']}) — trending #{m['rank']} ({period}, {date}); "
            f"see that repository for its own license." for m in members)
        files[f"templates/{slug}/SKILL.md"] = STARTER_SKILL.format(
            slug=slug, label=pattern_label(slug), attribution=attribution)
    files["ATTRIBUTION.md"] = (
        "# Attribution\n\nAll trending data is public metadata from GitHub Trending "
        f"({snapshot.get('source_url','')}), fetched {snapshot.get('fetched_at','')}.\n"
        "Repository names and links belong to their owners; each linked repository "
        "is governed by its own license. Everything else in this pack — summaries, "
        "pattern notes, and starter templates — is original work released under MIT "
        "(see the pack's LICENSE).\n\nRepos referenced:\n"
        + "\n".join(f"- [{r['full_name']}]({r['url']})" for r in repos) + "\n")
    files["LICENSE"] = MIT_TEXT
    files["manifest.json"] = json.dumps({
        "tool": "skillvane", "version": VERSION, "period": period, "date": date,
        "top": [r["full_name"] for r in repos],
        "patterns": {k: [m["full_name"] for m in v] for k, v in sorted(patterns.items())},
        "files": sorted(files.keys()) + ["manifest.json"],
    }, indent=2, ensure_ascii=False)
    return files

MIT_TEXT = """MIT License

Copyright (c) 2026 Kontenlaris Studio

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

def pack_digest(files):
    h = hashlib.sha256()
    for k in sorted(files):
        h.update(k.encode()); h.update(files[k].encode())
    return h.hexdigest()[:16]

def cmd_pack(args):
    if args.snapshot:
        snap_path = Path(args.snapshot)
    else:
        cands = sorted(DATA.glob("trending-*.json"))
        if not cands:
            print("pack: no snapshot found — run `skillvane fetch` first", file=sys.stderr)
            return 2
        snap_path = cands[-1]
    snapshot = json.loads(snap_path.read_text(encoding="utf-8"))
    files = build_pack(snapshot, top=args.top)
    out = Path(args.out) if args.out else ROOT / "packs" / f"{snapshot['date']}-{snapshot.get('period','weekly')}"
    for rel, content in files.items():
        p = out / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    print(f"pack: {len(files)} files -> {out} (digest {pack_digest(files)})")
    return 0

# ------------------------------------------------------------- selftest ----
def cmd_selftest(_args):
    import selftest
    return selftest.run()

def main(argv=None):
    ap = argparse.ArgumentParser(prog="skillvane", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch"); f.add_argument("--period", default="weekly")
    f.add_argument("--out", default=None); f.set_defaults(fn=cmd_fetch)
    p = sub.add_parser("pack"); p.add_argument("--snapshot", default=None)
    p.add_argument("--top", type=int, default=5); p.add_argument("--out", default=None)
    p.set_defaults(fn=cmd_pack)
    s = sub.add_parser("selftest"); s.set_defaults(fn=cmd_selftest)
    args = ap.parse_args(argv)
    return args.fn(args)

if __name__ == "__main__":
    sys.exit(main())
