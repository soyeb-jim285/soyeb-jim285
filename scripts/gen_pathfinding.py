#!/usr/bin/env python3
"""Generate assets/pathfinding.svg: A* (weighted) over my contribution grid.

Reads calendar.json (GitHub GraphQL contributionCalendar) and renders an
animated SVG: gray cells light up teal as A* explores them (each day weighted
by commit count), then a gold path draws the cheapest route from my first day
to my last through my busiest days. Self-contained, dark/light aware.
"""
import json, heapq, os, sys

CAL = os.environ.get("CALENDAR_JSON", "calendar.json")
OUT = os.environ.get("OUT_SVG", "assets/pathfinding.svg")

data = json.load(open(CAL))
weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
LV = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
COLS = len(weeks); ROWS = 7
lvl = [[0] * ROWS for _ in range(COLS)]
cnt = [[0] * ROWS for _ in range(COLS)]
for c, w in enumerate(weeks):
    for day in w["contributionDays"]:
        lvl[c][day["weekday"]] = LV[day["contributionLevel"]]
        cnt[c][day["weekday"]] = day["contributionCount"]
maxc = max(max(r) for r in cnt) or 1
lastwd = weeks[-1]["contributionDays"][-1]["weekday"]
start = (0, 0); goal = (COLS - 1, lastwd)

CELL, GAP = 14, 3; PITCH = CELL + GAP; PADX = PADY = 6; CAP = 20
W = PADX * 2 + COLS * PITCH - GAP
H = PADY * 2 + ROWS * PITCH - GAP + CAP

def cost(v): return max(1, round(maxc / (v + 1)))   # busy day cheap, empty day costly
def cx(x): return PADX + x * PITCH
def cy(y): return PADY + y * PITCH

def astar():   # A* with weighted heuristic (W=10): explores less, optimal here
    Wt = 10
    def h(n): return Wt * (abs(n[0] - goal[0]) + abs(n[1] - goal[1]))
    g = {start: 0}; prev = {}; pq = [(h(start), 0, start)]; order = []; done = set()
    while pq:
        _, gc, u = heapq.heappop(pq)
        if u in done: continue
        done.add(u); order.append(u)
        if u == goal: break
        ux, uy = u
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = ux + dx, uy + dy
            if 0 <= nx < COLS and 0 <= ny < ROWS:
                ng = gc + cost(cnt[nx][ny])
                if ng < g.get((nx, ny), 1e18):
                    g[(nx, ny)] = ng; prev[(nx, ny)] = u
                    heapq.heappush(pq, (ng + h((nx, ny)), ng, (nx, ny)))
    path = []; c = goal
    while c in prev: path.append(c); c = prev[c]
    path.append(start); path.reverse()
    return order, path

order, path = astar()
M = len(order); P = len(path)
T = 13.0; EXP_END = 0.58; PATH_END = 0.80
vt = {n: EXP_END * (i / max(1, M - 1)) for i, n in enumerate(order)}
pt = {n: EXP_END + (PATH_END - EXP_END) * (i / max(1, P - 1)) for i, n in enumerate(path)}

STYLE = '''  <style>
    .g0{fill:#14181d;} .g1{fill:#2a2f37;} .g2{fill:#3d434d;} .g3{fill:#525964;} .g4{fill:#6b7480;}
    .e0{fill:#1f2733;} .e1{fill:#0e4f44;} .e2{fill:#15806f;} .e3{fill:#1fb89f;} .e4{fill:#36e2c3;}
    .path{fill:#f0a83b;} .ep{fill:#ef4d6b;}
    .cap{fill:#5b6473;font:11px JetBrains Mono,monospace;}
    @media (prefers-color-scheme:light){
      .g0{fill:#f6f8fa;} .g1{fill:#dde1e6;} .g2{fill:#c2c8d0;} .g3{fill:#a4acb6;} .g4{fill:#858f9b;}
      .e0{fill:#e9ecf0;} .e1{fill:#9be9d9;} .e2{fill:#40c9b0;} .e3{fill:#1a9c86;} .e4{fill:#0f6f60;}
      .path{fill:#b45309;} .ep{fill:#e23b59;} .cap{fill:#9aa2b0;}
    }
  </style>'''

def rect(x, y, cls, extra=""):
    return f'<rect class="{cls}" x="{cx(x)}" y="{cy(y)}" width="{CELL}" height="{CELL}" rx="3"{extra}/>'

L = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" fill="none" role="img" aria-label="A* over my contribution graph">']
L.append(STYLE)
L.append('  <g>')   # unexplored grayscale (variance by level)
for x in range(COLS):
    for y in range(ROWS): L.append('    ' + rect(x, y, f"g{lvl[x][y]}"))
L.append('  </g>')
L.append('  <g>')   # reveal: cell flips to teal contribution color when settled
for n, t in vt.items():
    if n in (start, goal): continue
    x, y = n
    L.append(f'    <rect class="e{lvl[x][y]}" x="{cx(x)}" y="{cy(y)}" width="{CELL}" height="{CELL}" rx="3" opacity="0">'
             f'<animate attributeName="opacity" values="0;1;0" keyTimes="0;{t:.4f};1" calcMode="discrete" dur="{T}s" repeatCount="indefinite"/></rect>')
L.append('  </g>')
L.append('  <g>')   # gold cheapest path
for n, t in pt.items():
    if n in (start, goal): continue
    x, y = n
    L.append(f'    <rect class="path" x="{cx(x)}" y="{cy(y)}" width="{CELL}" height="{CELL}" rx="3" opacity="0">'
             f'<animate attributeName="opacity" values="0;0;1;0" keyTimes="0;{t:.4f};{min(t + 0.004, 0.999):.4f};1" calcMode="discrete" dur="{T}s" repeatCount="indefinite"/></rect>')
L.append('  </g>')
L.append('  ' + rect(*start, "ep")); L.append('  ' + rect(*goal, "ep"))
L.append(f'  <text class="cap" x="{PADX}" y="{H - 6}">A* finds the cheapest path through my busiest days  ·  gray&#8594;teal = explored  ·  gold = path  ·  red = first/last day</text>')
L.append('</svg>')

svg = "\n".join(L)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w").write(svg)
active = sum(1 for c in range(COLS) for r in range(ROWS) if cnt[c][r] > 0)
print(f"wrote {OUT}: {COLS}x{ROWS}, explored {M}, path {P}, active days {active}, max day {maxc}", file=sys.stderr)
