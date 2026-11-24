#!/usr/bin/env python3
"""skillvane selftest — deterministic, offline. Run: python3 skillvane.py selftest"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import skillvane as sv

FIXTURE_HTML = """
<html><body>
<article class="Box-row">
  <h2 class="h3 lh-condensed"><a href="/acme/planmate">acme / planmate</a></h2>
  <p class="col-9 color-fg-muted my-1 pr-4">Annotate plans and review agent diffs in one click</p>
  <span itemprop="programmingLanguage">TypeScript</span>
  <a href="/acme/planmate/stargazers">12,345</a>
  <a href="/acme/planmate/forks">1,234</a>
  <span>2,345 stars this week</span>
</article>
<article class="Box-row">
  <h2 class="h3 lh-condensed"><a href="/globex/deep-research-skill">globex / deep-research-skill</a></h2>
  <p class="col-9 color-fg-muted my-1 pr-4">Research any topic across the web and synthesize a brief</p>
  <span itemprop="programmingLanguage">Python</span>
  <a href="/globex/deep-research-skill/stargazers">9,876</a>
  <a href="/globex/deep-research-skill/forks">987</a>
  <span>5,678 stars this week</span>
</article>
</body></html>
"""

FIXTURE_SNAP = {
    "tool": "skillvane", "version": sv.VERSION, "period": "weekly",
    "source_url": "https://github.com/trending?since=weekly",
    "fetched_at": "2026-11-25T00:00:00+00:00", "date": "2026-11-25", "count": 2,
    "repos": [
        {"rank": 1, "full_name": "acme/planmate", "owner": "acme", "name": "planmate",
         "url": "https://github.com/acme/planmate",
         "description": "Annotate plans and review agent diffs in one click",
         "language": "TypeScript", "stars": 12345, "forks": 1234,
         "stars_in_period": 2345, "period": "weekly"},
        {"rank": 2, "full_name": "globex/deep-research-skill", "owner": "globex",
         "name": "deep-research-skill", "url": "https://github.com/globex/deep-research-skill",
         "description": "Research any topic across the web and synthesize a brief",
         "language": "Python", "stars": 9876, "forks": 987,
         "stars_in_period": 5678, "period": "weekly"},
    ],
}

def run():
    checks = []
    def check(name, ok):
        checks.append((name, bool(ok)))

    repos = sv.parse_trending(FIXTURE_HTML, "weekly")
    check("parser finds 2 repos", len(repos) == 2)
    check("parser rank order + names", [r["full_name"] for r in repos] ==
          ["acme/planmate", "globex/deep-research-skill"])
    check("parser stars/forks/period numbers",
          repos[0]["stars"] == 12345 and repos[0]["forks"] == 1234
          and repos[0]["stars_in_period"] == 2345 and repos[1]["stars_in_period"] == 5678)
    check("parser language + description",
          repos[0]["language"] == "TypeScript" and "Annotate plans" in repos[0]["description"])
    check("classify plan-annotation", sv.classify(repos[0]) == "plan-annotation")
    check("classify research-synthesis", sv.classify(repos[1]) == "research-synthesis")
    check("why_viral is exactly 5 lines", all(len(sv.why_viral(r, "weekly")) == 5 for r in repos))

    files = sv.build_pack(FIXTURE_SNAP, top=5)
    check("pack has SKILL.md + patterns + attribution + license + manifest",
          all(k in files for k in ("SKILL.md", "patterns.md", "ATTRIBUTION.md", "LICENSE", "manifest.json")))
    check("pack has one template per distinct pattern",
          "templates/plan-annotation/SKILL.md" in files and "templates/research-synthesis/SKILL.md" in files)
    check("pack SKILL.md cites both repos with links",
          "acme/planmate" in files["SKILL.md"] and "https://github.com/globex/deep-research-skill" in files["SKILL.md"])
    check("templates declare MIT + no-copy guardrail",
          "license: MIT" in files["templates/plan-annotation/SKILL.md"]
          and "Never copy code" in files["templates/plan-annotation/SKILL.md"])
    check("pack build is deterministic", sv.pack_digest(files) == sv.pack_digest(sv.build_pack(FIXTURE_SNAP, top=5)))
    check("manifest lists top repos",
          json.loads(files["manifest.json"])["top"] == ["acme/planmate", "globex/deep-research-skill"])
    check("slugify", sv.slugify("Hello World!") == "hello-world")

    passed = sum(1 for _n, ok in checks if ok)
    for name, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    print(f"selftest: {passed}/{len(checks)} passed")
    return 0 if passed == len(checks) else 1

if __name__ == "__main__":
    sys.exit(run())
