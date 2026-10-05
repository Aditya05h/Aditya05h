"""Map the supplied portrait to an animated SVG character grid (requires Pillow).

The PNG is read only; the output is real text in a self-contained SVG.
Run once when changing the photo, not in the daily workflow.
"""
from html import escape
from pathlib import Path
from PIL import Image, ImageOps, ImageFilter

ROOT = Path(__file__).resolve().parents[1]


def main():
    source = Image.open(ROOT / 'assets/aditya.png').convert('L')
    sx, sy = source.width / 1536, source.height / 1024
    box = tuple(round(n * (sx if i % 2 == 0 else sy)) for i, n in enumerate((545, 88, 1005, 548)))
    face = ImageOps.autocontrast(source.crop(box), cutoff=1)
    # Local contrast separates glasses/eyes/hair from the broad skin tones.
    # This is character selection from luminance, not a replacement face image.
    face = face.filter(ImageFilter.UnsharpMask(radius=12, percent=180, threshold=2))
    face = face.point([round(255 * (i / 255) ** 0.42) for i in range(256)])
    cols, line, rows = 100, 15, 53
    sample = face.resize((cols, rows), Image.Resampling.LANCZOS)
    ramp = ' .`:-=+*cs#%@'
    width, height = 840, 875
    parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">Aditya Heralage — ASCII portrait</title>
<desc id="desc">A monochrome character portrait derived from Aditya's own photograph. Lines print once, then remain visible.</desc>
<style>
text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}
.signature{{animation:signature .4s {rows*.11+.1:.2f}s both}}
@keyframes signature{{from{{opacity:0}}to{{opacity:1}}}}
@media(prefers-reduced-motion:reduce){{.row{{clip-path:none}}.cursor{{display:none}}.signature{{animation:none}}}}
</style>
<defs><linearGradient id="bg" x2="0" y2="1"><stop stop-color="#111722"/><stop offset="1" stop-color="#0d1117"/></linearGradient></defs>
<rect x=".5" y=".5" width="839" height="{height-1}" rx="12" fill="url(#bg)" stroke="#30363d"/>
<path d="M1 31H839" stroke="#30363d"/>
<circle cx="19" cy="16" r="5" fill="#ff5f57"/><circle cx="35" cy="16" r="5" fill="#febc2e"/><circle cx="51" cy="16" r="5" fill="#28c840"/>
<text x="420" y="20" text-anchor="middle" fill="#7d8590" font-size="12">aditya@github: ~$ ./portrait.sh</text>
''']
    for y in range(rows):
        chars = ''.join(ramp[min(len(ramp)-1, int((255-sample.getpixel((x, y))) / 256 * len(ramp)))] for x in range(cols))
        begin, end = y*.11, (y+1)*.11
        top=37+y*line
        # A continuous row wipe and a travelling block cursor, as in a terminal.
        parts.append(f'<clipPath id="r{y}"><rect x="20" y="{top}" height="15" width="800"><animate attributeName="width" values="0;0;800" keyTimes="0;{begin/end:.6f};1" begin="0s" dur="{end:.3f}s" fill="freeze"/></rect></clipPath>')
        parts.append(f'<g class="row" clip-path="url(#r{y})"><text x="20" y="{top+11.1:.1f}" fill="#c9d1d9" font-size="12.9" xml:space="preserve" textLength="800" lengthAdjust="spacing">{escape(chars)}</text></g>')
        parts.append(f'<rect class="cursor" x="20" y="{top+1}" width="8" height="13" fill="#c9d1d9" opacity="0"><animate attributeName="x" from="20" to="820" begin="{begin:.3f}s" dur=".11s" fill="freeze"/><set attributeName="opacity" to=".85" begin="{begin:.3f}s"/><set attributeName="opacity" to="0" begin="{end:.3f}s"/></rect>')
    parts.append(f'<text class="signature" x="20" y="{height-22}" fill="#8b949e" font-size="12">aditya@github:~$ whoami <tspan fill="#e6edf3"> Aditya Heralage</tspan></text></svg>')
    (ROOT/'assets/aditya-ascii.svg').write_text(''.join(parts), encoding='utf-8')
    print(f'Created {cols} x {rows} character portrait.')


if __name__ == '__main__':
    main()
