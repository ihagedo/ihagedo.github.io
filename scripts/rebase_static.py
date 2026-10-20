# File:        rebase_static.py
# Author:      Isaac Hagedorn
# Date:        2026-10-20
# Description: Points a built static site's root paths to its public/ files (/img/a.jpg) at the subfolder it is served from, and adds a noindex tag to every page. Used for sites whose code assumes they are served from /.
import argparse
import pathlib
import re
import urllib.parse

TEXT = {'.html', '.js', '.mjs', '.json', '.css', '.webmanifest'}
NOINDEX = '<meta name="robots" content="noindex, nofollow">'

ap = argparse.ArgumentParser()
ap.add_argument('public', type=pathlib.Path)
ap.add_argument('out', type=pathlib.Path)
ap.add_argument('base')
args = ap.parse_args()

names = {p.relative_to(args.public).as_posix() for p in args.public.rglob('*') if p.is_file()}
variants = sorted({v for n in names for v in (n, urllib.parse.quote(n))}, key=len, reverse=True)
base = '/' + args.base.strip('/') + '/'
# one pass per way a slash can be written: plain, JSON-escaped and unicode-escaped (Nuxt payloads)
passes = []
for sep in ('/', '\\/', '\\u002F'):
    alts = '|'.join(re.escape(v.replace('/', sep)) for v in variants)
    s_ = re.escape(sep)
    passes.append((re.compile(r'(?<![\w.%/-])(' + s_ + r'public)?' + s_ + '(' + alts + r')(?![\w.%-])'), base.replace('/', sep)))

changed = 0
for f in args.out.rglob('*'):
    if not f.is_file() or f.suffix not in TEXT:
        continue
    text = f.read_text(encoding='utf-8')
    new = text
    for pattern, b in passes:
        new = pattern.sub(lambda m: (m.group(1) or '') + b + m.group(2), new)
    if f.suffix == '.html' and NOINDEX not in new:
        new = new.replace('<head>', '<head>' + NOINDEX, 1)
    if new != text:
        f.write_text(new, encoding='utf-8')
        changed += 1
print(f'rebase_static: {len(names)} public files, {changed} output files changed')
