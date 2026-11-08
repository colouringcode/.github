# .github

The public organisation profile for **Colouring Code**, shown at
[github.com/colouringcode](https://github.com/colouringcode).

- `profile/README.md` — the profile page itself.
- `profile/assets/` — the SVG artwork it renders: a desktop banner and a phone
  banner (light and dark), the discipline strip in wide and stacked forms, and
  the petal rule.
- `tools/build-banners.py` — regenerates the artwork.

All type is converted to outlines from the studio's own Space Grotesk files
(`SpaceGrotesk-Regular/Medium/Bold.ttf` from the site's `public/fonts`), so the
wordmark renders exactly as it does on the website — 700 for "colouring", 500
for "code" — instead of falling back to a system face. GitHub serves images
through its image proxy, which is why nothing here references a webfont.

```bash
python3 -m venv .venv && .venv/bin/pip install fonttools uharfbuzz
FONT_DIR=/path/to/colouringcode-web/public/fonts \
  .venv/bin/python tools/build-banners.py
```

Colours are the site's own — `--cc-forge` `#FF5B14`, `--cc-rose-amber`
`#FFB000`, `--cc-rose-teal` `#12A39A`, `--cc-rose-cobalt` `#2747C9`,
`--cc-rose-magenta` `#E5267A` on `--cc-surface` `#F6F1E7` and `--cc-ink`
`#141414`. The strapline "Straight talking. Full colour." carries the petal
gradient across "Full colour.", as it does on the site and the invoice.
