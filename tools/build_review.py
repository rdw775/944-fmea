#!/usr/bin/env python3
"""Build a local, read-only review page from 944-fmea JSON exports.

Usage:
  python3 tools/build_review.py --rows 944-fmea.json \
      --sessions 944-fmea-sessions.json --comments 944-fmea-comments.json

Any of --rows/--sessions/--comments may be omitted if that export isn't
available yet. Output has no inputs of any kind — it cannot change S/O/D
scores. Score changes only happen in the live tool, deliberately.
"""
import argparse
import html
import json
import sys
from datetime import datetime, timezone


def esc(s):
    return html.escape(str(s), quote=True)


def rpn(s, o, d):
    if not s or not o or not d:
        return None
    return s * o * d


def ap(s, o, d):
    if not s or not o or not d:
        return "?"
    if s >= 9:
        if o >= 4:
            return "H"
        if o >= 2:
            return "H" if d >= 5 else "M"
        return "M" if d >= 7 else "L"
    if s >= 7:
        if o >= 6:
            return "H"
        if o >= 4:
            return "H" if d >= 5 else "M"
        if o >= 2:
            return "M" if d >= 7 else "L"
        return "L"
    if s >= 4:
        if o >= 7:
            return "H" if d >= 5 else "M"
        if o >= 4:
            return "M" if d >= 7 else "L"
        return "L"
    return "M" if (o >= 8 and d >= 7) else "L"


def rows_table(rows):
    if not rows:
        return '<p class="empty">No rows export provided.</p>'
    scored = sorted(rows, key=lambda r: (rpn(r.get("S"), r.get("O"), r.get("D")) or -1), reverse=True)
    out = ['<div class="wrap-table"><table><thead><tr>',
           "<th>System</th><th>Failure mode</th><th>S</th><th>O</th><th>D</th><th>RPN</th><th>AP</th>",
           "</tr></thead><tbody>"]
    for r in scored:
        s, o, d = r.get("S"), r.get("O"), r.get("D")
        n = rpn(s, o, d)
        a = ap(s, o, d)
        sev_cls = " sev-hi" if (s or 0) >= 9 else ""
        out.append(
            f'<tr class="{sev_cls}"><td>{esc(r.get("sys", ""))}</td><td>{esc(r.get("fm", ""))}</td>'
            f'<td class="n">{s if s is not None else "–"}</td><td class="n">{o if o is not None else "–"}</td>'
            f'<td class="n">{d if d is not None else "–"}</td><td class="n">{n if n is not None else "–"}</td>'
            f'<td class="n">{a}</td></tr>'
        )
    out.append("</tbody></table></div>")
    return "".join(out)


def sessions_table(sessions):
    if not sessions:
        return '<p class="empty">No sessions export provided.</p>'
    sessions = sorted(sessions, key=lambda s: s.get("ts", 0), reverse=True)
    out = []
    for s in sessions:
        entries = s.get("entries", [])
        passes = sum(1 for e in entries if e.get("status") == "pass")
        fails = sum(1 for e in entries if e.get("status") == "fail")
        unchecked = sum(1 for e in entries if e.get("status") == "unchecked")
        title = esc(s.get("date", ""))
        if s.get("note"):
            title += " — " + esc(s["note"])
        out.append(f'<div class="sess"><h3>{title}</h3>')
        out.append(f'<p class="meta">{passes} passed, {fails} failed, {unchecked} unchecked</p>')
        out.append(
            '<div class="wrap-table"><table><thead><tr>'
            "<th>System</th><th>Characteristic</th><th>Status</th><th>Note</th>"
            "</tr></thead><tbody>"
        )
        for e in entries:
            cls = " fail" if e.get("status") == "fail" else ""
            out.append(
                f'<tr class="{cls}"><td>{esc(e.get("sys", ""))}</td><td>{esc(e.get("ch", ""))}</td>'
                f'<td class="status-{esc(e.get("status", ""))}">{esc(e.get("status", ""))}</td>'
                f'<td>{esc(e.get("note", "")) or "—"}</td></tr>'
            )
        out.append("</tbody></table></div></div>")
    return "".join(out)


def comments_list(comments):
    if not comments:
        return '<p class="empty">No comments export provided.</p>'
    comments = sorted(comments, key=lambda c: c.get("ts", 0), reverse=True)
    out = []
    for c in comments:
        ts = c.get("ts")
        when = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC") if ts else ""
        out.append(
            f'<div class="citem"><b>{esc(c.get("name") or "Anonymous")}</b> '
            f'<span class="when">{esc(when)}</span>'
            f'<div class="ctext">{esc(c.get("text", ""))}</div></div>'
        )
    return "".join(out)


TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>944 Track Car — Local Review (read-only)</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700&family=Archivo+Narrow:wght@500;600;700&family=IBM+Plex+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
:root{{
  color-scheme:light only;
  --ink:#16181c; --ink-2:#4b525c; --ink-3:#7b838f;
  --rule:#c8ccd2; --rule-hard:#16181c; --paper:#f2f3f0; --card:#ffffff;
  --hi:#b3121a; --md:#c07600; --lo:#2f6b3a; --tape:#1d4ed8;
}}
*{{box-sizing:border-box}}
html{{background:#f2f3f0;color-scheme:light only}}
body{{
  margin:0;background:#f2f3f0;color:var(--ink);
  font-family:"Archivo",-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
  font-size:15px;line-height:1.5;
}}
.wrap{{max-width:1180px;margin:0 auto;padding:0 18px 90px}}
header.sheet{{border-bottom:3px solid var(--rule-hard);padding:26px 0 14px;margin-bottom:22px}}
header.sheet h1{{
  font-family:"Archivo Narrow","Archivo",sans-serif;font-weight:700;
  font-size:clamp(26px,6vw,42px);line-height:.98;letter-spacing:-.015em;margin:0 0 8px;
}}
header.sheet span{{display:block;color:var(--ink-3);font-weight:600;font-size:.44em;margin-top:6px}}
.gen{{color:var(--ink-3);font-size:13px;margin:10px 0 0}}
.banner{{border:2px solid var(--tape);background:var(--card);padding:12px 16px;font-size:13.5px;margin:18px 0 26px;color:var(--ink-2)}}
.banner b{{color:var(--tape);display:block;font-family:"Archivo Narrow",sans-serif;font-size:14.5px;margin-bottom:2px}}
h2{{
  font-family:"Archivo Narrow",sans-serif;font-size:20px;font-weight:700;
  border-bottom:2px solid var(--rule-hard);padding-bottom:6px;margin:34px 0 14px;
}}
.wrap-table{{overflow-x:auto;-webkit-overflow-scrolling:touch;border:1px solid var(--rule-hard)}}
table{{border-collapse:collapse;width:100%;min-width:680px;font-size:13px;background:var(--card)}}
th{{
  font-family:"Archivo Narrow",sans-serif;font-size:12px;text-align:left;
  background:var(--ink);color:var(--paper);padding:8px 10px;font-weight:600;
}}
td{{padding:9px 10px;border-top:1px solid var(--rule);vertical-align:top;line-height:1.4}}
td.n{{font-family:"IBM Plex Mono",monospace;font-weight:600;text-align:right;white-space:nowrap}}
tr.sev-hi td:first-child{{border-left:5px solid var(--hi)}}
tr.fail td{{background:#fff6f6}}
td.status-pass{{color:var(--lo);font-weight:600}}
td.status-fail{{color:var(--hi);font-weight:600}}
.sess{{margin-bottom:26px}}
.sess h3{{margin:0 0 2px;font-size:15px;font-family:"Archivo Narrow",sans-serif}}
.sess .meta{{font-size:12px;color:var(--ink-2);margin:0 0 8px}}
.citem{{border-top:1px solid var(--rule);padding:10px 0}}
.citem b{{font-size:13.5px}}
.citem .when{{font-size:11.5px;color:var(--ink-3);margin-left:6px}}
.citem .ctext{{margin-top:3px;white-space:pre-wrap;font-size:14px}}
.empty{{color:var(--ink-3);font-style:italic;font-size:13.5px}}
</style></head><body><div class="wrap">
<header class="sheet">
  <h1>944 Track Car<span>Local review — read-only snapshot</span></h1>
  <p class="gen">Generated {generated} from local exports.</p>
</header>
<div class="banner"><b>Read-only</b>This page has no inputs of any kind and cannot change any S/O/D score. Edit scores only in the live FMEA at the usual link, deliberately, after reviewing what's here.</div>
<h2>Current FMEA scores</h2>
{rows_html}
<h2>Banked pre-grid sessions</h2>
{sessions_html}
<h2>Comments</h2>
{comments_html}
</div></body></html>
"""


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--rows")
    p.add_argument("--sessions")
    p.add_argument("--comments")
    p.add_argument("--out", default="review.html")
    args = p.parse_args()

    rows = json.load(open(args.rows)) if args.rows else None
    sessions = json.load(open(args.sessions)) if args.sessions else None
    comments = json.load(open(args.comments)) if args.comments else None

    if not any([rows, sessions, comments]):
        sys.exit("Provide at least one of --rows, --sessions, --comments")

    html_out = TEMPLATE.format(
        generated=datetime.now().strftime("%Y-%m-%d %H:%M"),
        rows_html=rows_table(rows or []),
        sessions_html=sessions_table(sessions or []),
        comments_html=comments_list(comments or []),
    )
    with open(args.out, "w") as f:
        f.write(html_out)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
