#!/usr/bin/env python3
"""Render a plan document to a standalone HTML page.

    python docs/plan/render.py docs/plan/rebuild-plan.md

KNOWN CEILING: this handles the Markdown subset the plan documents use — ATX
headings, paragraphs, fenced code, bullet and ordered lists, pipe tables,
blockquotes, and inline code/bold. It is not a Markdown implementation. A
construct it does not know passes through as a paragraph, visibly wrong rather
than silently dropped, which is the behaviour to keep if this grows.
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

CSS = """
:root{--bg:#fbfbfa;--panel:#fff;--ink:#1a1a18;--ink-soft:#55554f;--ink-faint:#85857c;
--rule:#e3e3dd;--accent:#1f5f8b;--accent-soft:#eef4f8;--code-bg:#f3f3ef;
--mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace}
@media(prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#16171a;--panel:#1d1f23;
--ink:#e8e8e4;--ink-soft:#b3b3ab;--ink-faint:#85857c;--rule:#2e3137;--accent:#78b4dc;
--accent-soft:#1b2831;--code-bg:#24262b}}
:root[data-theme=dark]{--bg:#16171a;--panel:#1d1f23;--ink:#e8e8e4;--ink-soft:#b3b3ab;
--ink-faint:#85857c;--rule:#2e3137;--accent:#78b4dc;--accent-soft:#1b2831;--code-bg:#24262b}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);-webkit-font-smoothing:antialiased;
font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:880px;margin:0 auto;padding:56px 16px 120px}
h1{font-size:1.8rem;line-height:1.22;margin:0 0 26px;padding-bottom:24px;font-weight:650;
letter-spacing:-.015em;border-bottom:1px solid var(--rule)}
h2{font-size:1.22rem;margin:46px 0 16px;padding-top:22px;border-top:1px solid var(--rule);
font-weight:640;letter-spacing:-.01em}
h3{font-size:1rem;margin:30px 0 12px;font-weight:640}
p,li{color:var(--ink-soft)}p{margin:0 0 16px}
strong{color:var(--ink);font-weight:640}
ul,ol{margin:0 0 18px;padding-left:22px}li{margin-bottom:10px}
code{font:.855em/1.5 var(--mono);background:var(--code-bg);padding:.14em .36em;
border-radius:3px;color:var(--ink);word-break:break-word}
pre{background:var(--code-bg);border:1px solid var(--rule);border-radius:6px;
padding:15px 17px;overflow-x:auto;margin:0 0 20px}
pre code{background:none;padding:0;font-size:.82rem;line-height:1.6}
blockquote{margin:0 0 22px;padding:17px 20px;background:var(--accent-soft);
border-left:3px solid var(--accent);border-radius:0 5px 5px 0}
blockquote p{margin:0;color:var(--ink)}
.tablewrap{overflow-x:auto;margin:0 0 24px;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;font-size:.875rem;min-width:600px}
th,td{text-align:left;vertical-align:top;padding:11px 13px;border-bottom:1px solid var(--rule)}
th{font-size:.75rem;text-transform:uppercase;letter-spacing:.055em;color:var(--ink-faint);
font-weight:650;background:var(--code-bg)}
td{color:var(--ink-soft)}
tbody tr:hover td{background:var(--panel)}
footer{margin-top:60px;padding-top:20px;border-top:1px solid var(--rule);
font:12.5px/1.7 var(--mono);color:var(--ink-faint)}
@media(max-width:620px){.wrap{padding:36px 16px 90px}h1{font-size:1.45rem}}
"""


def inline(text: str) -> str:
    """Inline code, bold, then escape everything else."""
    slots: list[str] = []

    def hold(markup: str) -> str:
        slots.append(markup)
        return f"\x00{len(slots) - 1}\x00"

    text = re.sub(r"`([^`]+)`", lambda m: hold(f"<code>{html.escape(m[1])}</code>"), text)
    text = html.escape(text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    return re.sub(r"\x00(\d+)\x00", lambda m: slots[int(m[1])], text)


def cells(row: str) -> list[str]:
    """Split a table row on pipes, ignoring pipes inside inline code."""
    out, buf, in_code = [], "", False
    for ch in row.strip().strip("|"):
        if ch == "`":
            in_code = not in_code
        if ch == "|" and not in_code:
            out.append(buf)
            buf = ""
        else:
            buf += ch
    out.append(buf)
    return [c.strip() for c in out]


def render(md: str) -> tuple[str, str]:
    lines, body, title = md.split("\n"), [], ""
    i = 0
    while i < len(lines):
        line = lines[i]

        if line.startswith("```"):
            block, i = [], i + 1
            while i < len(lines) and not lines[i].startswith("```"):
                block.append(lines[i])
                i += 1
            body.append(f"<pre><code>{html.escape(chr(10).join(block))}</code></pre>")
            i += 1
            continue

        if m := re.match(r"^(#{1,3}) (.+)$", line):
            level, text = len(m[1]), m[2]
            if level == 1 and not title:
                title = re.sub(r"[`*]", "", text)
            body.append(f"<h{level}>{inline(text)}</h{level}>")
            i += 1
            continue

        # a pipe table: header, separator, rows
        if line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|$", lines[i + 1]):
            head = cells(line)
            i += 2
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(cells(lines[i]))
                i += 1
            th = "".join(f"<th>{inline(c)}</th>" for c in head)
            tb = "".join(
                "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows
            )
            body.append(
                f'<div class="tablewrap"><table><thead><tr>{th}</tr></thead>'
                f"<tbody>{tb}</tbody></table></div>"
            )
            continue

        if line.startswith("> "):
            quote = []
            while i < len(lines) and lines[i].startswith(">"):
                quote.append(lines[i].lstrip("> ").rstrip())
                i += 1
            body.append(f"<blockquote><p>{inline(' '.join(quote))}</p></blockquote>")
            continue

        if re.match(r"^[-*] |^\d+\. ", line):
            tag = "ul" if line[0] in "-*" else "ol"
            items: list[str] = []
            while i < len(lines) and (re.match(r"^[-*] |^\d+\. ", lines[i]) or lines[i].startswith("  ")):
                if re.match(r"^[-*] |^\d+\. ", lines[i]):
                    items.append(re.sub(r"^([-*] |\d+\. )", "", lines[i]))
                elif items:
                    items[-1] += " " + lines[i].strip()
                i += 1
            lis = "".join(f"<li>{inline(it)}</li>" for it in items)
            body.append(f"<{tag}>{lis}</{tag}>")
            continue

        if not line.strip():
            i += 1
            continue

        para = []
        while i < len(lines) and lines[i].strip() and not re.match(
            r"^(#{1,3} |[-*] |\d+\. |\||> |```)", lines[i]
        ):
            para.append(lines[i].strip())
            i += 1
        if para:
            body.append(f"<p>{inline(' '.join(para))}</p>")

    return title, "\n".join(body)


def main() -> None:
    src = Path(sys.argv[1])
    title, body = render(src.read_text())
    out = src.with_suffix(".html")
    out.write_text(
        "<!doctype html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{html.escape(title)}</title>\n<style>{CSS}</style>\n</head>\n"
        f'<body>\n<div class="wrap">\n{body}\n'
        f"<footer>Rendered from <code>{src.name}</code> by <code>render.py</code>. "
        "The Markdown file is the source.</footer>\n</div>\n</body>\n</html>\n"
    )
    print(f"{out}  ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
