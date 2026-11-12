#!/usr/bin/env python3
"""Generate profile/activity.svg: an animated contribution calendar built from
the GitHub GraphQL API (real data only). Run by .github/workflows/activity.yml."""
import json, os, sys, urllib.request
from datetime import date

USER = os.environ.get("GH_USER", "Ravitejeshnagasarapu")
OUT = os.environ.get("OUT", "profile/activity.svg")
FONT = "'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "'Courier New', Consolas, monospace"
COLORS = {"NONE": "#12203a", "FIRST_QUARTILE": "#1e3a8a", "SECOND_QUARTILE": "#2563eb",
          "THIRD_QUARTILE": "#22d3ee", "FOURTH_QUARTILE": "#a5f3fc"}
QUERY = """query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{
totalContributions weeks{contributionDays{date contributionCount contributionLevel weekday}}}}}}"""


def fetch(user, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": user}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "profile-activity-generator"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        sys.exit(f"GraphQL error: {data['errors']}")
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def render(cal):
    weeks = cal["weeks"]
    W, H = 1200, 296
    left, top, pitch, size = 70, 118, 19.6, 16
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">'
             f'<title id="t">GitHub contribution calendar for {USER}</title>'
             f'<desc id="d">{cal["totalContributions"]} contributions in the last year.</desc>'
             '<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#080f1e"/><stop offset="1" stop-color="#0d1c33"/></linearGradient>'
             '<linearGradient id="acc" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#3b82f6"/><stop offset="0.55" stop-color="#22d3ee"/><stop offset="1" stop-color="#a78bfa"/></linearGradient></defs>',
             f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="14" fill="url(#bg)" stroke="#2dd4bf" stroke-opacity="0.35"/>',
             f'<text x="40" y="44" font-family="{MONO}" font-size="13" letter-spacing="3" fill="#22d3ee">CONTRIBUTIONS · LAST 12 MONTHS</text>',
             f'<text x="40" y="76" font-family="{FONT}" font-size="26" font-weight="800" fill="#f1f5f9">{cal["totalContributions"]:,} <tspan font-size="16" font-weight="400" fill="#9fb3c8">contributions on GitHub</tspan></text>']
    for label, wd in (("Mon", 1), ("Wed", 3), ("Fri", 5)):
        parts.append(f'<text x="{left-10}" y="{top+wd*pitch+size-3:.0f}" text-anchor="end" font-family="{FONT}" font-size="11" fill="#7f93aa">{label}</text>')
    last_month = None
    for i, wk in enumerate(weeks):
        days = wk["contributionDays"]
        if not days:
            continue
        m = date.fromisoformat(days[0]["date"]).strftime("%b")
        if m != last_month and (i == 0 or date.fromisoformat(days[0]["date"]).day <= 7):
            parts.append(f'<text x="{left+i*pitch:.0f}" y="{top-10}" font-family="{FONT}" font-size="11" fill="#7f93aa">{m}</text>')
            last_month = m
        parts.append(f'<g><animate attributeName="opacity" values="0;1" dur="0.5s" begin="{i*0.025:.2f}s" fill="freeze"/>')
        for d in days:
            parts.append(f'<rect x="{left+i*pitch:.1f}" y="{top+d["weekday"]*pitch:.1f}" width="{size}" height="{size}" rx="4" '
                         f'fill="{COLORS.get(d["contributionLevel"], COLORS["NONE"])}"/>')
        parts.append('</g>')
    lx = W - 40 - 5 * 22 - 90
    parts.append(f'<text x="{lx}" y="{H-24}" text-anchor="end" font-family="{FONT}" font-size="11" fill="#7f93aa">Less</text>')
    for k, c in enumerate(COLORS.values()):
        parts.append(f'<rect x="{lx+10+k*22}" y="{H-36}" width="14" height="14" rx="4" fill="{c}"/>')
    parts.append(f'<text x="{lx+10+5*22+4}" y="{H-24}" font-family="{FONT}" font-size="11" fill="#7f93aa">More</text>')
    parts.append(f'<rect x="40" y="{H-30}" width="0" height="3" rx="1.5" fill="url(#acc)"><animate attributeName="width" values="0;120" dur="1.4s" fill="freeze"/></rect></svg>')
    return "".join(parts)


if __name__ == "__main__":
    cal = fetch(USER, os.environ["GITHUB_TOKEN"])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(render(cal))
    print(f"wrote {OUT}: {cal['totalContributions']} contributions")
