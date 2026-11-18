"""Rebuild the PDF outline from Chromium's heading-based one with clean, nested titles.

Usage: python3 -I fix_outline.py in.pdf out.pdf "Document title" source.html
Titles are taken from the h1-h3 headings of source.html (in document order), so
CSS text-transform and badge/timecode spans don't leak into bookmark names;
page and position come from Chromium's outline.
Chromium (Playwright page.pdf(outline=True)) nests bookmarks by h1>h2>h3.
Here: the cover h1 becomes a top-level "Обложка" bookmark, h2 sections become
top-level items "N. Title (timecode)", h3 become their children.
"""
import re, sys
from pypdf import PdfReader, PdfWriter
from pypdf.generic import Fit

src, dst, doc_title, html = sys.argv[1:5]
import html as _h
HEADS = []
for tag, inner in re.findall(r'<(h[123])[^>]*>(.*?)</\1>', open(html, encoding='utf-8').read(), re.S):
    num = re.search(r'<span class="n">(.*?)</span>', inner)
    tc = re.search(r'<span class="t">(.*?)</span>', inner)
    body = re.sub(r'<span class="[nt]">.*?</span>', '', inner)
    body = _h.unescape(re.sub(r'<[^>]+>', '', body)).replace('\xa0', ' ')
    body = re.sub(r'\s+', ' ', body).replace('💰', '').strip()
    n = num.group(1) if num and num.group(1).isdigit() else None
    t = (f'{n}. ' if n else '') + body + (f' ({tc.group(1)})' if tc else '')
    HEADS.append(t)
r = PdfReader(src)
items = []  # (level, title, page, left, top)

def walk(ol, depth):
    for x in ol:
        if isinstance(x, list):
            walk(x, depth + 1)
        else:
            items.append((depth, x.title, r.get_destination_page_number(x),
                          float(x.get('/Left') or 0), float(x.get('/Top') or 0)))
walk(r.outline, 0)
assert len(items) == len(HEADS), (len(items), len(HEADS))

TC = re.compile(r'(\d{1,2}:\d{2}(?::\d{2})?)$')
def clean(title, level):
    t = re.sub(r'\s+', ' ', title.replace('\xa0', ' ')).strip()
    tc = TC.search(t)
    if tc:
        t = t[:tc.start()].strip()
    m = re.match(r'^(\d+)(?=\D)', t)
    if m:
        t = f'{m.group(1)}. ' + t[m.end():].strip()
    t = t.lstrip('★≡').strip()
    t = re.sub(r'(?<=[а-яa-z»])(?=[А-ЯA-Z])', ' ', t)   # glue fix: «персональногоИИ» -> «персонального ИИ»
    if tc and level >= 1:
        t += f' ({tc.group(1)})'
    if t.isupper() or (len(t) > 3 and t == t.upper()):
        t = t.capitalize()
    return t

w = PdfWriter(clone_from=r)
w._root_object.pop('/Outlines', None)
w.outline  # reset
parents = {}
for i, (depth, title, page, left, top) in enumerate(items):
    fit = Fit.xyz(left, top, None)
    if depth == 0:   # cover h1
        w.add_outline_item('Обложка и главная мысль', page, fit=fit)
        continue
    level = depth - 1            # h2 -> 0, h3 -> 1
    parent = parents.get(level - 1) if level > 0 else None
    node = w.add_outline_item(HEADS[i], page, parent=parent, fit=fit)
    parents[level] = node
w.page_mode = '/UseOutlines'
w.add_metadata({'/Title': doc_title})
w.write(dst)
