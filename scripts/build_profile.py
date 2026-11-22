"""Build the Frost40 profile README and its SVGs (light + dark).

Run locally or from the weekly GitHub Action:
    python scripts/build_profile.py            # live data from the GitHub API
    python scripts/build_profile.py --offline  # baked data only

Live parts: latest public commits (terminal scene), bytes per language (flame graph),
repo count + sync date (status bar), public repo table. Everything else is fixed content below.
Big text is converted to Fraunces outlines so GitHub shows the exact font.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
import urllib.request
from pathlib import Path
from types import SimpleNamespace as NS

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
OWNER = os.environ.get("GITHUB_REPOSITORY_OWNER", "Frost40")
OFFLINE = "--offline" in sys.argv

# ---------------------------------------------------------------- tokens
PAL = {
    "light": NS(panel="#FFFDFA", ink="#1F1915", muted="#6B5F57", line="#E6DDD3", accent="#A9461F", soft="#F6E3D8", onacc="#FFFFFF",
                tbg="#211B17", tink="#F4EDE5", tmuted="#A99D93", tacc="#EC9068", tline="#3A302A"),
    "dark": NS(panel="#1D1916", ink="#F4EDE5", muted="#A99D93", line="#302824", accent="#EC9068", soft="#2E2019", onacc="#1F1915",
               tbg="#110E0C", tink="#F4EDE5", tmuted="#A99D93", tacc="#EC9068", tline="#302824"),
}
SYS = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
P, E = 6, "cubic-bezier(.4,0,.2,1)"  # one shared motion beat for the whole page

# ---------------------------------------------------------------- content (public only)
NAME = ["Flavio", "Di Lorenzo"]
TAGLINE = ("I build systems end to end: firmware for wearables and smart glasses, AI models and agents "
           "that run on one local GPU, and the apps on top. At Politecnico di Milano I research machine "
           "learning, agentic pipelines, RAG and deep learning for holography.")
LINKEDIN = "https://www.linkedin.com/in/flavio-di-lorenzo-573043295/"
DOMAINS = [
    ("Wearables", "chip", "STM32 · BLE · C", "glasses · holography"),
    ("Local AI", "wave", "speech · agents · CUDA", "PyTorch · ONNX Runtime"),
    ("Research", "ring", "ML · agents · RAG", "DL for holography"),
    ("Interfaces", "cube", "React · Nuxt · Flutter", "Vulkan · C++"),
]
SCENES = [
    ("whoami", [("cmd", "whoami"), ("out", "Flavio Di Lorenzo"), ("out", "Politecnico di Milano"), ("cmd", "ls ~/work"),
                ("dir", "wearables/   local-ai/"), ("dir", "research/    interfaces/")]),
    ("plaud", [("cmd", "# plaud-backend: 72-min meeting"), ("out", "  transcribe  whisper turbo   ✓"), ("out", "  diarize     pyannote        ✓"),
               ("out", "  notes       Obsidian vault  ✓"), ("hi", "done in 4m 50s · 2.67 GiB VRAM")]),
    ("cards", [("cmd", "# smart_scrolling: card factory"), ("out", "  1 scout    2 fetch    3 feeds"), ("out", "  4 make     5 publish  6 requests"),
               ("hi", "quality-gated cards → Supabase")]),
    ("research", [("cmd", "cat research.txt"), ("out", "Machine learning, agentic"), ("out", "pipelines and RAG systems."),
                  ("out", "Deep learning for holography"), ("out", "at Politecnico di Milano."), ("hi", "Holography details under NDA.")]),
]
SPOT = NS(repo="plaud-backend", title="Open Plaud Studio", lc="#3572A5", desc=["Local transcription and speaker", "separation into Obsidian notes"])
SMALL = [
    NS(repo="smart_scrolling", title="SmartScrolling", lang="Dart", lc="#00B4AB", d=["Learning cards instead", "of an endless feed"], m="Flutter · Supabase"),
    NS(repo="Hypermedia_Polimi_24-25", title="Soul Sanctuary", lang="Vue", lc="#41B883", d=["Nuxt 3 SSR site for", "a wellness studio"], m="9 pages · 8 APIs"),
    NS(repo="BarbieriDiLorenzo", title="Students & Companies", lang="Java", lc="#B07219", d=["Internship matching", "platform"], m="Servlets · MySQL"),
]
# curated graph rows: repo -> (year from the course name, display name, language label, colour, lane)
# lanes: 0 hardware, 1 software eng., 2 AI, 3 apps. Public repos missing here are added automatically.
CURATED = {
    "plaud-backend": ("2026", "Open Plaud Studio", "Python", "#3572A5", 2), "smart_scrolling": ("2026", "SmartScrolling", "Dart", "#00B4AB", 3),
    "SousChef_DIMA": ("2025", "SousChef", "Dart", "#00B4AB", 3), "Hypermedia_Polimi_24-25": ("2025", "Soul Sanctuary", "Vue", "#41B883", 3),
    "Fake_News_Detector": ("2025", "Fake News Detector", "Jupyter", "#DA5B0B", 2), "BarbieriDiLorenzo": ("2024", "Students & Companies", "Java", "#B07219", 1),
    "BasicRolePlay_TelegramBot": ("2024", "Role-play Telegram bot", "Python", "#3572A5", 2), "TIW-project2024": ("2024", "TIW web project", "Java", "#B07219", 1),
    "project-IS23-AM06": ("2023", "IS23 software engineering", "Java", "#B07219", 1), "Project_Reti-Logiche_2023": ("2023", "Reti Logiche", "VHDL", "#ADB2CB", 0),
    "API_Project_21-22": ("2022", "API algorithms project", "C", "#555555", 0),
}
LANE = {"C": 0, "C++": 0, "VHDL": 0, "Assembly": 0, "Java": 1, "Python": 2, "Jupyter Notebook": 2}


def history(repos):
    """Graph rows for every public repo, newest first: curated rows as written, new repos from their creation year and language."""
    rows = [CURATED.get(name) or (year, name.replace("_", " ").replace("-", " "), lang, LANGC.get(lang, LANGC["Other"]), LANE.get(lang, 3))
            for name, lang, year in repos]
    return sorted(rows, key=lambda r: -int(r[0]))


ABOUT = {
    "SousChef_DIMA": "Order-ahead cooking app: Flutter, Firebase, Stripe",
    "smart_scrolling": "Offline-first microlearning app", "Hypermedia_Polimi_24-25": "Nuxt 3 wellness studio site",
    "plaud-backend": "Local GPU transcription and diarization", "BarbieriDiLorenzo": "Internship matching platform",
    "BasicRolePlay_TelegramBot": "Telegram role-play bot", "Fake_News_Detector": "Fake news classification",
    "TIW-project2024": "Web Technologies course project", "Project_Reti-Logiche_2023": "Digital logic design in VHDL",
    "project-IS23-AM06": "Software Engineering course project", "API_Project_21-22": "Algorithms and data structures in C",
}
LANGC = {"Java": "#B07219", "Python": "#3572A5", "Dart": "#00B4AB", "JavaScript": "#F1E05A", "HTML": "#E34C26", "Vue": "#41B883",
         "CSS": "#663399", "TypeScript": "#3178C6", "C": "#555555", "VHDL": "#ADB2CB", "Jupyter Notebook": "#DA5B0B", "Other": "#8A7F77"}

# baked fallbacks (GitHub API, 2026-11-22)
BAKED = NS(
    repos=[("smart_scrolling", "Dart", "2026"), ("Hypermedia_Polimi_24-25", "Vue", "2025"), ("plaud-backend", "Python", "2026"), ("BarbieriDiLorenzo", "Java", "2024"),
           ("BasicRolePlay_TelegramBot", "Python", "2024"), ("Fake_News_Detector", "Jupyter Notebook", "2025"), ("TIW-project2024", "Java", "2024"),
           ("Project_Reti-Logiche_2023", "VHDL", "2024"), ("project-IS23-AM06", "Java", "2024"), ("API_Project_21-22", "C", "2024")],
    commits=[("026ccc4", "plaud-backend", "feat: initial public release of Open Plaud Studio"),
             ("e55994c", "smart_scrolling", "chore: initial public release under GNU AGPLv3"),
             ("498d7c7", "Hypermedia_Polimi_24-25", "docs: add bento README, MIT license, root .gitignore")],
    langs={"project-IS23-AM06": {"Java": 809342, "CSS": 917}, "BarbieriDiLorenzo": {"Java": 793746, "JavaScript": 150618, "CSS": 35853, "HTML": 16357, "Alloy": 14035},
           "TIW-project2024": {"Java": 222154, "JavaScript": 48430, "CSS": 38179, "HTML": 22972}, "smart_scrolling": {"Dart": 647467, "Python": 492805, "PLpgSQL": 59399, "HTML": 15052, "other": 5026},
           "plaud-backend": {"Python": 368340, "HTML": 124012, "PowerShell": 1356}, "BasicRolePlay_TelegramBot": {"Python": 106908},
           "Hypermedia_Polimi_24-25": {"Vue": 170655, "JavaScript": 10267, "TypeScript": 2958, "CSS": 1757}, "Fake_News_Detector": {"Jupyter Notebook": 25110},
           "API_Project_21-22": {"C": 22128, "CMake": 200}, "Project_Reti-Logiche_2023": {"VHDL": 8334}},
)

# ---------------------------------------------------------------- live data
def api(path: str):
    req = urllib.request.Request(f"https://api.github.com/{path}", headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-build"})
    if os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def load_data() -> NS:
    if OFFLINE:
        return BAKED
    try:
        raw = [r for r in api(f"users/{OWNER}/repos?type=owner&sort=pushed&per_page=100")
               if not r["private"] and not r["fork"] and r["name"].lower() != OWNER.lower()]
        repos = [(r["name"], r.get("language") or "Markdown", r["created_at"][:4]) for r in raw]
        langs = {r["name"]: api(f"repos/{OWNER}/{r['name']}/languages") for r in raw}
        commits = []
        for r in raw[:3]:  # sorted by last push
            c = api(f"repos/{OWNER}/{r['name']}/commits?per_page=1")[0]
            commits.append((c["sha"][:7], r["name"], c["commit"]["message"].splitlines()[0]))
        return NS(repos=repos, commits=commits, langs=langs)
    except Exception as e:
        if os.environ.get("GITHUB_ACTIONS"):  # in CI, fail rather than commit stale data under a fresh date
            raise
        print(f"GitHub API failed ({e}); using baked data.")
        return BAKED

# ---------------------------------------------------------------- Fraunces outlines
FONT = TTFont(ROOT / "fonts" / "Fraunces-SemiBold-opsz96.ttf")
GS, CMAP, UPM, HMTX = FONT.getGlyphSet(), FONT.getBestCmap(), FONT["head"].unitsPerEm, FONT["hmtx"]
TRACK = -0.02  # em; kerning pairs are ignored (ponytail: add GPOS kerning if a pair ever looks off)


def _glyphs(text: str):
    return [CMAP.get(ord(c)) or CMAP.get(ord("-")) for c in text]


def measure(text: str, size: float) -> float:
    return sum(HMTX[g][0] for g in _glyphs(text)) * size / UPM + TRACK * size * (len(text) - 1)


def fit(text: str, avail: float, base: float) -> float:
    return round(min(base, base * avail / measure(text, base)), 1)


def outline(text: str, x: float, y: float, size: float, fill: str, anchor: str = "start") -> str:
    if anchor == "end":
        x -= measure(text, size)
    pen, s = SVGPathPen(GS, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip(".")), size / UPM
    for g in _glyphs(text):
        GS[g].draw(TransformPen(pen, (s, 0, 0, -s, x, y)))
        x += HMTX[g][0] * s + TRACK * size
    return f'<path d="{pen.getCommands()}" fill="{fill}"/>'

# ---------------------------------------------------------------- svg helpers
def esc(s: str) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace('"', "&quot;")


def mono(size, extra=""):
    return f'font-family="{MONO}" font-size="{size}" {extra}'


def sysf(size, extra=""):
    return f'font-family="{SYS}" font-size="{size}" {extra}'


def still(sel: str) -> str:
    return "@media (prefers-reduced-motion: reduce){" + sel + "{animation:none!important}}"


def svg(w, h, label, css, body) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{esc(label)}">'
            f"<title>{esc(label)}</title><style>{css}</style>{body}</svg>")

# ---------------------------------------------------------------- hero
def hero(t):
    rings = "".join(f'<circle r="{i * 9}"/>' for i in range(1, 47))
    css = ".r{animation:r 9s %s infinite alternate}@keyframes r{from{transform:translateX(-28px)}to{transform:translateX(28px)}}" % E + still(".r")
    s = fit(NAME[1], 560, 108)
    body = (f'<defs><linearGradient id="g" x1="0" x2="1"><stop offset=".36" stop-color="#fff" stop-opacity="0"/><stop offset=".74" stop-color="#fff"/></linearGradient>'
            f'<mask id="m"><rect width="880" height="360" fill="url(#g)"/></mask><clipPath id="c"><rect width="880" height="360" rx="26"/></clipPath></defs>'
            f'<rect x=".5" y=".5" width="879" height="359" rx="26" fill="{t.panel}" stroke="{t.line}"/>'
            f'<g clip-path="url(#c)"><g mask="url(#m)"><g fill="none" stroke-width="1.3" transform="translate(700 180)">'
            f'<g stroke="{t.ink}" opacity=".42">{rings}</g><g class="r" stroke="{t.accent}" opacity=".9" transform="translate(20 0)">{rings}</g></g></g></g>'
            f"{outline(NAME[0], 46, 58 + s, s, t.ink)}{outline(NAME[1], 46, 58 + 2 * s, s, t.ink)}"
            f'<text x="50" y="318" {mono(22)} fill="{t.muted}">@Frost40 · Politecnico di Milano</text>')
    return svg(880, 360, "Flavio Di Lorenzo, @Frost40, Politecnico di Milano", css, body)

# ---------------------------------------------------------------- section stations on one vertical line
def station(t, idx, title, right, end=False):
    ny, size, h = (64, 38, 96) if end else (76, 54, 124)
    stop = (f"45%{{transform:translateY({ny - 40}px);opacity:1}}55%,100%{{transform:translateY({ny - 40}px);opacity:0}}" if end
            else "80%{opacity:1}100%{transform:translateY(130px);opacity:0}")
    css = (f".p{{animation:p {P}s {E} infinite}}@keyframes p{{0%{{transform:translateY(-50px);opacity:0}}10%{{opacity:1}}{stop}}}"
           f".n{{animation:n {P}s {E} infinite}}@keyframes n{{0%,30%,62%,100%{{opacity:.25}}44%{{opacity:1}}}}" + still(".p,.n"))
    body = (f'<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t.accent}" stop-opacity="0"/><stop offset="1" stop-color="{t.accent}"/></linearGradient></defs>'
            f'<path d="M18 0V{ny if end else h}" stroke="{t.line}" stroke-width="2"/>'
            f'<rect class="p" x="16" y="0" width="4" height="40" rx="2" fill="url(#g)" opacity="0"/>'
            f'<circle cx="18" cy="{ny}" r="10" fill="{t.panel}" stroke="{t.accent}" stroke-width="2"/><circle class="n" cx="18" cy="{ny}" r="4.5" fill="{t.accent}"/>'
            + (f'<text x="52" y="{ny - 38}" {mono(18)} fill="{t.muted}" letter-spacing="2">{idx}</text>' if idx else "")
            + outline(title, 50, ny + size * 0.34, size, t.muted if end else t.ink)
            + f'<text x="880" y="{ny + 8}" text-anchor="end" {mono(19)} fill="{t.muted}">{esc(right)}</text>')
    return svg(880, h, title, css, body)

# ---------------------------------------------------------------- glyphs that act out their domain
def glyph(kind, x, y, c, i):
    d = f"animation-delay:{i * 0.5:.1f}s"
    g = {
        "chip": (f'<rect x="8" y="8" width="24" height="24" rx="3"/><rect x="15" y="15" width="10" height="10" rx="1" fill="{c}" fill-opacity=".18"/>'
                 f'<path class="pin" style="{d}" d="M14 2v6M20 2v6M26 2v6M14 32v6M20 32v6M26 32v6M2 14h6M2 20h6M2 26h6M32 14h6M32 20h6M32 26h6"/>'),
        "wave": (f'<clipPath id="wc{i}"><rect width="40" height="40"/></clipPath><path d="M0 20h40" opacity=".3"/>'
                 f'<g clip-path="url(#wc{i})"><path class="wav" d="M-24 20 C-20 6 -16 6 -12 20 S-4 34 0 20 S8 6 12 20 S20 34 24 20 S32 6 36 20 S44 34 48 20 S56 6 60 20 S68 34 72 20"/></g>'),
        "ring": (f'<circle cx="20" cy="20" r="3.5" fill="{c}"/><circle cx="20" cy="20" r="18" opacity=".25"/>'
                 f'<circle class="wf" style="{d}" cx="20" cy="20" r="11"/><circle class="wf" style="animation-delay:{i * 0.5 + P / 2:.1f}s" cx="20" cy="20" r="11"/>'),
        "cube": (f'<path class="f1" d="M20 3 36 12 20 21 4 12Z" fill="{c}" fill-opacity=".12"/><path class="f2" d="M4 12 20 21V37L4 28Z" fill="{c}" fill-opacity=".12"/>'
                 f'<path class="f3" d="M36 12 20 21V37L36 28Z" fill="{c}" fill-opacity=".12"/>'),
    }[kind]
    return f'<g transform="translate({x} {y}) scale(1.4)" fill="none" stroke="{c}" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round">{g}</g>'


GLYPH_CSS = (f".pin{{animation:pin {P / 3}s steps(2) infinite}}@keyframes pin{{50%{{opacity:.25}}}}"
             f".wav{{animation:wav {P / 3}s linear infinite}}@keyframes wav{{to{{transform:translateX(-24px)}}}}"
             f".wf{{transform-box:fill-box;transform-origin:center;animation:wf {P}s {E} infinite}}@keyframes wf{{0%{{transform:scale(.4);opacity:1}}100%{{transform:scale(1.7);opacity:0}}}}"
             f".f1,.f2,.f3{{animation:f {P}s {E} infinite}}.f2{{animation-delay:.4s}}.f3{{animation-delay:.8s}}@keyframes f{{0%,100%{{fill-opacity:0}}20%,50%{{fill-opacity:.35}}}}"
             + still(".pin,.wav,.wf,.f1,.f2,.f3"))

# ---------------------------------------------------------------- bento: terminal + four areas
def bento(t, data):
    H, TW, x0, top, lh, cw = 560, 548, 30, 108, 40, 13.2
    git = [("cmd", "# latest public commits")]
    for sha, repo, msg in data.commits:
        git += [("dir", f"{sha} {repo}"[:34]), ("out", ("  " + msg)[:33] + ("…" if len(msg) > 31 else ""))]
    scenes = [(tab, lines + [("cmd", "")]) for tab, lines in SCENES + [("git*", git)]]
    # one global cycle: typed commands at 45 ms/char, outputs at once, 2.6 s hold per scene
    time, sched = 0.0, []
    for _, lines in scenes:
        s0, time, ls = time, time + 0.3, []
        for k, s in lines:
            typed = k == "cmd"
            d = (len(s) + 2) * 0.045 if typed else 0.01
            ls.append((time, d, typed, (len(s) + 2) * cw + 16))
            time += d + (0.35 if typed else 0.2)
        time += 2.6
        sched.append((s0, time, ls))
    C = time

    def pc(v):
        return f"{v / C * 100:.2f}"

    css, term, tabs, tabw = "", "", "", (TW - 60) / len(scenes)
    for si, (tab, lines) in enumerate(scenes):
        s0, s1, ls = sched[si]
        g = ""
        for i, (k, s) in enumerate(lines):
            y, (st, d, typed, ln) = top + i * lh, ls[i]
            col = t.tink if k == "cmd" else t.tacc if k in ("hi", "dir") else t.tmuted
            pre = f'<tspan fill="{t.tacc}">$ </tspan>' if k == "cmd" else ""
            fw = ' font-weight="700"' if k == "hi" else ""
            g += f'<text x="{x0}" y="{y}" {mono(22)} fill="{col}"{fw} xml:space="preserve">{pre}{esc(s)}</text>'
            if k == "cmd" and not s:
                g += f'<rect class="car" x="{x0 + 26}" y="{y - 21}" width="12" height="26" fill="{t.tacc}"/>'
            cl = f"c{si}_{i}"
            g += f'<rect class="cov {cl}" x="{x0 - 4}" y="{y - 27}" width="{TW}" height="{lh}" fill="{t.tbg}"/>'
            steps = -(-ln // cw) if typed else 1
            css += (f".{cl}{{animation:{cl} {C:.2f}s infinite}}@keyframes {cl}{{0%,{pc(st)}%{{transform:translateX(0);animation-timing-function:steps({int(steps)},end)}}"
                    f"{pc(st + d)}%,99.9%{{transform:translateX({ln + TW:.0f}px)}}100%{{transform:translateX(0)}}}}")
        win = (f"0%,{pc(s1)}%{{V1}}{pc(s1 + .02)}%,100%{{V0}}" if si == 0
               else f"0%,{pc(s0 - .02)}%{{V0}}{pc(s0)}%,{pc(s1)}%{{V1}}{pc(s1 + .02)}%,100%{{V0}}")
        css += (f".s{si}{{animation:s{si} {C:.2f}s infinite}}@keyframes s{si}{{{win.replace('V1', 'opacity:1').replace('V0', 'opacity:0')}}}"
                f".t{si}{{animation:t{si} {C:.2f}s infinite}}@keyframes t{si}{{{win.replace('V1', 'fill:' + t.tacc).replace('V0', 'fill:' + t.tmuted)}}}")
        term += f'<g class="s{si}" style="opacity:{1 if si == 0 else 0}">{g}</g>'
        tabs += f'<text class="t{si}" x="{30 + si * tabw:.1f}" y="{H - 28}" {mono(17)} style="fill:{t.tacc if si == 0 else t.tmuted}">{tab}</text>'
    css += ".car{animation:car 1s steps(1) infinite}@keyframes car{50%{opacity:0}}"
    css += "@media (prefers-reduced-motion: reduce){.cov{display:none}[class]{animation:none!important}}"
    rx, rw, th = TW + 14, 880 - TW - 14, (H - 36) / 4
    tiles = ""
    for i, (k, gk, l1, l2) in enumerate(DOMAINS):
        y = i * (th + 12)
        tiles += (f'<rect x="{rx + .5}" y="{y + .5}" width="{rw - 1}" height="{th - 1:.1f}" rx="20" fill="{t.panel}" stroke="{t.line}"/>'
                  + glyph(gk, rx + 22, y + th / 2 - 28, t.accent, i)
                  + outline(k, rx + 96, y + 50, fit(k, rw - 112, 28), t.ink)
                  + f'<text x="{rx + 96}" y="{y + 82}" {sysf(17)} fill="{t.muted}">{esc(l1)}</text>'
                  + f'<text x="{rx + 96}" y="{y + 106}" {sysf(17)} fill="{t.muted}">{esc(l2)}</text>')
    body = (f'<defs><clipPath id="k"><rect width="{TW}" height="{H}" rx="22"/></clipPath></defs>'
            f'<rect x=".5" y=".5" width="{TW - 1}" height="{H - 1}" rx="22" fill="{t.tbg}" stroke="{t.tline}"/>'
            f'<circle cx="32" cy="34" r="7" fill="{t.tacc}"/><circle cx="56" cy="34" r="7" fill="{t.tmuted}" opacity=".45"/><circle cx="80" cy="34" r="7" fill="{t.tmuted}" opacity=".25"/>'
            f'<text x="{TW - 28}" y="41" text-anchor="end" {mono(18)} fill="{t.tmuted}">frost40@polimi: ~</text>'
            f'<path d="M0 64H{TW}M0 {H - 62}H{TW}" stroke="{t.tline}"/>'
            f'<g clip-path="url(#k)">{term}</g>{tabs}{tiles}')
    label = ("Terminal cycling through: whoami; Open Plaud Studio importing a 72-minute meeting in 4m 50s; the SmartScrolling card pipeline; "
             "research in machine learning, agentic pipelines, RAG and holography; latest public commits. Areas: wearables, local AI, research, interfaces.")
    return svg(880, H, label, css + GLYPH_CSS, body)

# ---------------------------------------------------------------- spotlight with to-scale bars
def spotlight(t):
    bx, bw = 500, 340
    proc, vram = bw * (4 + 50 / 60) / 72, bw * 2.67 / 8  # 4m50s vs 72 min; of the RTX 3070's 8 GiB
    css = (".a,.b{transform-box:fill-box;transform-origin:left center}"
           f".a{{animation:a {P}s linear infinite}}@keyframes a{{0%{{transform:scaleX(0)}}80%,100%{{transform:scaleX(1)}}}}"
           f".b{{animation:b {P}s linear infinite}}@keyframes b{{0%{{transform:scaleX(0)}}5.33%,100%{{transform:scaleX(1)}}}}" + still(".a,.b"))
    body = (f'<rect x=".5" y=".5" width="879" height="399" rx="26" fill="{t.panel}" stroke="{t.line}"/><path d="M460 40V360" stroke="{t.line}"/>'
            f'<text x="40" y="66" {mono(18)} fill="{t.accent}" letter-spacing="2">FEATURED · OPEN SOURCE</text>'
            + outline(SPOT.title, 40, 120, fit(SPOT.title, 390, 52), t.ink)
            + f'<text x="40" y="170" {sysf(23)} fill="{t.muted}">{SPOT.desc[0]}</text><text x="40" y="202" {sysf(23)} fill="{t.muted}">{SPOT.desc[1]}</text>'
            f'<g {mono(18)} fill="{t.muted}"><text x="40" y="270">Python · Apache-2.0</text><text x="40" y="298">faster-whisper · pyannote · FastAPI</text></g>'
            f'<circle cx="47" cy="345" r="7" fill="{SPOT.lc}"/><text x="62" y="352" {mono(21)} fill="{t.ink}">{SPOT.repo} ↗</text>'
            + outline("4m 50s", bx, 88, 54, t.accent)
            + f'<text x="{bx}" y="118" {mono(18)} fill="{t.muted}">for 72 min of audio, ~15× real time</text>'
            f'<rect x="{bx}" y="138" width="{bw}" height="10" rx="5" fill="{t.line}"/><rect class="a" x="{bx}" y="138" width="{bw}" height="10" rx="5" fill="{t.muted}" opacity=".55"/>'
            f'<rect x="{bx}" y="156" width="{bw}" height="10" rx="5" fill="{t.line}" opacity=".5"/><rect class="b" x="{bx}" y="156" width="{proc:.1f}" height="10" rx="5" fill="{t.accent}"/>'
            f'<text x="{bx + bw}" y="190" text-anchor="end" {mono(15)} fill="{t.muted}">audio length · processing time</text>'
            + outline("2.67 GiB", bx, 250, 40, t.ink)
            + f'<text x="{bx}" y="278" {mono(18)} fill="{t.muted}">peak VRAM of 8 GiB · RTX 3070</text>'
            f'<rect x="{bx}" y="292" width="{bw}" height="10" rx="5" fill="{t.line}"/><rect x="{bx}" y="292" width="{vram:.1f}" height="10" rx="5" fill="{t.ink}" opacity=".7"/>'
            + outline("−4 to −7 pp", bx, 352, 34, t.ink)
            + f'<text x="{bx}" y="378" {mono(16)} fill="{t.muted}">Italian word errors vs. Plaud</text>')
    return svg(880, 400, "Open Plaud Studio: a 72-minute recording processed in 4m 50s (~15x real time), 2.67 GiB peak VRAM on an RTX 3070, "
               "4 to 7 points lower Italian word error rate than Plaud's own transcript.", css, body)


def card(t, p):
    w, h = 286, 236
    body = (f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="18" fill="none" stroke="{t.line}" stroke-width="2"/>'
            f'<circle cx="28" cy="40" r="6" fill="{p.lc}"/><text x="42" y="47" {mono(18)} fill="{t.muted}">{p.lang}</text>'
            f'<text x="{w - 24}" y="47" text-anchor="end" {mono(20)} fill="{t.muted}">↗</text>'
            + outline(p.title, 24, 98, fit(p.title, w - 48, 30), t.ink)
            + f'<text x="24" y="140" {sysf(20)} fill="{t.muted}">{esc(p.d[0])}</text><text x="24" y="166" {sysf(20)} fill="{t.muted}">{esc(p.d[1])}</text>'
            f'<text x="24" y="210" {mono(17)} fill="{t.accent}">{esc(p.m)}</text>')
    return svg(w, h, f"{p.title}: {' '.join(p.d)}", "", body)

# ---------------------------------------------------------------- extras
def git_graph(t, data):
    HISTORY = history(data.repos)
    rh, top, mx = 46, 66, 24
    H = top + len(HISTORY) * rh

    def lx(i):
        return 70 + i * 34

    lanes = ""
    for li in range(4):
        rows = [i for i, r in enumerate(HISTORY) if r[4] == li]
        if not rows:
            continue
        y0, y1 = top + rows[0] * rh - 14, top + rows[-1] * rh - 14
        # branch off main below the oldest commit, merge back into main above the newest
        lanes += (f'<path d="M{mx} {y1 + 34} C{mx} {y1 + 14} {lx(li)} {y1 + 20} {lx(li)} {y1}V{y0}'
                  f'C{lx(li)} {y0 - 20} {mx} {y0 - 14} {mx} {y0 - 34}" fill="none" stroke="{t.line}" stroke-width="2.5"/>')
    rows = ""
    for i, (yr, name, lang, c, li) in enumerate(HISTORY):
        y = top + i * rh - 14
        rows += (f'<circle cx="{lx(li)}" cy="{y}" r="7" fill="{c}" stroke="{t.panel}" stroke-width="2"/>'
                 f'<text x="230" y="{y + 6}" {mono(17)} fill="{t.muted}">{yr}</text><text x="290" y="{y + 7}" {sysf(20)} fill="{t.ink}">{esc(name)}</text>'
                 f'<text x="880" y="{y + 6}" text-anchor="end" {mono(17)} fill="{t.muted}">{lang}</text>')
    css = f".p{{animation:p {P}s {E} infinite}}@keyframes p{{0%{{transform:translateY(-60px);opacity:0}}10%,85%{{opacity:1}}100%{{transform:translateY({H}px);opacity:0}}}}" + still(".p")
    body = (f'<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t.accent}" stop-opacity="0"/><stop offset="1" stop-color="{t.accent}"/></linearGradient></defs>'
            f'<path d="M{mx} 0V{H}" stroke="{t.accent}" stroke-width="2.5" opacity=".5"/><rect class="p" x="{mx - 2}" y="0" width="4" height="50" rx="2" fill="url(#g)" opacity="0"/>'
            f'<text x="{mx + 12}" y="{top - 46}" {mono(14)} fill="{t.accent}">main</text>{lanes}{rows}')
    return svg(880, H, f"Git graph of public projects, {HISTORY[-1][0]} to {HISTORY[0][0]}: " + ", ".join(f"{r[0]} {r[1]}" for r in HISTORY), css, body)


def flame(t, data):
    by_lang: dict[str, dict[str, int]] = {}
    for repo, langs in data.langs.items():
        for lang, b in langs.items():
            by_lang.setdefault(lang, {})[repo] = b
    ranked = sorted(by_lang.items(), key=lambda kv: -sum(kv[1].values()))
    top, rest = ranked[:6], ranked[6:]
    groups = [(lang, repos) for lang, repos in top] + [("Other", {lang: sum(r.values()) for lang, r in rest})]
    total = sum(sum(r.values()) for _, r in groups)
    W, rh = 880, 44

    def lum(hexc):
        v = int(hexc[1:], 16)
        return (0.299 * (v >> 16) + 0.587 * (v >> 8 & 255) + 0.114 * (v & 255)) / 255

    def box(x, y, w, fill, op, label, txt):
        lab = f'<text x="{x + 10:.1f}" y="{y + 28}" {mono(16)} fill="{txt}">{esc(label)}</text>' if len(label) * 10.5 + 16 < w else ""
        return f'<rect x="{x + 1:.1f}" y="{y + 1}" width="{max(w - 2, 1):.1f}" height="{rh - 2}" rx="4" fill="{fill}" fill-opacity="{op}"/>{lab}'

    s = box(0, 0, W, t.accent, 1, f"all public code · {total / 1e6:.2f} MB · {len(data.langs)} repos", t.onacc)
    x = 0.0
    for lang, repos in groups:
        v = sum(repos.values())
        w, c = v / total * W, LANGC.get(lang, LANGC["Other"])
        s += box(x, rh, w, c, 0.95, f"{lang} {round(v / total * 100)}%", "#1F1915" if lum(c) > 0.55 else "#FFFFFF")
        xx = x
        for repo, b in sorted(repos.items(), key=lambda kv: -kv[1]):
            ww = b / total * W
            s += box(xx, rh * 2, ww, c, 0.45, repo.replace("_", " "), t.ink)
            xx += ww
        x += w
    s += f'<text x="880" y="{rh * 3 + 24}" text-anchor="end" {mono(14)} fill="{t.muted}">bytes per language, from the GitHub API · updated weekly</text>'
    label = "Public code by language: " + ", ".join(f"{lang} {round(sum(r.values()) / total * 100)}%" for lang, r in groups)
    return svg(880, rh * 3 + 30, label, "", s)


def status_bar(t, data, today):
    css = f".s{{transform-box:fill-box;transform-origin:center;animation:s {P}s linear infinite}}@keyframes s{{0%,80%{{transform:rotate(0)}}100%{{transform:rotate(360deg)}}}}" + still(".s")
    n = len(data.repos)
    body = (f'<rect width="880" height="44" rx="10" fill="{t.accent}"/><g {mono(16)} fill="{t.onacc}"><text x="18" y="28">⎇ main</text>'
            f'<g class="s"><path d="M176 15a8 8 0 1 1-7 4" fill="none" stroke="{t.onacc}" stroke-width="2"/><path d="M166 14l3 5 5-3" fill="none" stroke="{t.onacc}" stroke-width="2"/></g>'
            f'<text x="194" y="28">{n} public repos in sync</text><text x="862" y="28" text-anchor="end">Fraunces · UTF-8 · synced {today}</text></g>')
    return svg(880, 44, f"main branch, {n} public repositories in sync, last synced {today}", css, body)

# ---------------------------------------------------------------- README
def pic(name, alt, width="100%"):
    return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="assets/{name}-dark.svg">'
            f'<img src="assets/{name}-light.svg" alt="{esc(alt)}" width="{width}"></picture>')


def readme(data) -> str:
    rows = "\n".join(f"| [`{r}`](https://github.com/{OWNER}/{r}) | {lang} | {ABOUT.get(r, 'Public repository')} |" for r, lang, _ in data.repos)
    repo = f"https://github.com/{OWNER}"
    cards = "\n".join(f'<a href="{repo}/{p.repo}">{pic("card-" + p.repo.lower(), p.title, "32%")}</a>' for p in SMALL)
    return f"""<!-- Generated by scripts/build_profile.py. Edit the script, not this file. -->
<div align="center">

{pic("hero", "Flavio Di Lorenzo, @Frost40, Politecnico di Milano")}

</div>

{TAGLINE}

[LinkedIn]({LINKEDIN}) · [plaud-backend]({repo}/plaud-backend) · [All repositories]({repo}?tab=repositories)

<br>

{pic("station-work", "What I work on")}

{pic("bento", "Terminal and four work areas: wearables, local AI, research, interfaces")}

<br>

{pic("station-selected", "Selected work")}

<a href="{repo}/plaud-backend">{pic("spotlight", "Open Plaud Studio: 72 min of audio in 4m 50s on an RTX 3070")}</a>

<p>
{cards}
</p>

<br>

{pic("station-extras", "Extras")}

{pic("git-graph", "Git graph of public projects, 2022 to 2026")}

{pic("languages", "Public code by language")}

<details>
<summary><strong>All {len(data.repos)} public repositories</strong> · synced weekly</summary>

| Repository | Language | About |
| :--- | :--- | :--- |
{rows}

</details>

{pic("status", "Status bar: repositories in sync")}
"""

# ---------------------------------------------------------------- main
def main():
    data, today = load_data(), dt.date.today().isoformat()
    ASSETS.mkdir(exist_ok=True)
    for theme, t in PAL.items():
        files = {
            "hero": hero(t),
            "station-work": station(t, "01 / 02", "What I work on", "terminal · 4 areas"),
            "bento": bento(t, data),
            "station-selected": station(t, "02 / 02", "Selected work", "4 public projects"),
            "spotlight": spotlight(t),
            "station-extras": station(t, "", "Extras", "path · languages · every repo", end=True),
            "git-graph": git_graph(t, data),
            "languages": flame(t, data),
            "status": status_bar(t, data, today),
            **{"card-" + p.repo.lower(): card(t, p) for p in SMALL},
        }
        for name, content in files.items():
            (ASSETS / f"{name}-{theme}.svg").write_text(content, encoding="utf-8")
    (ROOT / "README.md").write_text(readme(data), encoding="utf-8")
    print(f"Built {len(files) * 2} SVGs and README.md ({len(data.repos)} repos, {'offline' if data is BAKED else 'live'} data).")


if __name__ == "__main__":
    main()
