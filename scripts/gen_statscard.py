#!/usr/bin/env python3
"""Generate assets/statscard.svg: a neofetch-style GitHub stats card.

Reads profile.json (GraphQL: repos+languages, contributions, followers) and
renders a terminal card: ASCII self-portrait (baked, photo is fixed) + live
stats + a language bar. Jupyter Notebook is excluded (one notebook repo skews
it; .ipynb stores rendered outputs inline). Dark/light aware, self-contained.
"""
import json, os

FACE = [
    '                       -..+..-',
    '                  #--+-#++#+-+---.',
    '                .++###########+++--+',
    '               -++####+++#++####+#+-+-',
    '                +#+#++-..-...+++##+##+',
    '                -##+--......----+####+',
    '                -##-..........---+###.',
    '                 ##...+---++#+++---+#.',
    '                 +-+.-.#++#++++-++-+#',
    '                 .-+#--+#.#-+-+--+----',
    '                 -...---...#....-.--+.-',
    '                 .-+--------+--------.',
    '                 .-+-+-+###+++++----..',
    '                  -++##++-.+#-+-----',
    '                   -++.-++++---++-++',
    '                    ++-.+------++++++###',
    '                    +#++++++##+###++++++-+###+.',
    '                ---######+++#####+++##+###+---#----',
    '          -+-------#+#+++###+#+++++###+++#--#--------',
    '       -----++---++####+++++++++++####+++++#-#--+-----',
    '     --------+---+-######++++++++######+#+#-#-+--------',
    '   ------------------###++++++++++#####+#-+--+------++-',
    '  ----+-++--+-+++--+####+++++++++######+#--++-+-+++---+',
    ' ---+++-+++++++++--#+#####++++++#####+#++++---+--++----',
    '----+++--++##++---+++#######+++######+######+++++------',
    '----+-++#+###+-+#+#+-#######+###########+###+-#----+---',
    '-#+-#+-+#+###+##++#+-##+#########++##+##+###+#+-+------',
    '-----++##-######++#+++##+++#+####+###########+---------',
    '++-+#++##### +#++++-++###+######++###++#####-#-+#------',
    '.+++#+###-    #++++++-++++######+##+#++###++#++-+-+----',
    '...................-++--.-.....................---+----',
    '..................................................+----',
    '....................................................+--',
    '---------+++--....................--------............+',
    '+++++++++++   ---.........-....+...++++++++------------',
]

EXCLUDE = {"Jupyter Notebook"}
LCOL = {"TypeScript":"#3178C6","JavaScript":"#F1E05A","C++":"#F34B7D","Python":"#3572A5",
        "QML":"#44A51C","Lua":"#9C7FE8","TeX":"#3D6117","C":"#888888","Shell":"#89E051",
        "CMake":"#DA3434","Dart":"#00B4AB","Rust":"#DEA584","Go":"#00ADD8"}

u = json.load(open(os.environ.get("PROFILE_JSON","profile.json")))["data"]["user"]
repos = u["repositories"]["nodes"]
stars = sum(r["stargazerCount"] for r in repos)
from collections import Counter
lang = Counter()
for r in repos:
    for e in r["languages"]["edges"]:
        if e["node"]["name"] in EXCLUDE: continue
        lang[e["node"]["name"]] += e["size"]
top = lang.most_common(6); tot = sum(s for _, s in top) or 1
cc = u["contributionsCollection"]
commits = cc["totalCommitContributions"]; contribs = cc["contributionCalendar"]["totalContributions"]
prs = cc["totalPullRequestContributions"]; issues = cc["totalIssueContributions"]
repocount = u["repositories"]["totalCount"]; followers = u["followers"]["totalCount"]
year = u["createdAt"][:4]
def esc(s): return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

# streaks + busiest day from the contribution calendar (same calendar.json the workflow fetches)
cur_streak = longest_streak = busiest = 0
cal_path = os.environ.get("CALENDAR_JSON", "calendar.json")
if os.path.exists(cal_path):
    cw = json.load(open(cal_path))["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = [d["contributionCount"] for w in cw for d in w["contributionDays"]]
    busiest = max(days) if days else 0
    run = 0
    for c in days:
        run = run + 1 if c > 0 else 0
        longest_streak = max(longest_streak, run)
    # current streak: trailing run, allow today (last day) to be 0
    i = len(days) - 1
    if i >= 0 and days[i] == 0: i -= 1
    while i >= 0 and days[i] > 0:
        cur_streak += 1; i -= 1

colA = [("since",f"{year} ~8 yrs"),("commits",f"{commits} / yr"),("contribs",f"{contribs:,} / yr"),("PRs",f"{prs} / yr"),("followers",str(followers))]
colB = [("repos",str(repocount)),("stars",str(stars)),("streak",f"{cur_streak} days"),("longest",f"{longest_streak} days"),("best day",f"{busiest} commits")]
FS=6.0; LH=6.2
W=900; H=max(300,int(70+len(FACE)*LH+60))

L=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="JetBrains Mono, Consolas, monospace" role="img" aria-label="github stats card">']
L.append('''  <style>
    .win{fill:#0d1117;stroke:#1a423d;} .bar{fill:#11161d;}
    .t{fill:#5b6473;font-size:12px;} .key{fill:#36e2c3;font-size:13px;font-weight:600;}
    .val{fill:#c9d1d9;font-size:13px;} .hdr{fill:#36e2c3;font-size:15px;font-weight:700;}
    .at{fill:#f0a83b;font-size:14px;font-weight:700;} .face{fill:#36e2c3;} .foc{fill:#f0a83b;font-size:12px;}
    .lg{fill:#8a93a3;font-size:11px;} .div{stroke:#1a423d;}
    @media (prefers-color-scheme:light){
      .win{fill:#ffffff;stroke:#cfe9e2;} .bar{fill:#f3f6f4;}
      .t{fill:#9aa2b0;} .key{fill:#0f9b86;} .val{fill:#1d242f;} .hdr{fill:#0f9b86;}
      .at{fill:#b45309;} .face{fill:#0f9b86;} .foc{fill:#b45309;} .lg{fill:#5b6473;} .div{stroke:#cfe9e2;}
    }
  </style>''')
L.append(f'<rect class="win" x="1" y="1" width="{W-2}" height="{H-2}" rx="12" stroke-width="1.5"/>')
L.append(f'<rect class="bar" x="1" y="1" width="{W-2}" height="34" rx="12"/>')
L.append('<rect class="bar" x="1" y="22" width="240" height="13"/>')
for i,c in enumerate(["#ff5f56","#ffbd2e","#27c93f"]): L.append(f'<circle cx="{22+i*20}" cy="18" r="6" fill="{c}"/>')
L.append('<text class="t" x="98" y="22">soyeb@github: ~/profile</text>')
L.append('<text x="24" y="58" class="val"><tspan class="at">soyeb@github</tspan>:<tspan fill="#36e2c3">~</tspan>$ git fetch --stats</text>')
y0=72
for i,ln in enumerate(FACE):
    L.append(f'<text class="face" font-size="{FS}" x="30" y="{y0+i*LH:.1f}" xml:space="preserve">{esc(ln)}</text>')
x0=300
L.append(f'<text class="hdr" x="{x0}" y="92">Soyeb Pervez Jim</text>')
L.append(f'<text class="t" x="{x0}" y="109">@soyeb-jim285  &#183;  EEE @ Univ. of Dhaka</text>')
ay=140
for i,(k,v) in enumerate(colA):
    y=ay+i*22
    L.append(f'<text class="key" x="{x0}" y="{y}">{k:<10}</text><text class="val" x="{x0+92}" y="{y}">{v}</text>')
xb=x0+300
for i,(k,v) in enumerate(colB):
    y=ay+i*22
    L.append(f'<text class="key" x="{xb}" y="{y}">{k:<8}</text><text class="val" x="{xb+72}" y="{y}">{v}</text>')
L.append(f'<text class="foc" x="{x0}" y="{ay+len(colA)*22+6}">focus: AI agents &#183; agentic workflows &#183; biosignal ML &#183; Qt/QML</text>')
L.append(f'<line class="div" x1="24" y1="{H-46}" x2="{W-24}" y2="{H-46}" stroke-width="1"/>')
bx,by,bw,bh=24,H-38,W-48,12; acc=0
for n,s in top:
    w=bw*s/tot; col=LCOL.get(n,"#36e2c3")
    L.append(f'<rect x="{bx+acc:.1f}" y="{by}" width="{max(w-1.5,1):.1f}" height="{bh}" fill="{col}" rx="2"/>'); acc+=w
cur=24; ly=H-10
for n,s in top:
    pct=100*s/tot; col=LCOL.get(n,"#36e2c3"); label=f"{n} {pct:.0f}%"
    L.append(f'<circle cx="{cur+3}" cy="{ly-4}" r="3" fill="{col}"/><text class="lg" x="{cur+10}" y="{ly}">{esc(label)}</text>')
    cur+=10+len(label)*6.3+14
L.append("</svg>")
os.makedirs("assets", exist_ok=True)
open(os.environ.get("OUT_SVG","assets/statscard.svg"),"w").write("\n".join(L))
import sys; print(f"statscard: {len(FACE)} face rows, langs {[n for n,_ in top]}", file=sys.stderr)
