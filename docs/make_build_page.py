"""Turn docs/BUILD.md into docs/build-guide.html (same images, styled for reading at the bench).

    pip install markdown
    python3 docs/make_build_page.py
"""

import os
import re

import markdown

HERE = os.path.dirname(os.path.abspath(__file__))

STYLE = """
/* Layout: one reading column; each step is a heading, a full-width board image, then the actions. */
:root {
  --bg: #f5f3ee; --surface: #ffffff; --fg: #1d1f1c; --muted: #5d625a; --line: #dcd8cd;
  --accent: #a35f00; --accent-soft: #fbeccf; --code-bg: #ecebe4;
  --font-body: "IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-head: "IBM Plex Sans Condensed", "IBM Plex Sans", system-ui, sans-serif;
  --font-mono: "IBM Plex Mono", ui-monospace, Menlo, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #141613; --surface: #1c1f1b; --fg: #ecebe5; --muted: #a4a99f; --line: #33372f;
  --accent: #f4a300; --accent-soft: #3a2c10; --code-bg: #262a24; color-scheme: dark } }
:root[data-theme="dark"] {
  --bg: #141613; --surface: #1c1f1b; --fg: #ecebe5; --muted: #a4a99f; --line: #33372f;
  --accent: #f4a300; --accent-soft: #3a2c10; --code-bg: #262a24; color-scheme: dark }
body { background: var(--bg); color: var(--fg); font: 16px/1.6 var(--font-body); }
main { max-width: 820px; margin: 0 auto; padding-block: 28px 64px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }
h1, h2 { font-family: var(--font-head); text-wrap: balance; line-height: 1.2; }
h1 { font-size: 2rem; font-weight: 600; margin: 0 0 12px; }
h2 { font-size: 1.4rem; font-weight: 600; margin: 44px 0 10px; padding-top: 14px; border-top: 1px solid var(--line); }
h2:first-of-type { border-top: 0; }
p, li { max-width: 68ch; }
ul, ol { padding-left: 1.4em; }
li + li { margin-top: 4px; }
li > ul { margin-top: 4px; }
strong { font-weight: 600; }
em { font-style: normal; text-decoration: underline; text-decoration-color: var(--accent); text-underline-offset: 3px; }
hr { border: 0; height: 0; margin: 8px 0; }
code { font-family: var(--font-mono); font-size: 0.9em; background: var(--code-bg); padding: 1px 5px; border-radius: 4px; }
figure { margin: 14px 0 16px; background: #0f100e; border-radius: 10px; padding: 6px; overflow-x: auto; }
figure img { display: block; width: 100%; min-width: 560px; height: auto; }
.step-tag { display: inline-block; font-family: var(--font-mono); font-size: 0.78rem; letter-spacing: 0.04em;
  color: var(--accent); background: var(--accent-soft); border-radius: 999px; padding: 2px 10px; margin-bottom: 6px; }
.callout { background: var(--accent-soft); border-radius: 8px; padding: 10px 14px; margin: 12px 0; }
.callout p { margin: 0; }
.table-wrap { overflow-x: auto; margin: 12px 0; }
table { border-collapse: collapse; width: 100%; min-width: 440px; background: var(--surface); }
th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--line); vertical-align: top; }
th { font-weight: 600; font-size: 0.9rem; color: var(--muted); }
a { color: var(--accent); }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
"""


def build(src="BUILD.md", dst="build-guide.html", title="Tree Lights Board Build"):
    md = open(os.path.join(HERE, src)).read()
    html = markdown.markdown(md, extensions=["tables"])
    # images: own figure, not inside a <p>
    html = re.sub(r'<p><img alt="([^"]*)" src="([^"]+)" /></p>',
                  r'<figure><img alt="\1" src="\2" loading="lazy"></figure>', html)
    # "Step N." headings get a small tag above them
    html = re.sub(r"<h2>Step (\d+)\. ([^<]+)</h2>",
                  r'<h2 id="step-\1"><span class="step-tag">STEP \1</span><br>\2</h2>', html)
    # bold-led warning paragraphs become callouts
    html = re.sub(r"<p><strong>(Check:|Watch for solder bridges:|Get the polarity right:)</strong>(.*?)</p>",
                  r'<div class="callout"><p><strong>\1</strong>\2</p></div>', html, flags=re.S)
    html = html.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
    html = re.sub(r'href="BUILD\.md"', 'href="https://github.com/jrobinson-uk/treeLights/blob/master/docs/BUILD.md"', html)
    page = ('<title>%s</title>\n' % title +
            '<meta name="claude:viewport-fit-sides" content="cover">\n'
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500'
            '&family=IBM+Plex+Sans+Condensed:wght@600&family=IBM+Plex+Sans:wght@400;600&display=swap">\n'
            '<style>%s</style>\n<main>\n%s\n</main>\n' % (STYLE, html))
    out = os.path.join(HERE, dst)
    open(out, "w").write(page)
    print("wrote", out, len(page), "bytes")


if __name__ == "__main__":
    import sys
    build(*sys.argv[1:])
