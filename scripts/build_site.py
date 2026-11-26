#!/usr/bin/env python3
"""Build the Singapore AI Radar website from events/ and issues/ into _site/.

Usage: python3 scripts/build_site.py [--out _site] [--today YYYY-MM-DD]

Only depends on PyYAML. Problems in data files are printed as GitHub Actions
warnings and the file is skipped, so one bad file never takes the site down.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import re
import shutil
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from duplicates import find_duplicates  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SGT = dt.timezone(dt.timedelta(hours=8))
SITE_NAME = "Singapore AI Radar"
SITE_TAGLINE = "新加坡 AI 活动指南"
REPO_URL = "https://github.com/magicmajie/sg_ai_radar"

WEEKDAYS = "一二三四五六日"
CATEGORY = {"tech": "技术与开发", "community": "创业与社群"}
STATUS = {
    "open": "可报名", "waitlist": "候补", "full": "已满", "closed": "已截止",
    "cancelled": "已取消", "postponed": "延期", "unknown": "状态待核实",
}
FORMAT = {"offline": "线下", "online": "线上", "hybrid": "线上 + 线下"}
LANGUAGE = {"en": "英文", "zh": "中文", "mixed": "中英文"}
EVENT_TYPE = {
    "meetup": "聚会", "talk": "讲座", "workshop": "工作坊", "hackathon": "黑客松",
    "conference": "大会", "networking": "社交", "demo-day": "Demo / 路演",
    "course": "课程", "other": "其他",
}
PARTNER_ROLE = {"sponsor": "赞助", "venue": "场地", "community": "合作社区"}
PLATFORM = {"luma": "Luma", "meetup": "Meetup", "eventbrite": "Eventbrite",
            "peatix": "Peatix", "website": "官方网站", "other": "报名页面"}

warnings: list[str] = []


def warn(path: Path, msg: str) -> None:
    rel = path.relative_to(ROOT) if path.is_absolute() else path
    warnings.append(f"{rel}: {msg}")
    print(f"::warning file={rel}::{msg}", file=sys.stderr)


def esc(v) -> str:
    return html.escape("" if v is None else str(v), quote=True)


# ---------------------------------------------------------------- parsing

def split_front_matter(text: str):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    if not m:
        return None, text
    return yaml.safe_load(m.group(1)) or {}, m.group(2)


def to_dt(v):
    if v in (None, ""):
        return None
    if isinstance(v, dt.datetime):
        return v.astimezone(SGT) if v.tzinfo else v.replace(tzinfo=SGT)
    if isinstance(v, dt.date):
        return dt.datetime(v.year, v.month, v.day, tzinfo=SGT)
    try:
        d = dt.datetime.fromisoformat(str(v))
    except ValueError:
        return None
    return d.astimezone(SGT) if d.tzinfo else d.replace(tzinfo=SGT)


def to_date(v):
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    try:
        return dt.date.fromisoformat(str(v))
    except (TypeError, ValueError):
        return None


def md_inline(s: str) -> str:
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
               r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
    return s


def parse_sections(body: str) -> list[tuple[str, str]]:
    """Split the Markdown body into (heading, html) pairs on '## ' headings."""
    sections, title, lines = [], None, []

    def flush():
        if title is None and not any(l.strip() for l in lines):
            return
        sections.append((title or "", md_block("\n".join(lines))))

    for line in body.splitlines():
        if line.startswith("## "):
            flush()
            title, lines = line[3:].strip(), []
        else:
            lines.append(line)
    flush()
    return [(t, h) for t, h in sections if h]


def md_block(text: str) -> str:
    out, para, items = [], [], []

    def end_para():
        if para:
            out.append("<p>" + "<br>".join(md_inline(p) for p in para) + "</p>")
            para.clear()

    def end_list():
        if items:
            out.append("<ul>" + "".join(f"<li>{md_inline(i)}</li>" for i in items) + "</ul>")
            items.clear()

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            end_para(); end_list()
        elif re.match(r"^[-*] ", line):
            end_para(); items.append(line[2:])
        elif line.startswith("#"):
            end_para(); end_list()
            out.append(f"<h3>{md_inline(line.lstrip('#').strip())}</h3>")
        else:
            end_list(); para.append(line)
    end_para(); end_list()
    return "\n".join(out)


class Event:
    def __init__(self, path: Path, fm: dict, body: str):
        self.path, self.fm, self.body = path, fm, body
        self.id = str(fm["id"])
        self.title = str(fm.get("title") or "").strip()
        self.display_title = str(fm.get("display_title") or "").strip() or self.title
        self.category = fm.get("category") if fm.get("category") in CATEGORY else "tech"
        self.status = fm.get("status") if fm.get("status") in STATUS else "unknown"
        self.start = to_dt(fm.get("start"))
        self.end = to_dt(fm.get("end"))
        self.doors_open = to_dt(fm.get("doors_open"))
        self.venue = fm.get("venue") or {}
        self.organizer = fm.get("organizer") or {}
        self.price = fm.get("price") or {}
        self.reg = fm.get("registration") or {}
        self.card = fm.get("card") or {}
        self.labels = [str(x) for x in (fm.get("labels") or [])][:2]
        self.unverified = set(str(x) for x in (fm.get("unverified") or []))
        self.verified_at = to_date(fm.get("verified_at"))
        self.sections = parse_sections(body)

    # A field counts as unverified when listed itself or under its parent.
    def unv(self, *names: str) -> bool:
        return any(n in self.unverified or n.split(".")[0] in self.unverified for n in names)

    @property
    def finish(self):
        return self.end or (self.start + dt.timedelta(hours=3))

    def date_label(self, long=False) -> str:
        d = self.start
        if long:
            return f"{d.year}年{d.month}月{d.day}日（星期{WEEKDAYS[d.weekday()]}）"
        return f"{d.month}月{d.day}日 周{WEEKDAYS[d.weekday()]}"

    def time_label(self) -> str:
        s = self.start.strftime("%H:%M")
        if self.end and self.end.date() == self.start.date():
            s += " – " + self.end.strftime("%H:%M")
        elif self.end:
            s += f" – {self.end.month}月{self.end.day}日 {self.end.strftime('%H:%M')}"
        return s

    def organizer_label(self) -> str:
        name = str(self.organizer.get("name") or "").strip()
        if not name:
            return "待核实"
        return name + ("（待核实）" if self.unv("organizer", "organizer.name") else "")

    def venue_label(self) -> tuple[str, str]:
        if self.fm.get("format") == "online":
            return "线上活动", ""
        if self.venue.get("tba"):
            area = self.venue.get("area")
            return "报名通过后公布", (f"区域：{area}" if area else "")
        name = str(self.venue.get("name") or "").strip()
        addr = str(self.venue.get("address") or "").strip()
        if not name and not addr:
            return "待核实", ""
        if self.unv("venue", "venue.name", "venue.address"):
            name = (name or addr) + "（待核实）"
        return name or addr, (addr if name and addr != name else "")

    def price_label(self) -> str:
        t, note = self.price.get("type"), str(self.price.get("note") or "").strip()
        if self.unv("price", "price.type") or t not in ("free", "paid"):
            return "待核实"
        if t == "free":
            return f"免费（{note}）" if note else "免费"
        return note or "收费，金额见报名页"

    def language_label(self) -> str:
        lang = self.fm.get("language")
        if self.unv("language") or lang not in LANGUAGE:
            return "待核实"
        return LANGUAGE[lang]

    def registration_label(self) -> str:
        parts = []
        if self.status != "open":
            parts.append(STATUS[self.status])
        note = str(self.reg.get("note") or "").strip()
        if note:
            parts.append(note)
        elif self.reg.get("requires_approval"):
            parts.append("需报名并通过审核")
        dl = to_date(self.reg.get("deadline"))
        if dl:
            parts.append(f"截止 {dl.month}月{dl.day}日")
        return " · ".join(parts) or "可报名"


def load_events() -> list[Event]:
    events, seen = [], set()
    for path in sorted((ROOT / "events").rglob("*.md")):
        try:
            fm, body = split_front_matter(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            warn(path, f"YAML 无法解析，已跳过：{e}".replace("\n", " "))
            continue
        if not isinstance(fm, dict):
            warn(path, "缺少 YAML 开头，已跳过")
            continue
        missing = [k for k in ("id", "title", "start") if not fm.get(k)]
        if not (fm.get("registration") or {}).get("url"):
            missing.append("registration.url")
        if missing:
            warn(path, f"缺少必填字段 {', '.join(missing)}，已跳过")
            continue
        if str(fm["id"]) != path.stem:
            warn(path, f"id `{fm['id']}` 与文件名不一致")
        if fm["id"] in seen:
            warn(path, f"id `{fm['id']}` 重复，已跳过")
            continue
        ev = Event(path, fm, body)
        if not ev.start:
            warn(path, "start 不是合法时间，已跳过")
            continue
        if not str(ev.organizer.get("name") or "").strip():
            warn(path, "organizer.name 为空（必填）")
        seen.add(ev.id)
        events.append(ev)
    events.sort(key=lambda e: (e.start, e.id))
    return events


def load_issues(event_ids: set[str]) -> list[dict]:
    issues = []
    for path in sorted((ROOT / "issues").glob("*/issue.md"), reverse=True):
        try:
            fm, body = split_front_matter(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            warn(path, f"YAML 无法解析，已跳过：{e}".replace("\n", " "))
            continue
        if not isinstance(fm, dict) or fm.get("status") != "published":
            continue
        img_dir = path.parent / "images"
        images = [i for i in (fm.get("images") or []) if (img_dir / i).is_file()]
        for i in fm.get("images") or []:
            if not (img_dir / i).is_file():
                warn(path, f"images 中的 {i} 不存在")
        for eid in fm.get("events") or []:
            if eid not in event_ids:
                warn(path, f"events 中的 {eid} 没有对应的活动文件")
        issues.append({
            "id": str(fm.get("id") or path.parent.name),
            "dir": path.parent,
            "start": to_date(fm.get("period_start")),
            "end": to_date(fm.get("period_end")),
            "events": [str(e) for e in (fm.get("events") or [])],
            "images": images,
        })
    return issues


# ---------------------------------------------------------------- rendering

ICONS = {  # Lucide (https://lucide.dev), ISC license
    "building": '<path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z"/><path d="M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2"/><path d="M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2"/><path d="M10 6h4"/><path d="M10 10h4"/><path d="M10 14h4"/><path d="M10 18h4"/>',
    "calendar": '<path d="M8 2v4"/><path d="M16 2v4"/><rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    "pin": '<path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0"/><circle cx="12" cy="10" r="3"/>',
    "banknote": '<rect width="20" height="12" x="2" y="6" rx="2"/><circle cx="12" cy="12" r="2"/><path d="M6 12h.01M18 12h.01"/>',
    "ticket": '<path d="M2 9a3 3 0 0 1 0 6v2a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-2a3 3 0 0 1 0-6V7a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z"/><path d="M13 5v2"/><path d="M13 17v2"/><path d="M13 11v2"/>',
    "languages": '<path d="m5 8 6 6"/><path d="m4 14 6-6 2-3"/><path d="M2 5h12"/><path d="M7 2h1"/><path d="m22 22-5-10-5 10"/><path d="M14 18h6"/>',
    "external": '<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h3"/>',
    "arrow-left": '<path d="m12 19-7-7 7-7"/><path d="M19 12H5"/>',
    "calendar-plus": '<path d="M8 2v4"/><path d="M16 2v4"/><path d="M21 13V6a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h8"/><path d="M3 10h18"/><path d="M16 19h6"/><path d="M19 16v6"/>',
}


def icon(name: str, cls: str = "icon") -> str:
    return (f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            f'{ICONS[name]}</svg>')


def dim(text: str) -> str:
    """Wrap '待核实' parts in a muted span."""
    t = esc(text)
    return t.replace("待核实", '<span class="unv">待核实</span>')


def page(title: str, body: str, depth: int, desc: str = "", today: dt.date | None = None) -> str:
    base = "../" * depth
    full_title = f"{title}｜{SITE_NAME}" if title else f"{SITE_NAME}｜{SITE_TAGLINE}"
    desc = desc or "每周整理新加坡的 AI Meetup、Workshop、黑客松和讲座，附官方报名链接。"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="{esc(desc)}">
<meta name="theme-color" content="#101A35">
<link rel="icon" href="{base}assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{base}assets/style.css">
</head>
<body>
<header class="topbar">
  <div class="wrap topbar-inner">
    <a class="brand" href="{base}index.html"><span class="brand-dot"></span><span class="brand-sg">Singapore </span>AI Radar</a>
    <nav class="nav">
      <a href="{base}index.html">近期活动</a>
      <a href="{base}past/index.html">往期</a>
      <a href="{base}issues/index.html">每期指南</a>
    </nav>
  </div>
</header>
{body}
<footer class="footer">
  <div class="wrap">
    <p><strong>{SITE_NAME}</strong> · {SITE_TAGLINE}</p>
    <p>信息整理自各活动的官方页面，时间、地点、费用和名额可能变化，<strong>报名前请以官方页面为准</strong>。标注“待核实”的信息还没有得到官方确认。</p>
    <p class="muted">本站只做信息整理，与各活动主办方无关。{f"页面生成于 {today.year}年{today.month}月{today.day}日。" if today else ""}</p>
  </div>
</footer>
<script src="{base}assets/app.js" defer></script>
</body>
</html>
"""


def badge_html(ev: Event) -> str:
    out = f'<span class="cat cat-{ev.category}">{CATEGORY[ev.category]}</span>'
    if ev.status != "open":
        out += f'<span class="status status-{ev.status}">{STATUS[ev.status]}</span>'
    return out


def event_row(ev: Event, base: str) -> str:
    venue, _ = ev.venue_label()
    labels = "".join(f'<span class="tag">{esc(l)}</span>' for l in ev.labels)
    return f"""<a class="ev ev-{ev.category}{' ev-dim' if ev.status in ('cancelled', 'closed', 'full') else ''}" href="{base}e/{esc(ev.id)}/index.html" data-cat="{ev.category}">
  <div class="ev-time">{esc(ev.start.strftime('%H:%M'))}</div>
  <div class="ev-main">
    <div class="ev-badges">{badge_html(ev)}</div>
    <h3 class="ev-title">{esc(ev.display_title)}</h3>
    <div class="ev-meta">
      <span>{icon('building', 'icon sm')}{dim(ev.organizer_label())}</span>
      <span>{icon('pin', 'icon sm')}{dim(venue)}</span>
      <span>{icon('banknote', 'icon sm')}{dim(ev.price_label())}</span>
    </div>
    {f'<div class="tags">{labels}</div>' if labels else ''}
  </div>
</a>"""


def grouped_list(events: list[Event], base: str, newest_first=False) -> str:
    days: dict[dt.date, list[Event]] = {}
    for ev in events:
        days.setdefault(ev.start.date(), []).append(ev)
    keys = sorted(days, reverse=newest_first)
    out = []
    for d in keys:
        out.append(f"""<section class="day" data-day>
  <h2 class="day-head"><span class="day-date">{d.month}月{d.day}日</span><span class="day-wd">星期{WEEKDAYS[d.weekday()]}</span><span class="day-n">{len(days[d])} 场</span></h2>
  <div class="day-list">{''.join(event_row(e, base) for e in days[d])}</div>
</section>""")
    return "\n".join(out)


def render_index(upcoming: list[Event], today: dt.date) -> str:
    n_tech = sum(e.category == "tech" for e in upcoming)
    n_comm = len(upcoming) - n_tech
    if upcoming:
        last = max(e.start.date() for e in upcoming)
        span = f"{today.month}月{today.day}日 – {last.month}月{last.day}日"
    else:
        span = ""
    listing = grouped_list(upcoming, "") if upcoming else (
        '<div class="empty">近期还没有收录的活动，每周一更新。</div>')
    body = f"""<main>
<section class="hero">
  <div class="wrap">
    <p class="eyebrow">Singapore AI Events Guide</p>
    <h1>新加坡 AI 活动指南</h1>
    <p class="lead">每周一更新：Meetup、Workshop、黑客松和讲座，附官方报名链接。</p>
    <div class="stats">
      <div><b>{len(upcoming)}</b><span>场近期活动</span></div>
      <div><b>{n_tech}</b><span>技术与开发</span></div>
      <div><b>{n_comm}</b><span>创业与社群</span></div>
    </div>
    {f'<p class="span">{span}</p>' if span else ''}
  </div>
</section>
<div class="wrap">
  <div class="filters" role="group" aria-label="按类别筛选">
    <button class="chip is-on" data-filter="all">全部 <i>{len(upcoming)}</i></button>
    <button class="chip" data-filter="tech">技术与开发 <i>{n_tech}</i></button>
    <button class="chip" data-filter="community">创业与社群 <i>{n_comm}</i></button>
  </div>
  <div class="days">{listing}</div>
  <p class="filter-empty" hidden>这个类别暂时没有活动。</p>
</div>
</main>"""
    return page("", body, 0, today=today)


def ics_text(ev: Event) -> str:
    def f(d: dt.datetime) -> str:
        return d.astimezone(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    def fold(s: str) -> str:
        return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

    venue, addr = ev.venue_label()
    loc = ", ".join(x for x in (venue, addr) if x)
    return "\r\n".join([
        "BEGIN:VCALENDAR", "VERSION:2.0", f"PRODID:-//{SITE_NAME}//ZH", "CALSCALE:GREGORIAN",
        "BEGIN:VEVENT",
        f"UID:{ev.id}@sg-ai-radar",
        f"DTSTAMP:{f(dt.datetime.now(dt.timezone.utc))}",
        f"DTSTART:{f(ev.start)}",
        f"DTEND:{f(ev.finish)}",
        f"SUMMARY:{fold(ev.display_title)}",
        f"LOCATION:{fold(loc)}",
        f"DESCRIPTION:{fold('报名：' + str(ev.reg.get('url')) + chr(10) + '信息以官方页面为准。')}",
        f"URL:{ev.reg.get('url')}",
        "END:VEVENT", "END:VCALENDAR", "",
    ])


def render_event(ev: Event, today: dt.date) -> str:
    base = "../../"
    venue, addr = ev.venue_label()
    time = ev.time_label()
    if ev.doors_open:
        time += f"（{ev.doors_open.strftime('%H:%M')} 入场）"
    if ev.unv("end") and ev.end:
        time += "（结束时间待核实）"
    if ev.unv("start"):
        time += "（待核实）"
    maps = ""
    if addr and not ev.venue.get("tba"):
        q = re.sub(r"\s+", "+", addr)
        maps = f' <a class="maplink" href="https://www.google.com/maps/search/?api=1&amp;query={esc(q)}" target="_blank" rel="noopener">地图</a>'
    rows = [
        ("building", "组织方", dim(ev.organizer_label())),
        ("calendar", "日期", esc(ev.date_label(long=True))),
        ("clock", "时间", dim(time)),
        ("pin", "地点", dim(venue) + (f'<small>{esc(addr)}{maps}</small>' if addr else "")),
        ("banknote", "费用", dim(ev.price_label())),
        ("ticket", "报名", dim(ev.registration_label())),
        ("languages", "语言", dim(ev.language_label())),
    ]
    info = "".join(f'<div class="row">{icon(i)}<dt>{k}</dt><dd>{v}</dd></div>' for i, k, v in rows)

    card_items = [("目标参与人群", ev.card.get("audience")), ("主要交流主题", ev.card.get("theme")),
                  ("活动形式与亮点", ev.card.get("highlights"))]
    card = "".join(f"<div><h3>{k}</h3><p>{esc(v)}</p></div>" for k, v in card_items if v)
    sections = "".join(f'<section class="prose">{f"<h2>{esc(t)}</h2>" if t else ""}{h}</section>'
                       for t, h in ev.sections)

    extra = []
    etype = EVENT_TYPE.get(ev.fm.get("event_type"))
    fmt = FORMAT.get(ev.fm.get("format"))
    if etype or fmt:
        extra.append(("形式", " · ".join(x for x in (fmt, etype) if x)))
    partners = ev.fm.get("partners") or []
    if partners:
        extra.append(("合作方", "、".join(
            f"{p.get('name')}（{PARTNER_ROLE.get(p.get('role'), '合作')}）" for p in partners if p.get("name"))))
    speakers = ev.fm.get("speakers") or []
    if speakers:
        extra.append(("主讲人", "、".join(str(s) for s in speakers)))
    extra_html = "".join(f"<div><dt>{k}</dt><dd>{esc(v)}</dd></div>" for k, v in extra)

    platform = PLATFORM.get(ev.reg.get("platform"), "报名页面")
    is_past = ev.finish.date() < today
    cta_label = "查看活动页面" if is_past or ev.status in ("cancelled", "closed") else f"去 {platform} 报名"
    subtitle = ev.fm.get("subtitle")
    orig = f'<p class="orig">官方标题：{esc(ev.title)}</p>' if ev.title != ev.display_title else ""
    verified = (f"信息于 {ev.verified_at.year}年{ev.verified_at.month}月{ev.verified_at.day}日 核对官方页面"
                if ev.verified_at else "")
    past_note = '<div class="notice">这场活动已经结束。</div>' if is_past else ""

    body = f"""<main class="wrap detail">
  <a class="back" href="{base}index.html">{icon('arrow-left', 'icon sm')}近期活动</a>
  {past_note}
  <div class="ev-badges">{badge_html(ev)}</div>
  <h1>{esc(ev.display_title)}</h1>
  {f'<p class="subtitle">{esc(subtitle)}</p>' if subtitle else ''}
  {orig}
  <dl class="info">{info}</dl>
  <div class="actions">
    <a class="btn primary" href="{esc(ev.reg.get('url'))}" target="_blank" rel="noopener">{cta_label}{icon('external', 'icon sm')}</a>
    {'' if is_past else f'<a class="btn" href="event.ics" download="{esc(ev.id)}.ics">{icon("calendar-plus", "icon sm")}加入日历</a>'}
  </div>
  {f'<div class="card-grid">{card}</div>' if card else ''}
  {sections}
  {f'<dl class="extra">{extra_html}</dl>' if extra_html else ''}
  <p class="verified">{esc(verified)}。时间、地点和名额可能变化，请以<a href="{esc(ev.reg.get('url'))}" target="_blank" rel="noopener">官方页面</a>为准。</p>
</main>"""
    desc = f"{ev.date_label()} {ev.start.strftime('%H:%M')} · {venue} · {ev.organizer_label()}"
    return page(ev.display_title, body, 2, desc=desc, today=today)


def render_past(past: list[Event], today: dt.date) -> str:
    listing = grouped_list(past, "../", newest_first=True) if past else '<div class="empty">还没有往期活动。</div>'
    body = f"""<main class="wrap">
  <div class="page-head"><h1>往期活动</h1><p class="muted">已经结束的活动，按时间倒序。</p></div>
  <div class="days">{listing}</div>
</main>"""
    return page("往期活动", body, 1, today=today)


def render_issues_index(issues: list[dict], today: dt.date) -> str:
    if issues:
        items = "".join(
            f'<a class="issue" href="{esc(i["id"])}/index.html">'
            f'{f"""<img src="{esc(i["id"])}/{esc(i["images"][0])}" alt="" loading="lazy">""" if i["images"] else ""}'
            f'<div><h3>{esc(i["id"])} 期</h3><p>{esc(fmt_range(i))} · {len(i["events"])} 场活动</p></div></a>'
            for i in issues)
    else:
        items = '<div class="empty">还没有发布的指南。</div>'
    body = f"""<main class="wrap">
  <div class="page-head"><h1>每期指南</h1><p class="muted">每周一发布在小红书的活动指南图片。图片是发布当时的快照，最新信息以活动详情页为准。</p></div>
  <div class="issues">{items}</div>
</main>"""
    return page("每期指南", body, 1, today=today)


def fmt_range(i: dict) -> str:
    s, e = i["start"], i["end"]
    if not s or not e:
        return ""
    return f"{s.month}月{s.day}日 – {e.month}月{e.day}日"


def render_issue(i: dict, by_id: dict, alias: dict, today: dt.date) -> str:
    imgs = "".join(f'<img src="{esc(n)}" alt="第 {k} 页" loading="lazy">' for k, n in enumerate(i["images"], 1))
    evs = []
    for e in i["events"]:
        ev = by_id.get(alias.get(e, e))
        if ev and ev not in evs:
            evs.append(ev)
    body = f"""<main class="wrap">
  <a class="back" href="../index.html">{icon('arrow-left', 'icon sm')}每期指南</a>
  <div class="page-head"><h1>{esc(i['id'])} 期</h1><p class="muted">{esc(fmt_range(i))} · {len(i['events'])} 场活动。图片是发布当时的快照，最新信息请点进活动查看。</p></div>
  {f'<div class="gallery">{imgs}</div>' if imgs else ''}
  <h2 class="section-title">本期活动</h2>
  <div class="days">{grouped_list(evs, "../../")}</div>
</main>"""
    return page(f"{i['id']} 期", body, 2, today=today)


def render_redirect(target_id: str) -> str:
    url = f"../{esc(target_id)}/index.html"
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta http-equiv="refresh" content="0; url={url}">
<link rel="canonical" href="{url}">
<title>{SITE_NAME}</title></head>
<body><p>这个活动的信息已合并，正在跳转：<a href="{url}">{url}</a></p></body></html>
"""


# ---------------------------------------------------------------- main

def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "_site"))
    ap.add_argument("--today", help="override today's date (YYYY-MM-DD, SGT)")
    args = ap.parse_args()

    now = dt.datetime.now(SGT)
    today = dt.date.fromisoformat(args.today) if args.today else now.date()
    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)

    events = load_events()
    alias: dict[str, str] = {}  # duplicate id -> id of the file that is kept
    for g in find_duplicates(events):
        keep = g["keep"]
        for ev, why in g["dups"]:
            alias[ev.id] = keep.id
            warn(ev.path, f"疑似与 {keep.path.relative_to(ROOT)} 是同一场活动（{why}）。"
                          f"网站只显示较早的文件，请把信息合并进去后删除本文件")
    events = [e for e in events if e.id not in alias]
    hidden = sorted(alias)
    for ev in events:  # files already merged and deleted keep redirecting
        for old in ev.fm.get("merged_from") or []:
            old = str(old)
            if old in alias or any(e.id == old for e in events):
                warn(ev.path, f"merged_from 中的 {old} 仍有活动文件，请删除该文件")
            alias.setdefault(old, ev.id)
    all_ids = {e.id for e in events} | set(alias)
    by_id = {e.id: e for e in events}
    issues = load_issues(all_ids)

    visible = [e for e in events if e.status != "cancelled"]
    upcoming = [e for e in visible if e.finish.date() >= today]
    past = [e for e in visible if e.finish.date() < today]

    shutil.copytree(ROOT / "site", out / "assets")
    write(out / "index.html", render_index(upcoming, today))
    write(out / "past" / "index.html", render_past(past, today))
    for ev in events:
        write(out / "e" / ev.id / "index.html", render_event(ev, today))
        write(out / "e" / ev.id / "event.ics", ics_text(ev))
    for dup_id, keep_id in alias.items():
        write(out / "e" / dup_id / "index.html", render_redirect(keep_id))
    write(out / "issues" / "index.html", render_issues_index(issues, today))
    for i in issues:
        write(out / "issues" / i["id"] / "index.html", render_issue(i, by_id, alias, today))
        for name in i["images"]:
            shutil.copy2(i["dir"] / "images" / name, out / "issues" / i["id"] / name)
    write(out / ".nojekyll", "")

    if hidden:
        print(f"{len(hidden)} duplicate event file(s) hidden: " + ", ".join(hidden))
    print(f"Built {len(events)} events ({len(upcoming)} upcoming, {len(past)} past), "
          f"{len(issues)} published issues -> {out}")
    if warnings:
        print(f"{len(warnings)} warning(s):")
        for w in warnings:
            print("  - " + w)
    return 0


if __name__ == "__main__":
    sys.exit(main())
