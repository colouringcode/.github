"""Regenerate the profile banners from the studio's own fonts.

    python3 -m venv .venv && .venv/bin/pip install fonttools uharfbuzz
    FONT_DIR=/path/to/colouringcode-web/public/fonts \
        .venv/bin/python tools/build-banners.py

Type is converted to outlines with HarfBuzz, so the wordmark renders exactly
as it does on the site instead of falling back to a system face. The rose mark
is reused from profile/assets/banner-light.svg, which must exist first.
"""

import os
import pathlib
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform

ROOT = pathlib.Path(
    os.environ.get('FONT_DIR', '')
).expanduser()
OUT = pathlib.Path(__file__).resolve().parents[1] / 'profile' / 'assets'

FONTS = {
    'regular': ROOT / 'SpaceGrotesk-Regular.ttf',
    'medium': ROOT / 'SpaceGrotesk-Medium.ttf',
    'bold': ROOT / 'SpaceGrotesk-Bold.ttf',
}


class Face:
    def __init__(self, path):
        blob = hb.Blob.from_file_path(str(path))
        self.face = hb.Face(blob)
        self.font = hb.Font(self.face)
        self.upem = self.face.upem
        self.tt = TTFont(str(path))
        self.glyphs = self.tt.getGlyphSet()
        self.order = self.tt.getGlyphOrder()

    def run(self, text, size, x, y, tracking=0.0):
        """Shape `text` and return (path d, advance width, end x)."""
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.font, buf, {'kern': True, 'liga': True})

        scale = size / self.upem
        pen = SVGPathPen(self.glyphs)
        cursor = 0.0
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            name = self.order[info.codepoint]
            t = Transform(
                scale, 0, 0, -scale,
                x + cursor + pos.x_offset * scale,
                y - pos.y_offset * scale,
            )
            self.glyphs[name].draw(TransformPen(pen, t))
            cursor += pos.x_advance * scale + tracking

        return pen.getCommands(), cursor, x + cursor


if not ROOT.is_dir():
    raise SystemExit(
        'Set FONT_DIR to the site\'s public/fonts directory '
        '(colouringcode-web/public/fonts).'
    )

faces = {k: Face(v) for k, v in FONTS.items()}

# The rose, reused from the hand-built light banner.
existing = (OUT / 'banner-light.svg').read_text()
rose = existing[existing.index('<g transform="translate('):existing.index('</g>') + 4]

SANS = "'Space Grotesk', 'Helvetica Neue', Helvetica, Arial, sans-serif"


def dark_rose():
    """The site's on-dark rose: cream spikes, ink centre, cream slash.

    Only the five spikes change; the centre and the slash are already right.
    """
    chunks = rose.split('fill="#141414"')
    out = []
    for i, chunk in enumerate(chunks[:-1]):
        out.append(chunk)
        out.append('fill="#F6F1E7"' if i < 5 else 'fill="#141414"')
    out.append(chunks[-1])
    return ''.join(out)


def path(d, fill):
    return f'  <path d="{d}" fill="{fill}"/>'


def build(scheme, mobile=False):
    ink = '#141414' if scheme == 'light' else '#F6F1E7'
    muted = '#6B6760' if scheme == 'light' else '#A8A29A'
    body = '#3A3733' if scheme == 'light' else '#D6D0C4'
    bg = '#F6F1E7' if scheme == 'light' else '#141414'
    line_op = '0.14' if scheme == 'light' else '0.18'

    if mobile:
        w, h = 720, 500
        mark = (dark_rose() if scheme == 'dark' else rose).replace(
            'translate(84 118) scale(0.37)', 'translate(40 40) scale(0.19)')
        eyebrow = ('DIGITAL STUDIO · YORKSHIRE', 19, 3.8, 160, 96, muted)
        word_size, word_track, word_x, word_y = 68, -1.7, 38, 222
        sentence = [('We make websites, apps', 31, 40, 300, body),
                    ('and brands that work.', 31, 40, 344, body)]
        strap_size, strap_track, strap_x, strap_y = 20, 4.0, 40, 426
        domain = ('colouringcode.com', 21, 40, 464)
        rule = (40, 390, 680)
    else:
        w, h = 1280, 440
        mark = (dark_rose() if scheme == 'dark' else rose)
        eyebrow = ('DIGITAL STUDIO · YORKSHIRE · SINCE 2010', 16, 3.2, 320, 172, muted)
        word_size, word_track, word_x, word_y = 88, -2.2, 318, 257
        sentence = [('We make websites, apps and brands that work.', 30, 320, 318, body)]
        strap_size, strap_track, strap_x, strap_y = 16, 3.2, 320, 386
        domain = ('colouringcode.com', 18, 320, 420)
        rule = (320, 352, 1196)

    parts = []

    text, size, track, x, y, fill = eyebrow
    d, width, _ = faces['bold'].run(text, size, x, y, track)
    parts.append(path(d, fill))
    print(f'{scheme} {"mobile" if mobile else "desktop"} eyebrow width {width:.1f}')

    # Wordmark: 700 for "colouring", 500 for "code", as on the site header.
    d, _, _ = faces['bold'].run('colouring', word_size, word_x, word_y, word_track)
    parts.append(path(d, ink))
    # Measure with the trailing space so "code" starts where the site's space sits.
    _, first_width, _ = faces['bold'].run('colouring ', word_size, word_x, word_y, word_track)
    d, code_width, _ = faces['medium'].run('code', word_size, word_x + first_width, word_y, word_track)
    parts.append(path(d, ink))
    print(f'{scheme} {"mobile" if mobile else "desktop"} wordmark width {first_width + code_width:.1f}')

    for text, size, x, y, fill in sentence:
        d, width, _ = faces['regular'].run(text, size, x, y)
        parts.append(path(d, fill))
        print(f'  sentence "{text}" width {width:.1f} at {x}')

    start = strap_x
    d, prefix_width, _ = faces['bold'].run('STRAIGHT TALKING. ', strap_size, strap_x, strap_y, strap_track)
    parts.append(path(d, ink))

    full_start = strap_x + prefix_width
    d, full_width, _ = faces['bold'].run('FULL COLOUR.', strap_size, full_start, strap_y, strap_track)
    parts.append(path(d, 'url(#fullcolour)'))
    print(f'  strapline full colour x {full_start:.1f} -> {full_start + full_width:.1f}')

    text, size, x, y = domain
    d, width, _ = faces['medium'].run(text, size, x, y)
    parts.append(path(d, fill := muted))

    gradient = f'''    <linearGradient id="fullcolour" gradientUnits="userSpaceOnUse" x1="{full_start:.2f}" y1="0" x2="{full_start + full_width:.2f}" y2="0">
      <stop offset="0" stop-color="#FF5B14"/>
      <stop offset="0.25" stop-color="#FFB000"/>
      <stop offset="0.5" stop-color="#12A39A"/>
      <stop offset="0.75" stop-color="#2747C9"/>
      <stop offset="1" stop-color="#E5267A"/>
    </linearGradient>'''

    rule_line = f'  <line x1="{rule[0]}" y1="{rule[1]}" x2="{rule[2]}" y2="{rule[1]}" stroke="{ink}" stroke-opacity="{line_op}" stroke-width="1"/>'

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-labelledby="title">
  <title id="title">Colouring Code — straight talking, full colour. A digital studio in Yorkshire making websites, apps and brands that work.</title>
  <defs>
    <linearGradient id="petals" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#FF5B14"/>
      <stop offset="0.25" stop-color="#FFB000"/>
      <stop offset="0.5" stop-color="#12A39A"/>
      <stop offset="0.75" stop-color="#2747C9"/>
      <stop offset="1" stop-color="#E5267A"/>
    </linearGradient>
{gradient}
  </defs>

  <rect width="{w}" height="{h}" fill="{bg}"/>
  <rect width="{w}" height="10" fill="url(#petals)"/>

{mark}

{chr(10).join(parts)}

{rule_line}
</svg>
'''


for scheme in ('light', 'dark'):
    (OUT / f'banner-{scheme}.svg').write_text(build(scheme))
    (OUT / f'banner-mobile-{scheme}.svg').write_text(build(scheme, mobile=True))
print('written')


# --------------------------------------------------------------- disciplines --

COLOURS = ['#FF5B14', '#FFB000', '#12A39A', '#2747C9', '#E5267A']
LABELS = ['WEB', 'APPS', 'BRANDING', 'MARKETING', 'CONSULTING']


def build_disciplines(wide, scheme='light'):
    """The discipline strip: five labels across, or stacked for a phone."""
    bg = '#F6F1E7' if scheme == 'light' else '#141414'
    ink = '#141414' if scheme == 'light' else '#F6F1E7'
    parts = []

    if wide:
        w, h = 1280, 132
        centres = [128, 384, 640, 896, 1152]
        bar_y, bar_w = 40, 56
        size, track, baseline = 20, 3.4, 92
    else:
        w, h = 720, 450
        centres = None
        bar_x, bar_w = 40, 56
        size, track, baselines = 28, 3.0, [78, 162, 246, 330, 414]
        bar_ys = [34, 118, 202, 286, 370]

    for i, (label, colour) in enumerate(zip(LABELS, COLOURS)):
        if wide:
            cx = centres[i]
            parts.append(f'  <rect x="{cx - bar_w // 2}" y="{bar_y}" width="{bar_w}" height="5" fill="{colour}"/>')
            _, width, _ = faces['bold'].run(label, size, 0, 0, track)
            x = cx - width / 2
            y = baseline
        else:
            parts.append(f'  <rect x="{bar_x}" y="{bar_ys[i]}" width="{bar_w}" height="5" fill="{colour}"/>')
            x, y = bar_x, baselines[i]
        d, _, _ = faces['bold'].run(label, size, x, y, track)
        parts.append(path(d, ink))

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="Web, apps, branding, marketing and consulting">
  <rect width="{w}" height="{h}" fill="{bg}"/>

{chr(10).join(parts)}
</svg>
'''


for wide, name in ((True, 'disciplines'), (False, 'disciplines-stack')):
    for scheme in ('light', 'dark'):
        (OUT / f'{name}-{scheme}.svg').write_text(build_disciplines(wide, scheme))
print('disciplines written')
