#!/usr/bin/env python3
"""Render profile images using public GitHub facts; standard library only."""
import base64
import datetime as dt
import html
import json
import math
import os
from pathlib import Path
import re
import textwrap
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / 'config.json').read_text())
USER = CFG['username']
OUT = ROOT / 'assets'
TOKEN = os.getenv('GITHUB_TOKEN', '')
BG, CYAN, PURPLE, WHITE, MUTED = '#080D25', '#36E2EF', '#A78BFA', '#F3F5FF', '#9DAACB'


def e(s):
    return html.escape(str(s), quote=True)


def api(url, body=None):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'github-profile-renderer'}
    if TOKEN:
        headers['Authorization'] = 'Bearer ' + TOKEN
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None, headers=headers)
    with urllib.request.urlopen(req, timeout=25) as response:
        return json.load(response)


def get_data():
    snap = dict(CFG['snapshot'], as_of='2026-09-10')
    repos = json.loads((ROOT / 'repositories.json').read_text())
    try:
        fresh = []
        for name in CFG['projects']:
            fresh.append(api(f'https://api.github.com/repos/{USER}/{name}'))
        repos = fresh
        profile = api(f'https://api.github.com/users/{USER}')
        for key in ('public_repos', 'followers', 'following'):
            snap[key] = profile[key]
        snap['stats_as_of'] = dt.datetime.now(dt.timezone.utc).date().isoformat()
    except Exception as error:
        print(f'Using dated public snapshot for unavailable REST data: {error}')
    if TOKEN:
        try:
            query = 'query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}'
            result = api('https://api.github.com/graphql', {'query': query, 'variables': {'login': USER}})
            cal = result['data']['user']['contributionsCollection']['contributionCalendar']
            days = {d['date']: d['contributionCount'] for w in cal['weeks'] for d in w['contributionDays']}
            if not days or sum(days.values()) != cal['totalContributions']:
                raise ValueError('Inconsistent contribution calendar')
            snap.update(contributions=days, total_contributions=cal['totalContributions'], as_of=max(days))
        except Exception as error:
            print(f'Contribution refresh unavailable; retaining dated history: {error}')
    return snap, {r['name']: r for r in repos}


def text(x, y, content, size=18, color=WHITE, extra=''):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" {extra}>{e(content)}</text>'


def svg(w, h, body, title):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">
    <title>{e(title)}</title><defs>
    <linearGradient id="bg" x2="1" y2="1"><stop stop-color="#080D25"/><stop offset="1" stop-color="#111938"/></linearGradient>
    <linearGradient id="edge"><stop stop-color="#36E2EF"/><stop offset=".6" stop-color="#A78BFA"/><stop offset="1" stop-color="#36E2EF"/></linearGradient>
    <filter id="glow" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    </defs><rect width="{w}" height="{h}" rx="20" fill="url(#bg)"/><rect x="1" y="1" width="{w-2}" height="{h-2}" rx="19" fill="none" stroke="#273352"/>
    <g font-family="DejaVu Sans Mono,Consolas,monospace">{body}</g></svg>'''


def hero(mobile=False):
    w, h = (600, 740) if mobile else (1000, 460)
    image = base64.b64encode((ROOT / CFG['portrait']).read_bytes()).decode()
    cx, cy, radius = (300, 196, 118) if mobile else (190, 234, 127)
    x, y = (38, 387) if mobile else (382, 141)
    name_size = 32 if mobile else 37
    b = '<rect x="1.5" y="1.5" width="%s" height="%s" rx="19" fill="none" stroke="url(#edge)" stroke-width="2"/>' % (w-3, h-3)
    for i, color in enumerate(['#FF6058', '#FFBD2E', '#29C840']):
        b += f'<circle cx="{27+i*22}" cy="27" r="6" fill="{color}"/>'
    b += text(103, 32, 'PROFILE / '+USER, 12, MUTED)
    b += f'<clipPath id="portrait"><circle cx="{cx}" cy="{cy}" r="{radius}"/></clipPath><circle cx="{cx}" cy="{cy}" r="{radius+7}" fill="none" stroke="url(#edge)" stroke-width="2" filter="url(#glow)"/>'
    b += f'<image href="data:image/jpeg;base64,{image}" x="{cx-radius}" y="{cy-radius}" width="{radius*2}" height="{radius*2}" preserveAspectRatio="xMidYMid slice" clip-path="url(#portrait)"/>'
    for i in range(20):
        angle = i*math.tau/20
        px, py = cx+(radius+17)*math.cos(angle), cy+(radius+17)*math.sin(angle)
        b += f'<circle cx="{px:.1f}" cy="{py:.1f}" r="1.5" fill="{CYAN}"><animate attributeName="opacity" values=".15;.9;.15" dur="3s" begin="-{i*.15}s" repeatCount="indefinite"/></circle>'
    b += text(x, y-32, 'SYSTEM.INFO', 13, CYAN, 'letter-spacing="3"')
    b += text(x, y+13, CFG['name'], name_size)
    b += text(x, y+46, '@'+USER, 20, PURPLE)
    b += f'<line x1="{x}" y1="{y+72}" x2="{w-38}" y2="{y+72}" stroke="#273352"/>'
    b += text(x, y+111, 'ORGANIZATION', 12, MUTED)
    b += text(x+192, y+111, CFG['organization'], 19)
    b += text(x, y+151, 'PUBLIC WORK', 12, MUTED)
    b += text(x+192, y+151, 'Explore repositories ↗', 17, CYAN)
    b += text(x, y+205, '$ open github.com/'+USER, 14, MUTED)
    b += f'<rect x="{x+366}" y="{y+191}" width="8" height="17" fill="{CYAN}"><animate attributeName="opacity" values="1;0;1" dur="1.2s" repeatCount="indefinite"/></rect>'
    return svg(w,h,b,'Tarang Narayan — '+USER+' — '+CFG['organization'])


def stats(snap, mobile=False):
    w,h = (600,260) if mobile else (1000,205)
    b = text(28,36,'GITHUB / PUBLIC SNAPSHOT',12,CYAN,'letter-spacing="2"')
    b += text(w-28,h-18,'Updated '+snap.get('stats_as_of',snap['as_of']),11,MUTED,'text-anchor="end"')
    for i,(label,key) in enumerate([('REPOSITORIES','public_repos'),('FOLLOWERS','followers'),('FOLLOWING','following'),('CONTRIBUTIONS','total_contributions')]):
        x = 30+(i%2)*290 if mobile else 34+i*245
        y = 84+(i//2)*91 if mobile else 114
        b += text(x,y,snap[key],36,CYAN if i%2==0 else PURPLE)
        b += text(x,y+25,label,11,MUTED,'letter-spacing="1"')
    return svg(w,h,b,'Public GitHub metrics; contributions as of '+snap['as_of'])


def languages(repos):
    counts = {}
    for name in CFG['projects']:
        lang = repos.get(name,{}).get('language')
        if lang:
            counts[lang]=counts.get(lang,0)+1
    b=text(28,33,'PROJECT LANGUAGES',12,CYAN,'letter-spacing="2"')
    b+=text(28,56,'Primary language of the six selected repositories',12,MUTED)
    colors=[CYAN,PURPLE,'#6EE7B7','#F472B6','#60A5FA']
    x=28
    for i,(lang,count) in enumerate(sorted(counts.items(),key=lambda x:(-x[1],x[0]))):
        width=944*count/max(1,sum(counts.values()))
        b+=f'<rect x="{x}" y="75" width="{width}" height="8" fill="{colors[i%5]}"/>'
        x+=width
        b+=text(28+i*236,118,f'{lang} · {count}',15,colors[i%5])
    return svg(1000,144,b,'Primary languages of selected public repositories')


def card(name, repo):
    b=text(25,31,'REPOSITORY',11,CYAN,'letter-spacing="2"')
    b+=text(545,31,'↗',21,PURPLE,'text-anchor="end"')
    title_lines=textwrap.wrap(name.replace('-',' ').replace('_',' '),width=35)
    for i,line in enumerate(title_lines):
        b+=text(25,73+i*25,line,21)
    desc=repo.get('description') or ''
    lines=textwrap.wrap(desc,width=59)
    for i,line in enumerate(lines[:4]):
        suffix='…' if i==3 and len(lines)>4 else ''
        b+=text(25,139+i*20,line+suffix,14,MUTED)
    b+='<line x1="25" y1="234" x2="545" y2="234" stroke="#273352"/>'
    lang=repo.get('language')
    if lang:
        b+=text(25,263,lang,15,PURPLE)
    metrics=[]
    if 'stargazers_count' in repo:
        metrics.append(str(repo['stargazers_count'])+' stars')
    if 'forks_count' in repo:
        metrics.append(str(repo['forks_count'])+' forks')
    b+=text(545,263,' · '.join(metrics),12,MUTED,'text-anchor="end"')
    return svg(570,285,b,name+': '+desc)


def activity(snap):
    values=snap['contributions']
    end=dt.date.fromisoformat(snap['as_of'])
    sunday=end-dt.timedelta(days=(end.weekday()+1)%7)
    start=sunday-dt.timedelta(weeks=52)
    palette=['#18213D','#225B70','#278E9B','#36C7CD','#8FFFE6']
    b=text(28,34,'CONTRIBUTION / FLIGHT',12,CYAN,'letter-spacing="2"')
    b+=text(972,34,str(snap['total_contributions'])+' contributions',16,WHITE,'text-anchor="end"')
    targets=[]
    for week in range(53):
        for weekday in range(7):
            date=start+dt.timedelta(days=week*7+weekday)
            if date>end:
                continue
            count=int(values.get(date.isoformat(),0))
            level=0 if count==0 else min(4,1+count//2)
            x,y=27+week*18,75+weekday*18
            b+=f'<rect x="{x}" y="{y}" width="13" height="13" rx="3" fill="{palette[level]}"><title>{date}: {count} contributions</title></rect>'
            if count:
                targets.append((x+6.5,y+6.5))
    targets=sorted(targets)
    if targets:
        duration=len(targets)*1.4
        positions=';'.join(str(p[0])+' 0' for p in targets+[targets[0]])
        b+=f'<g transform="translate({targets[0][0]} 0)"><animateTransform attributeName="transform" type="translate" values="{positions}" dur="{duration}s" repeatCount="indefinite"/>'
        b+=f'<path d="M0 220 L-11 244 L0 238 L11 244 Z" fill="{PURPLE}" stroke="{CYAN}" filter="url(#glow)"/><path d="M-4 242 L0 252 L4 242" fill="{CYAN}"><animate attributeName="opacity" values=".3;1;.3" dur=".3s" repeatCount="indefinite"/></path></g>'
        for i,(x,y) in enumerate(targets):
            begin=i*1.4
            b+=f'<line x1="{x}" x2="{x}" y1="220" y2="{y}" stroke="{CYAN}" stroke-width="2" opacity="0"><animate attributeName="opacity" values="0;.7;0;0" keyTimes="0;.04;.08;1" dur="{duration}s" begin="{begin}s" repeatCount="indefinite"/></line>'
    b+=text(28,279,'History through '+snap['as_of']+' · decorative animation',11,MUTED)
    return svg(1000,300,b,'GitHub contribution history through '+snap['as_of'])


def main():
    snap,repos=get_data()
    OUT.mkdir(exist_ok=True)
    (OUT/'projects').mkdir(exist_ok=True)
    generated={'hero.svg':hero(),'hero-mobile.svg':hero(True),'dashboard.svg':stats(snap),'dashboard-mobile.svg':stats(snap,True),'languages.svg':languages(repos),'activity.svg':activity(snap)}
    for name in CFG['projects']:
        generated['projects/'+name.lower()+'.svg']=card(name,repos.get(name,{}))
    for path,content in generated.items():
        # Retain the last successful contribution asset when GraphQL is unavailable.
        if path=='activity.svg' and TOKEN and snap['as_of']=='2026-09-10' and (OUT/path).exists():
            continue
        (OUT/path).write_text(content)
    print('Rendered '+str(len(generated))+' SVG assets')


if __name__=='__main__':
    main()
