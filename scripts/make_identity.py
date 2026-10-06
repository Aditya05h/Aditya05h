"""Render the supplied brain illustration as SVG ASCII; requires Pillow locally."""
from pathlib import Path
from html import escape
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]

def main():
    source = Image.open(ROOT / 'assets/brain-source.png').convert('RGB').crop((128, 34, 286, 218))
    # Isolate the cyan/purple strokes from the neutral photographic background.
    mask = Image.new('L', source.size)
    mask.putdata([min(255, max(0, round((max(r,g,b)-min(r,g,b)-40)*4))) for r,g,b in source.getdata()])
    sample = mask.resize((72, 62), Image.Resampling.LANCZOS)
    p = ['''<svg xmlns="http://www.w3.org/2000/svg" width="860" height="402" viewBox="0 0 860 402" role="img" aria-labelledby="title desc">
<title id="title">Aditya05h — ASCII brain and identity</title><desc id="desc">Two terminal panes: the supplied brain and circuit illustration rendered in cyan-to-purple ASCII characters, beside the username Aditya05h rendered in ASCII lettering.</desc>
<style>text{font-family:Consolas,Menlo,monospace}.scan{animation:reveal 1.8s ease-out both}.name{animation:reveal 1.4s .8s both}@keyframes reveal{from{opacity:0}to{opacity:1}}@media(prefers-reduced-motion:reduce){.scan,.name{animation:none}.rows{clip-path:none}}</style>
<defs><linearGradient id="ink" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#6ddde5"/><stop offset="1" stop-color="#a78bfa"/></linearGradient><clipPath id="print"><rect x="0" y="0" width="860" height="402"><animate attributeName="height" from="0" to="402" dur="2.5s" fill="freeze"/></rect></clipPath></defs>
<rect x=".5" y=".5" width="859" height="401" rx="10" fill="#0d1117" stroke="#30363d"/>
<path d="M0 32H860M430 0V402" stroke="#30363d"/>
''']
    for x,label in [(0,'./brain.sh'),(430,'./identity.sh')]:
        for dx,color in [(17,'#ff5f57'),(31,'#febc2e'),(45,'#28c840')]:
            p.append(f'<circle cx="{x+dx}" cy="16" r="4" fill="{color}"/>')
        p.append(f'<text x="{x+245}" y="20" text-anchor="middle" font-size="10" fill="#8b949e">aditya@github: ~$ {label}</text>')
    p.append('<g class="rows" clip-path="url(#print)">')
    ramp=' .:+*#@'
    for y in range(62):
        chars=''.join(ramp[min(6,sample.getpixel((x,y))*7//256)] for x in range(72))
        ratio=y/61
        color=f'#{round(109+58*ratio):02x}{round(221-82*ratio):02x}{round(229+21*ratio):02x}'
        p.append(f'<text x="89" y="{54+y*5:.1f}" font-size="5.8" textLength="252" lengthAdjust="spacing" fill="{color}" xml:space="preserve">{escape(chars)}</text>')
    p.append('</g>')
    font={
      'A':['01110','11011','11011','11111','11011','11011','11011'],
      'd':['00011','00011','01111','11011','11011','11011','01111'],
      'i':['01100','00000','01100','01100','01100','01100','01110'],
      't':['01100','01100','11110','01100','01100','01101','00110'],
      'y':['00000','11011','11011','11011','01111','00011','11110'],
      'a':['00000','01110','00011','01111','11011','11011','01111'],
      '0':['01110','11011','11011','11011','11011','11011','01110'],
      '5':['11111','11000','11110','00011','00011','11011','01110'],
      'h':['11000','11000','11110','11011','11011','11011','11011']}
    p.append('<text x="454" y="112" font-size="12" fill="#8b949e">$ echo $GITHUB_USER</text><g class="name" fill="url(#ink)">')
    for y in range(7):
        row='  '.join(''.join('@@' if bit=='1' else '  ' for bit in font[c][y]) for c in 'Aditya05h')
        for dy in range(2):
            p.append(f'<text x="454" y="{158+y*12+dy*6}" font-size="5.8" textLength="380" lengthAdjust="spacing" xml:space="preserve">{escape(row)}</text>')
    p.append('''</g><text x="454" y="275" font-size="17" fill="#e6edf3">Aspiring SDE</text>
<text x="454" y="300" font-size="12" fill="#8b949e">Aditya Heralage</text>
<path d="M0 372H860" stroke="#30363d"/>
<text x="18" y="391" font-size="10" fill="#8b949e">brain / circuits / curiosity</text><text x="454" y="391" font-size="10" fill="#8b949e">github.com/Aditya05h</text></svg>''')
    (ROOT/'assets/identity.svg').write_text(''.join(p),encoding='utf-8')

if __name__=='__main__':
    main()
