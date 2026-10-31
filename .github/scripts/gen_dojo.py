#!/usr/bin/env python3
"""Gera assets/dojo-stats.svg (tema samurai) com dados reais do GitHub.

Roda na GitHub Action .github/workflows/dojo.yml. Usa só a biblioteca padrão.
Teste local sem token: python3 gen_dojo.py --demo
"""
import json, os, sys, datetime, urllib.request, random
from html import escape

USER = os.environ.get("USERNAME", "joaowyctor75-alt")
OUT = os.environ.get("OUT", "assets/dojo-stats.svg")

QUERY = """
query($login:String!){
  user(login:$login){
    followers{ totalCount }
    contributionsCollection{
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      restrictedContributionsCount
      contributionCalendar{ totalContributions weeks{ contributionDays{ contributionCount date } } }
    }
    repositories(ownerAffiliations:OWNER, isFork:false, first:100){
      totalCount
      nodes{ stargazerCount languages(first:10, orderBy:{field:SIZE, direction:DESC}){ edges{ size node{ name } } } }
    }
  }
}"""


def fetch():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(data["errors"])
    return data["data"]["user"]


def demo():
    today = datetime.date.today()
    start = today - datetime.timedelta(days=today.weekday() + 1 + 52 * 7)
    weeks, d = [], start
    random.seed(7)
    while d <= today:
        week = []
        for _ in range(7):
            if d <= today:
                week.append({"date": d.isoformat(), "contributionCount": random.choice([0, 0, 0, 1, 2, 3, 5, 8]) if d > today - datetime.timedelta(days=120) else 0})
            d += datetime.timedelta(days=1)
        weeks.append({"contributionDays": week})
    langs = [("HTML", 52000), ("CSS", 31000), ("JavaScript", 12000), ("Python", 6000)]
    return {
        "followers": {"totalCount": 4},
        "contributionsCollection": {
            "totalCommitContributions": 96, "totalPullRequestContributions": 3, "totalIssueContributions": 1,
            "restrictedContributionsCount": 0,
            "contributionCalendar": {"totalContributions": 104, "weeks": weeks},
        },
        "repositories": {"totalCount": 6, "nodes": [{"stargazerCount": 1, "languages": {"edges": [{"size": s, "node": {"name": n}} for n, s in langs]}}]},
    }


def streaks(days):
    days = sorted(days, key=lambda x: x["date"])
    longest = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] > 0 else 0
        longest = max(longest, run)
    cur = 0
    seq = list(reversed(days))
    if seq and seq[0]["contributionCount"] == 0:  # hoje ainda sem commit não quebra a sequência
        seq = seq[1:]
    for d in seq:
        if d["contributionCount"] > 0:
            cur += 1
        else:
            break
    return cur, longest


def render(u):
    cc = u["contributionsCollection"]
    cal = cc["contributionCalendar"]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    cur, longest = streaks(days)
    stars = sum(n["stargazerCount"] for n in u["repositories"]["nodes"])

    sizes = {}
    for n in u["repositories"]["nodes"]:
        for e in n["languages"]["edges"]:
            sizes[e["node"]["name"]] = sizes.get(e["node"]["name"], 0) + e["size"]
    total = sum(sizes.values()) or 1
    langs = sorted(sizes.items(), key=lambda kv: -kv[1])[:5]

    stats = [
        ("Contribuições (ano)", cal["totalContributions"] + cc["restrictedContributionsCount"]),
        ("Commits", cc["totalCommitContributions"]),
        ("Pull Requests", cc["totalPullRequestContributions"]),
        ("Repositórios", u["repositories"]["totalCount"]),
        ("Estrelas", stars),
    ]

    s = []
    # painel 1 — registros
    s.append('<text class="t h" x="40" y="96">REGISTROS</text>')
    for i, (k, v) in enumerate(stats):
        y = 130 + i * 26
        s.append(f'<g class="fade" style="animation-delay:{0.2 + i * 0.12:.2f}s">'
                 f'<path d="M42 {y-5} l5 -5 l5 5 l-5 5 z" fill="#c8102e"/>'
                 f'<text class="m" x="62" y="{y}" font-size="13" fill="#d9cfc1">{escape(k)}</text>'
                 f'<text class="m" x="282" y="{y}" font-size="14" font-weight="700" fill="#f5f0e8" text-anchor="end">{v}</text></g>')

    # painel 2 — técnicas (linguagens)
    s.append('<text class="t h" x="330" y="96">TÉCNICAS</text>')
    if not langs:
        s.append('<text class="m" x="330" y="135" font-size="13" fill="#a8998f">Treinando os primeiros golpes…</text>')
    for i, (name, size) in enumerate(langs):
        pct = size / total * 100
        y = 126 + i * 26
        w = max(4, 150 * pct / 100)
        s.append(f'<text class="m" x="330" y="{y}" font-size="13" fill="#d9cfc1">{escape(name[:12])}</text>'
                 f'<rect x="438" y="{y-10}" width="110" height="10" rx="5" fill="#2a1a20"/>'
                 f'<rect class="grow" style="animation-delay:{0.3 + i * 0.15:.2f}s" x="438" y="{y-10}" width="{w*110/150:.1f}" height="10" rx="5" fill="url(#bar)"/>'
                 f'<text class="m" x="586" y="{y}" font-size="12" fill="#f5f0e8" text-anchor="end">{pct:.0f}%</text>')

    # painel 3 — sequência
    s.append('<text class="t h" x="620" y="96">SEQUÊNCIA</text>')
    s.append(f'<g class="fade" style="animation-delay:.5s">'
             f'<text x="680" y="160" text-anchor="middle" font-family="serif" font-size="46" fill="#c8102e" class="flame">炎</text>'
             f'<text class="t" x="790" y="150" text-anchor="middle" font-size="44" font-weight="700" fill="#f5f0e8">{cur}</text>'
             f'<text class="m" x="790" y="172" text-anchor="middle" font-size="12" fill="#a8998f">dias seguidos</text>'
             f'<text class="m" x="745" y="215" text-anchor="middle" font-size="13" fill="#f4d27a">Recorde: {longest} dias</text></g>')

    # heatmap — últimas 52 semanas
    weeks = cal["weeks"][-52:]
    mx = max([d["contributionCount"] for w in weeks for d in w["contributionDays"]] + [1])
    shades = ["#21151b", "#5a0f1e", "#8a0b1f", "#c8102e", "#ff4d5e"]
    s.append('<text class="t h" x="40" y="270">TREINO DO ANO</text>')
    x0, y0, c = 40, 284, 15.6
    for wi, w in enumerate(weeks):
        cells = []
        for d in w["contributionDays"]:
            dow = datetime.date.fromisoformat(d["date"]).weekday()  # seg=0
            row = (dow + 1) % 7  # dom no topo
            n = d["contributionCount"]
            lvl = 0 if n == 0 else min(4, 1 + int(3 * n / mx))
            cells.append(f'<rect x="{x0 + wi * c:.1f}" y="{y0 + row * c:.1f}" width="12" height="12" rx="2.5" fill="{shades[lvl]}"/>')
        s.append(f'<g class="col" style="animation-delay:{0.6 + wi * 0.025:.3f}s">{"".join(cells)}</g>')
    s.append('<g class="m" font-size="11" fill="#a8998f"><text x="40" y="410">menos</text>'
             + "".join(f'<rect x="{82 + i * 16}" y="400" width="12" height="12" rx="2.5" fill="{sh}"/>' for i, sh in enumerate(shades))
             + '<text x="166" y="410">mais</text></g>')
    s.append(f'<text class="m" x="860" y="410" font-size="11" fill="#6f6168" text-anchor="end">atualizado em {datetime.date.today().strftime("%d/%m/%Y")}</text>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 430" width="900" height="430">
  <defs><linearGradient id="bar" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#8a0b1f"/><stop offset="1" stop-color="#ff4d5e"/></linearGradient></defs>
  <style>
    .t {{ font-family: Georgia, 'Times New Roman', serif; }}
    .m {{ font-family: 'Courier New', monospace; }}
    .h {{ font-size: 15px; fill: #f4d27a; letter-spacing: 4px; }}
    .fade {{ opacity: 0; animation: fade .7s ease-out forwards; }}
    @keyframes fade {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; transform: none; }} }}
    .grow {{ transform: scaleX(0); transform-box: fill-box; transform-origin: left; animation: grow 1.2s cubic-bezier(.2,.8,.2,1) forwards; }}
    @keyframes grow {{ to {{ transform: scaleX(1); }} }}
    .col {{ opacity: 0; animation: fade .4s ease-out forwards; }}
    .flame {{ transform-box: fill-box; transform-origin: center bottom; animation: flick 1.6s ease-in-out infinite; }}
    @keyframes flick {{ 0%,100% {{ transform: scale(1); opacity: 1; }} 50% {{ transform: scale(1.08,1.12); opacity: .8; }} }}
  </style>
  <rect x="1" y="1" width="898" height="428" rx="10" fill="#120d16" stroke="#3a2229" stroke-width="2"/>
  <g stroke="#c8102e" stroke-width="3" fill="none"><path d="M14 40 V14 H40"/><path d="M860 14 H886 V40"/><path d="M14 390 V416 H40"/><path d="M886 390 V416 H860"/></g>
  <text class="t" x="450" y="40" text-anchor="middle" font-size="22" fill="#f5f0e8" letter-spacing="6">REGISTROS DO DOJO</text>
  <line x1="340" y1="52" x2="560" y2="52" stroke="#c8102e" stroke-width="2"/>
  <line x1="305" y1="80" x2="305" y2="225" stroke="#3a2229" stroke-width="2"/>
  <line x1="600" y1="80" x2="600" y2="225" stroke="#3a2229" stroke-width="2"/>
  {"".join(s)}
</svg>'''


if __name__ == "__main__":
    u = demo() if "--demo" in sys.argv else fetch()
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(render(u))
    print("ok ->", OUT)
