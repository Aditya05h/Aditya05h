"""Self-contained SVG renderers for the terminal profile. Standard library only."""
from datetime import date, timedelta
from html import escape

COLORS = ['#161b22', '#0e4429', '#006d32', '#26a641', '#39d353']


def start(height, title, description, width=860, background=True):
    return [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>
<style>text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}.reveal{{animation:appear .45s ease-out both}}@keyframes appear{{from{{opacity:0;transform:translateY(10px)}}to{{opacity:1;transform:translateY(0)}}}}@media(prefers-reduced-motion:reduce){{.reveal{{animation:none}}.frame{{display:none}}.final{{opacity:1!important}}}}</style>
<defs><linearGradient id="bg" x2="0" y2="1"><stop stop-color="#111722"/><stop offset="1" stop-color="#0d1117"/></linearGradient></defs>
<rect width="{width}" height="{height}" rx="12" fill="{'url(#bg)' if background else 'none'}"/>
''']


def render(data):
    days=data['days']
    total=sum(d['count'] for d in days)
    first=date.fromisoformat(days[0]['date'])
    sunday=first-timedelta(days=(first.weekday()+1)%7)
    ncols=(date.fromisoformat(days[-1]['date'])-sunday).days//7+1
    step=16
    width=40+ncols*step
    p=start(158, f"{data['username']}'s contributions", f"{total} contributions from {days[0]['date']} to {days[-1]['date']}.",width=width,background=False)
    p.append('''<style>text{font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif}.cell{transform-box:fill-box;transform-origin:center;animation:pop .55s ease-out both}.active{animation:pop .55s ease-out both,flash .7s ease-out both}@keyframes pop{0%{opacity:0;transform:scale(.2)}60%{opacity:1;transform:scale(1.1)}100%{opacity:1;transform:scale(1)}}@keyframes flash{0%,45%{filter:brightness(2.4)}100%{filter:brightness(1)}}.total{fill:#e6edf3}@media(prefers-color-scheme:light){.total{fill:#24292f}}@media(prefers-reduced-motion:reduce){.cell{animation:none}}</style>''')
    month=None
    last_label=-100
    for d in days:
        dt=date.fromisoformat(d['date'])
        col=(dt-sunday).days//7
        row=(dt.weekday()+1)%7
        x,y=34+col*step,24+row*16
        if month!=dt.month:
            if x-last_label>26:
                p.append(f'<text x="{x:.1f}" y="16" font-size="13" font-weight="600" fill="#7d8590">{dt:%b}</text>')
                last_label=x
            month=dt.month
        active=' active' if d['count'] else ''
        p.append(f'<rect class="cell{active}" style="animation-delay:{(col+row)*.036:.3f}s" x="{x:.1f}" y="{y}" width="13" height="13" rx="2.5" fill="{COLORS[d["level"]]}"><title>{dt}: {d["count"]} contributions</title></rect>')
    for row,label in [(1,'Mon'),(3,'Wed'),(5,'Fri')]:
        p.append(f'<text x="2" y="{35+row*16}" font-size="13" fill="#7d8590">{label}</text>')
    p.append(f'<text class="total" x="34" y="152" font-size="15" font-weight="700">{total:,} contributions in the last year</text>')
    p.append(f'<text x="{width-12}" y="152" text-anchor="end" font-size="11" fill="#7d8590">as of {days[-1]["date"]}</text></svg>')
    return ''.join(p)


def metrics(days):
    total=sum(d['count'] for d in days)
    active=sum(d['count']>0 for d in days)
    streak=longest=0
    for d in days:
        streak=streak+1 if d['count'] else 0
        longest=max(longest,streak)
    # An unfinished day with zero contributions need not break yesterday's streak.
    current=0
    effective=days[:-1] if days[-1]['count']==0 else days
    for d in reversed(effective):
        if not d['count']:
            break
        current+=1
    best=max(days,key=lambda d:d['count'])
    return total,active,current,longest,best


def render_stats(data):
    days=data['days']
    total,active,current,longest,best=metrics(days)
    p=start(292, f"{data['username']}'s GitHub stats", f"Stats for {days[0]['date']} to {days[-1]['date']}: {total} contributions, {active} active days, current streak {current}, longest streak in this window {longest} days.")
    p.append('''<rect x=".5" y=".5" width="859" height="291" rx="12" fill="none" stroke="#30363d"/>
<path d="M0 30H860" stroke="#30363d"/>
<circle cx="20" cy="15" r="5" fill="#ff5f57"/><circle cx="36" cy="15" r="5" fill="#febc2e"/><circle cx="52" cy="15" r="5" fill="#28c840"/>
<text x="430" y="19" font-size="12" text-anchor="middle" fill="#7d8590">aditya@github: ~$ ./stats.sh</text>''')
    cards=[
        ('current streak',current,' days','as of '+days[-1]['date']),
        ('longest streak',longest,' days','in the last year'),
        ('contributions',total,'','in the last year'),
        ('active days',active,f' / {len(days)}',f'{active/len(days):.0%} of the year'),
        ('best day',best['count'],'',date.fromisoformat(best['date']).strftime('%b %d') if total else 'no contributions yet'),
        ('avg / active day',total/active if active else 0,'','contributions'),
    ]
    for i,(label,value,suffix,detail) in enumerate(cards):
        x=20+(i%3)*278
        y=50+(i//3)*118
        delay=i*.12
        color='#39d353' if i==0 else '#e6edf3'
        p.append(f'<g class="reveal" style="animation-delay:{delay:.2f}s"><rect x="{x}" y="{y}" width="264" height="104" rx="8" fill="#161b22" stroke="#30363d"/><text x="{x+16}" y="{y+26}" font-size="12" fill="#7d8590">$ {label}</text>')
        def number(v, cls, opacity, animation):
            formatted=f'{v:.1f}' if i==5 else f'{round(v):,}'
            return f'<text class="{cls}" x="{x+16}" y="{y+64}" opacity="{opacity}" font-size="30" font-weight="700" fill="{color}">{formatted}<tspan font-size="14" font-weight="400" fill="#7d8590">{suffix}</tspan>{animation}</text>'
        begin=delay+.27
        finish=begin+1.1
        for frame in range(16):
            t=frame/16
            eased=1-(1-t)**3
            at=begin+frame*1.1/16
            until=begin+(frame+1)*1.1/16
            animation=f'<set attributeName="opacity" to="1" begin="{at:.3f}s"/><set attributeName="opacity" to="0" begin="{until:.3f}s"/>'
            p.append(number(value*eased,'frame',0,animation))
        p.append(number(value,'final',1,f'<set attributeName="opacity" to="0" begin="0s"/><set attributeName="opacity" to="1" begin="{finish:.3f}s"/>'))
        p.append(f'<text x="{x+16}" y="{y+86}" font-size="11" fill="#7d8590">{detail}</text></g>')
    p.append('</svg>')
    return ''.join(p)
