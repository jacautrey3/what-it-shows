"""Render a kb .svx page to static HTML, the way the desk's runbook layout shows it.

No Node here, so this mirrors the kb's own logic in Python: causes.ts (uniqueById, causeOf,
groupByCause), desk-ref.ts (deskRef), staleness.ts and the components the page uses.
Usage: python3 -I scripts/render_page.py <page.svx> <out.html> [today YYYY-MM-DD]
"""
import collections
import datetime as dt
import glob
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'src/lib/data'
STALE_AFTER_DAYS = 180

# Intl.DateTimeFormat order for the locales on file (what dayFirst() asks the platform).
DAY_FIRST = {'en-GB': True, 'en-IE': True, 'nl-NL': True, 'cs-CZ': True, 'it-IT': True, 'fr-FR': True,
             'pl-PL': True, 'pt-PT': True, 'da-DK': True, 'de-DE': True, 'es-ES': True, 'en-US': False}
DATE_HINT = {'booking-v2': 'DD/MM/YYYY', 'booking-v3': 'MM/DD/YYYY'}


# --- causes.ts ---------------------------------------------------------------------------------
def unique_by_id(reports):
    return list({r['id']: r for r in reports}.values())


def cause_of(r, t):
    if not t or not DAY_FIRST[t['locale']]:
        return None
    return 'hint' if r['channel'] == 'form' and DATE_HINT[t['form']].startswith('MM') else 'parser'


def group_by_cause(reports, tenant_of):
    by = collections.defaultdict(list)
    for r in reports:
        by[cause_of(r, tenant_of(r)) or 'unplaced'].append(r)
    groups = []
    for cause, rs in by.items():
        days = sorted(r['receivedAt'][:10] for r in rs)
        tags = collections.Counter(r['meta']['intakeTag'] for r in rs)
        groups.append({'cause': cause, 'reports': rs, 'taggedAs': dict(tags),
                       'tenants': len({r['tenant'] for r in rs}), 'firstSeen': days[0], 'lastSeen': days[-1]})
    return sorted(groups, key=lambda g: -len(g['reports']))  # stable, like Array.sort


# --- desk-ref.ts -------------------------------------------------------------------------------
ALPHABET = '0123456789ABCDEFGHJKMNPQRSTVWXYZ'


def fnv1a(text, seed):
    h = seed & 0xFFFFFFFF
    for ch in text:
        h ^= ord(ch)
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h


def desk_ref(signature):
    t = signature.strip()
    bits = (fnv1a(t, 0x811C9DC5) << 8) | (fnv1a(t, 0x9E3779B9) & 0xFF)
    out = ''
    for _ in range(8):
        out = ALPHABET[bits & 31] + out
        bits >>= 5
    return f'DR-{out[:4]}-{out[4:]}'


# --- components --------------------------------------------------------------------------------
WHAT = {
    'parser': 'The shared parser reads the date month first; the tenant wrote it day first.',
    'hint': 'booking-v3 prints MM/DD/YYYY under the date field, then reads what people type day first.',
    'shift': 'Day and month are right; the whole date moves by one day.',
    'unplaced': 'No tenant on file, or the tenant writes the month first: not placed.',
}


def problem_table(ticket, issues):
    rows = json.loads((DATA / 'reports-4471.json').read_text())
    tenants = {t['handle']: t for t in (json.loads(Path(f).read_text()) for f in glob.glob(str(DATA / 'tenants/*.json')))}
    shifted = json.loads((DATA / 'desk-notes.json').read_text())['oneDayMove']
    merged = [r for r in unique_by_id(rows) if r['mergedInto'] == ticket]
    groups = group_by_cause(merged, lambda r: tenants.get(r['tenant']))
    rows = [(g['cause'], len(g['reports']), g, None) for g in groups]
    rows += [('shift', n, None, g['cause']) for g in groups if (n := sum(r['id'] in shifted for r in g['reports']))]
    e = html.escape
    out = [f'<p class="sum"><strong>{len(rows)}</strong> rows in the export · <strong>{len(merged)}</strong> reports once each · '
           f'<strong>{len(rows)}</strong> {"problem" if len(rows) == 1 else "problems"}</p>',
           '<table class="pt"><thead><tr><th>problem</th><th>reports</th><th>what goes wrong</th><th>tagged as</th>'
           '<th>tenants</th><th>seen</th><th>issue</th></tr></thead><tbody>']
    for cause, n, g, within in rows:
        tags = ' · '.join(f'{k} ×{v}' for k, v in sorted(g['taggedAs'].items(), key=lambda kv: -kv[1])) if g else ''
        note = f' <span class="tags">Already counted under <code>{within}</code>.</span>' if within else ''
        seen = f"{g['firstSeen']} → {g['lastSeen']}" if g else ''
        url = issues.get(cause)
        link = f'<a href="{e(url)}">#{e(url.rsplit("/", 1)[-1])}</a>' if url else '<span class="none">none yet</span>'
        out.append(f'<tr><td><code>{cause}</code></td><td><strong>{n}</strong></td><td>{e(WHAT[cause])}{note}</td>'
                   f'<td class="tags">{e(tags)}</td><td>{g["tenants"] if g else ""}</td>'
                   f'<td>{seen}</td><td>{link}</td></tr>')
    out.append('</tbody></table>')
    return '\n'.join(out), rows


def render_stamp(signature):
    if signature:
        return f'<p class="stamp">desk ref <b>{desk_ref(signature)}</b></p>'
    return '<p class="stamp missing">no desk ref: this page isn\'t signed (no <code>signature</code> in its frontmatter)</p>'


# --- markdown, as much as kb pages use ---------------------------------------------------------
def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', s)
    s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', s)
    return s


def markdown(md):
    blocks, out = re.split(r'\n\s*\n', md.strip()), []
    for b in blocks:
        lines = b.split('\n')
        if b.startswith('## '):
            out.append(f'<h2>{inline(b[3:])}</h2>')
        elif re.match(r'^(\d+\.|-) ', b):
            tag = 'ol' if b[0].isdigit() else 'ul'
            items, cur = [], []
            for ln in lines:
                if re.match(r'^(\d+\.|-) ', ln):
                    if cur:
                        items.append(' '.join(cur))
                    cur = [re.sub(r'^(\d+\.|-) ', '', ln)]
                else:
                    cur.append(ln.strip())
            items.append(' '.join(cur))
            out.append(f'<{tag}>' + ''.join(f'<li>{inline(i)}</li>' for i in items) + f'</{tag}>')
        elif b.startswith('<!--RAW'):
            out.append(b[len('<!--RAW'):-3])
        else:
            out.append(f'<p>{inline(" ".join(ln.strip() for ln in lines))}</p>')
    return '\n'.join(out)


def main(src, dst, today):
    text = Path(src).read_text()
    _, fm, body = text.split('---\n', 2)
    meta = dict(re.findall(r"^(\w+):\s*'?(.*?)'?\s*$", fm, re.M))
    script = re.search(r'<script>(.*?)</script>', body, re.S).group(1)
    body = re.sub(r'<script>.*?</script>', '', body, flags=re.S)
    repo = re.search(r"const repo = '([^']+)'", script).group(1)
    issues = {k: f'{repo}/{n}' for k, n in re.findall(r'(\w+): `\$\{repo\}/(\d+)`', script)}

    table, groups = problem_table(int(re.search(r'<ProblemTable ticket=\{(\d+)\}', body).group(1)), issues)
    raw = lambda h: f'\n\n<!--RAW{h}-->\n\n'
    body = re.sub(r'<ProblemTable[^>]*/>', lambda m: raw(table), body)
    body = re.sub(r'<Callout kind="(\w+)">\s*(.*?)\s*</Callout>',
                  lambda m: raw(f'<aside class="{m.group(1)}">{inline(" ".join(m.group(2).split()))}</aside>'), body, flags=re.S)
    body = re.sub(r'<RenderStamp \{signature\} />', lambda m: raw(render_stamp(meta.get('signature'))), body)

    reviewed = dt.date.fromisoformat(meta['reviewed'])
    age = (today - reviewed).days
    stale = age > STALE_AFTER_DAYS
    e = html.escape
    page = TEMPLATE.format(
        title=e(meta['title']), owner=e(meta['owner']), status=e(meta['status']), reviewed=reviewed.isoformat(), age=age,
        stale_cls=' class="stale"' if stale else '', stale_txt=' · stale' if stale else '',
        banner=f'<p class="banner">Nobody has re-read this page in {age} days. Check it against the live views before you rely on it.</p>' if stale else '',
        main=markdown(body))
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    Path(dst).write_text(page)
    for cause, n, g, within in groups:
        print(cause, n, g and g['taggedAs'], within or '')
    print('desk ref', desk_ref(meta.get('signature', '')))


TEMPLATE = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · support kb</title>
<style>
  :root {{ --bg: #fbfaf7; --fg: #1d1d1b; --muted: #6b6a66; --line: #e3e0d8;
    --accent: #2f6f5e; --warn: #b4501f; --warn-bg: #fbeee6; --note-bg: #eef5f2;
    --mono: ui-monospace, 'Cascadia Code', Menlo, monospace; }}
  @media (prefers-color-scheme: dark) {{ :root {{ --bg: #171716; --fg: #ecebe6; --muted: #9c9a93; --line: #34332f;
    --accent: #6fbfa6; --warn: #f0905d; --warn-bg: #3a2418; --note-bg: #1d2c27; }} }}
  body {{ margin: 0; background: var(--bg); color: var(--fg); font: 16px/1.6 system-ui, sans-serif; }}
  .kb table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; font-size: 0.92rem; }}
  .kb th, .kb td {{ border-bottom: 1px solid var(--line); padding: 0.35rem 0.5rem; text-align: left; }}
  .kb code {{ font-family: var(--mono); font-size: 0.88em; }}
  .kb a {{ color: var(--accent); }}
  .kb {{ max-width: 760px; margin: 0 auto; padding: 2rem 16px 4rem; }}
  .crumb {{ font: 0.8rem var(--mono); text-decoration: none; color: var(--muted); }}
  h1 {{ margin: 0.25rem 0 0.5rem; line-height: 1.2; }}
  .meta {{ display: flex; flex-wrap: wrap; gap: 0.5rem 1rem; color: var(--muted); font-size: 0.85rem; margin: 0; }}
  .status {{ border: 1px solid var(--line); border-radius: 99px; padding: 0 0.6rem; }}
  .stale {{ color: var(--warn); font-weight: 600; }}
  .banner {{ background: var(--warn-bg); color: var(--warn); padding: 0.6rem 1rem; border-radius: 6px; }}
  footer {{ margin-top: 3rem; color: var(--muted); font-size: 0.8rem; border-top: 1px solid var(--line); padding-top: 1rem; }}
  aside {{ border-left: 4px solid var(--accent); padding: 0.5rem 1rem; margin: 1rem 0; background: var(--note-bg); }}
  aside.warn {{ border-color: var(--warn); background: var(--warn-bg); }}
  .sum {{ font-size: 1.1rem; }}
  .tags {{ color: var(--muted); font-size: 0.85em; }}
  .none {{ color: var(--warn); font-weight: 600; }}
  table.pt {{ display: block; overflow-x: auto; }}
  .stamp {{ margin: 2rem 0 0; font: 0.85rem var(--mono); color: var(--muted); }}
  .stamp b {{ color: var(--accent); letter-spacing: 0.04em; }}
  .missing {{ color: var(--warn); }}
</style>
</head>
<body>
<div class="kb">
  <header>
    <a class="crumb" href="/kb">support desk · kb</a>
    <h1>{title}</h1>
    <p class="meta">
      <span>owner <b>{owner}</b></span>
      <span class="status {status}">{status}</span>
      <span{stale_cls}>reviewed {reviewed} · {age} days ago{stale_txt}</span>
    </p>
  </header>
  {banner}
  <main>
{main}
  </main>
  <footer>Pages are written by people. Tables and charts are built from data at render time.</footer>
</div>
</body>
</html>
'''

if __name__ == '__main__':
    today = dt.date.fromisoformat(sys.argv[3]) if len(sys.argv) > 3 else dt.date.today()
    main(sys.argv[1], sys.argv[2], today)
