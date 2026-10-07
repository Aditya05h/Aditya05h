"""Self-contained SVG renderers for the terminal profile. Standard library only."""
from datetime import date, datetime, timedelta, timezone
from html import escape

COLORS = ['#161b22', '#0e4429', '#006d32', '#26a641', '#39d353']


def snapshot_label(data):
    if data.get('fetched_at'):
        stamp = datetime.fromisoformat(data['fetched_at']).astimezone(timezone.utc)
        return f'Updated {stamp:%d %b %Y, %H:%M} UTC'
    return 'As of ' + data['days'][-1]['date']


def start(height, title, description, width=860, background=True):
    return [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>
<style>text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}.reveal{{animation:appear .45s ease-out both}}@keyframes appear{{from{{opacity:0;transform:translateY(10px)}}to{{opacity:1;transform:translateY(0)}}}}@media(prefers-reduced-motion:reduce){{.reveal{{animation:none}}}}</style>
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
    p=start(180, f"{data['username']}'s contributions", f"{total} contributions from {days[0]['date']} to {days[-1]['date']}. {snapshot_label(data)}.",width=width,background=True)
    p.append('''<style>text{font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif}.cell{transform-box:fill-box;transform-origin:center;animation:pop .55s ease-out both}.active{animation:pop .55s ease-out both,flash .7s ease-out both}@keyframes pop{0%{opacity:0;transform:scale(.2)}60%{opacity:1;transform:scale(1.1)}100%{opacity:1;transform:scale(1)}}@keyframes flash{0%,45%{filter:brightness(2.4)}100%{filter:brightness(1)}}.total{fill:#e6edf3}@media(prefers-reduced-motion:reduce){.cell,.active{animation:none}}</style>''')
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
    p.append(f'<text x="34" y="172" font-size="11" fill="#7d8590">{escape(snapshot_label(data))}</text>')
    p.append(f'<text x="{width-12}" y="172" text-anchor="end" font-size="11" fill="#7d8590">{days[0]["date"]} to {days[-1]["date"]}</text></svg>')
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
    p=start(570, f"{data['username']}'s GitHub stats", f"Stats for {days[0]['date']} to {days[-1]['date']}: {total} contributions, {active} active days, current streak {current}, longest streak in this window {longest} days. Monthly bars total contributions within the displayed date window; boundary months may be partial. {snapshot_label(data)}.")
    p.append('''<rect x=".5" y=".5" width="859" height="569" rx="12" fill="none" stroke="#30363d"/>
<path d="M0 30H860" stroke="#30363d"/>
<circle cx="20" cy="15" r="5" fill="#ff5f57"/><circle cx="36" cy="15" r="5" fill="#febc2e"/><circle cx="52" cy="15" r="5" fill="#28c840"/>
<text x="430" y="19" font-size="12" text-anchor="middle" fill="#7d8590">aditya@github: ~$ ./stats.sh</text>''')
    cards=[
        ('current streak',current,' days','as of '+days[-1]['date']),
        ('longest streak',longest,' days','in the last year'),
        ('contributions',total,'','in the last year'),
        ('active days',active,f' / {len(days)}',f'{active/len(days):.0%} of displayed days'),
        ('best day',best['count'],'',date.fromisoformat(best['date']).strftime('%b %d') if total else 'no contributions yet'),
        ('avg / active day',total/active if active else 0,'','contributions'),
    ]
    for i,(label,value,suffix,detail) in enumerate(cards):
        x=20+(i%3)*278
        y=50+(i//3)*118
        delay=i*.12
        color='#39d353' if i==0 else '#e6edf3'
        p.append(f'<g class="reveal" style="animation-delay:{delay:.2f}s"><rect x="{x}" y="{y}" width="264" height="104" rx="8" fill="#161b22" stroke="#30363d"/><text x="{x+16}" y="{y+26}" font-size="12" fill="#7d8590">$ {label}</text>')
        # Animate the card, never its numeric value: the count is always exact.
        formatted=f'{value:.1f}' if i==5 else f'{value:,}'
        p.append(f'<text class="metric" data-metric="{label}" x="{x+16}" y="{y+64}" font-size="30" font-weight="700" fill="{color}">{formatted}<tspan font-size="14" font-weight="400" fill="#7d8590">{suffix}</tspan></text>')
        p.append(f'<text x="{x+16}" y="{y+86}" font-size="11" fill="#7d8590">{detail}</text></g>')
    months = monthly_totals(days)
    peak = max(months.values(), default=0)
    p.append('<style>.bar{transform-box:fill-box;transform-origin:center bottom;animation:grow 1s ease-out both}@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}@media(prefers-reduced-motion:reduce){.bar{animation:none}}</style>')
    p.append('<rect x="20" y="300" width="820" height="210" rx="8" fill="#161b22" stroke="#30363d"/><text x="36" y="326" font-size="12" fill="#8b949e">$ contributions / month</text>')
    step = 770 / len(months)
    for i,(month,count) in enumerate(months.items()):
        x = 45 + i*step
        height = count / peak * 130 if peak else 0
        fill = '#39d353' if count==peak and peak else '#26a641'
        p.append(f'<g><title>{month}: {count} contributions in the displayed window</title><rect class="bar" style="animation-delay:{i*.06:.2f}s" x="{x:.2f}" y="{478-height:.2f}" width="{step*.62:.2f}" height="{height:.2f}" rx="2" fill="{fill}"/>')
        if not count:
            p.append(f'<path d="M{x:.2f} 478h{step*.62:.2f}" stroke="#30363d"/>')
        if count:
            p.append(f'<text x="{x+step*.31:.2f}" y="{470-height:.2f}" font-size="11" text-anchor="middle" fill="#e6edf3" font-weight="700">{count:,}</text>')
        label=date.fromisoformat(month+'-01').strftime('%b %y')
        p.append(f'<text x="{x+step*.31:.2f}" y="497" font-size="10" text-anchor="middle" fill="#8b949e">{label}</text></g>')
    p.append(f'<text x="24" y="536" font-size="11" fill="#8b949e">{escape(snapshot_label(data))}</text>')
    p.append(f'<text x="836" y="536" text-anchor="end" font-size="11" fill="#8b949e">{days[0]["date"]} to {days[-1]["date"]}</text>')
    p.append('<text x="24" y="554" font-size="10" fill="#8b949e">Same calendar as above. First and last months may be partial.</text></svg>')
    return ''.join(p)


def monthly_totals(days):
    result = {}
    for day in days:
        month = day['date'][:7]
        result[month] = result.get(month, 0) + day['count']
    return result
