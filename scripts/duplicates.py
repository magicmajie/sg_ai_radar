#!/usr/bin/env python3
"""Find event files that describe the same event.

Used by build_site.py; can also run alone:  python3 scripts/duplicates.py
Exit code 1 when suspected duplicates exist.

Two files are treated as the same event when any of these hold:
  1. same registration.url (scheme, www., query, fragment, trailing slash ignored)
  2. same start time and similar titles
  3. same start date, same organizer and overlapping titles
The file that was added to the repo first is kept; the others are duplicates.
"""
from __future__ import annotations

import re
import subprocess
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent

# Words nearly every title shares; they say nothing about which event it is.
STOPWORDS = {
    "ai", "singapore", "sg", "the", "and", "a", "an", "of", "for", "in", "at", "on",
    "with", "to", "by", "x", "meetup", "event", "edition", "2025", "2026", "2027",
    "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec",
    "january", "february", "march", "april", "june", "july", "august", "september",
    "october", "november", "december",
}
HOST_ALIASES = {"lu.ma": "luma.com", "www.luma.com": "luma.com"}


def norm_url(url) -> str:
    if not url:
        return ""
    p = urlsplit(str(url).strip())
    host = p.netloc.lower()
    host = HOST_ALIASES.get(host, host)
    if host.startswith("www."):
        host = host[4:]
    return f"{host}{p.path.rstrip('/').lower()}"


def tokens(text: str) -> set[str]:
    text = str(text or "").lower()
    words = re.findall(r"[a-z0-9]+", text)
    cjk = re.findall(r"[一-鿿]", text)
    return {w for w in words if w not in STOPWORDS and not re.fullmatch(r"\d{1,2}", w)} | set(cjk)


def norm_text(text: str) -> str:
    return " ".join(sorted(tokens(text)))


def title_similarity(a, b) -> float:
    """Best match between any title variant of a and of b (0..1)."""
    best = 0.0
    for x in {a.title, a.display_title}:
        for y in {b.title, b.display_title}:
            tx, ty = tokens(x), tokens(y)
            if not tx or not ty:
                continue
            jac = len(tx & ty) / len(tx | ty)
            seq = SequenceMatcher(None, norm_text(x), norm_text(y)).ratio()
            best = max(best, jac, seq)
    return best


def organizer_key(ev) -> str:
    name = str((ev.organizer or {}).get("name") or "")
    return norm_text(name)


def same_event(a, b) -> str | None:
    """Return the reason a and b look like the same event, else None."""
    ua, ub = norm_url(a.reg.get("url")), norm_url(b.reg.get("url"))
    if ua and ua == ub:
        return "报名链接相同"
    if a.start == b.start and title_similarity(a, b) >= 0.6:
        return "开始时间相同且标题相似"
    oa, ob = organizer_key(a), organizer_key(b)
    if (a.start.date() == b.start.date() and oa and oa == ob
            and title_similarity(a, b) >= 0.5):
        return "同一天、同一组织方且标题相似"
    return None


def added_order(paths) -> dict[Path, int]:
    """Rank files by when they were first added to git (unknown/untracked = newest)."""
    first: dict[str, int] = {}
    try:
        log = subprocess.run(
            ["git", "log", "--diff-filter=A", "--format=@%ct", "--name-only", "--", "events"],
            cwd=ROOT, capture_output=True, text=True, check=True).stdout
        ts = 0
        for line in log.splitlines():
            if line.startswith("@"):
                ts = int(line[1:])
            elif line.strip():
                first[line.strip()] = ts  # log is newest-first, so the last seen wins
    except (OSError, subprocess.CalledProcessError, ValueError):
        pass
    big = 1 << 62
    return {p: first.get(str(p.relative_to(ROOT)), big) for p in paths}


def find_duplicates(events) -> list[dict]:
    """Group duplicates. Returns [{keep: Event, dups: [(Event, reason)]}]."""
    parent = list(range(len(events)))
    reasons: dict[tuple[int, int], str] = {}

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(events)):
        for j in range(i + 1, len(events)):
            r = same_event(events[i], events[j])
            if r:
                reasons[(i, j)] = r
                parent[root(j)] = root(i)

    groups: dict[int, list[int]] = {}
    for i in range(len(events)):
        groups.setdefault(root(i), []).append(i)

    order = added_order([e.path for e in events])
    result = []
    for members in groups.values():
        if len(members) < 2:
            continue
        members.sort(key=lambda k: (order[events[k].path], str(events[k].path)))
        keep = members[0]
        dups = []
        for k in members[1:]:
            pair = (min(keep, k), max(keep, k))
            reason = reasons.get(pair) or next(
                (v for (x, y), v in reasons.items() if k in (x, y)), "与同组文件相似")
            dups.append((events[k], reason))
        result.append({"keep": events[keep], "dups": dups})
    return result


def main() -> int:
    import build_site  # noqa: E402  (same directory)
    groups = find_duplicates(build_site.load_events())
    if not groups:
        print("没有发现疑似重复的活动文件。")
        return 0
    for g in groups:
        print(f"保留 {g['keep'].path.relative_to(ROOT)}")
        for ev, why in g["dups"]:
            print(f"  重复 {ev.path.relative_to(ROOT)}（{why}）")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
