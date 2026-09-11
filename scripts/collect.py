"""Collect public municipal calendars. No credentials or browser required."""
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.deps'))
import requests
from bs4 import BeautifulSoup
from dateutil import parser

TZ = ZoneInfo('America/Vancouver')
TODAY = datetime.now(TZ).date()
OUT = ROOT / 'public/data/events.json'
SESSION = requests.Session()
SESSION.headers['User-Agent'] = 'LocalActivities/1.0 (public community calendar; github.com/Jianchu/Local-Activities)'

def text(node):
    return re.sub(r'\s+', ' ', node.get_text(' ', strip=True)).strip() if node else ''

def get(url, data=None):
    time.sleep(.15)
    for attempt in range(3):
        try:
            r = SESSION.get(url, timeout=35) if data is None else SESSION.post(url, data=data, timeout=35)
            r.raise_for_status()
            r.encoding = 'utf-8'
            return BeautifulSoup(r.text, 'html.parser')
        except requests.RequestException:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)

def dates(raw):
    # Only explicit full dates; never invent occurrences for a recurring listing.
    pattern = r'(?:\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}|[A-Za-z]{3,9}\s+\d{1,2}(?:st|nd|rd|th)?[,]?\s+\d{4})'
    values = []
    for match in re.findall(pattern, raw):
        try:
            values.append(parser.parse(match).date().isoformat())
        except (ValueError, OverflowError):
            pass
    return (values[0], values[-1]) if values else (None, None)

def category(raw):
    raw = raw.lower()
    for name, keys in [
        ('Nature & outdoors', ['parks & environment', 'bird', 'tree planting', 'garden work', 'nature', 'gardening', 'farm fest']),
        ('Sports & wellness', ['sport', 'recreation', 'fitness', 'yoga', 'swim', 'run', 'walk']),
        ('Arts & culture', ['art', 'culture', 'heritage', 'gallery', 'museum', 'music', 'concert']),
        ('Learn & create', ['workshop', 'lecture', 'learning', 'discovery', 'class']),
        ('Community & festivals', ['festival', 'market', 'community', 'special event', 'open house'])]:
        if any(k in raw for k in keys):
            return name
    return 'Community & festivals'

def record(city, title, url, raw_date, raw_time, location, description, tags='', price='', start=None, end=None):
    a, b = dates(raw_date)
    a, b = start or a, end or b
    return {'id': hashlib.sha256(f'{url}|{raw_date}|{raw_time}'.encode()).hexdigest()[:16],
        'city': city, 'title': title, 'url': url, 'dateLabel': raw_date,
        'startDate': a, 'endDate': b, 'time': raw_time or 'Time not published — check event link',
        'location': location or 'Location not published — check event link',
        'description': description or 'See the official event page for details.',
        'category': category(tags + ' ' + title), 'sourceCategories': tags,
        'price': price, 'isFree': bool(re.search(r'\bfree\b', price, re.I))}

def surrey():
    base = 'https://www.surrey.ca'
    links = {}
    for page in range(25):
        soup = get(f'{base}/news-events/events?page={page}')
        cards = soup.select('.events__item-body')
        added = 0
        for card in cards:
            a = card.select_one('h3 a')
            if not a:
                continue
            url = urljoin(base, a['href'])
            if url not in links:
                links[url] = (text(a), text(card.select_one('p')), ' '.join(text(t) for t in card.select('.tag')))
                added += 1
        if not cards or not soup.select_one('a[rel="next"], .pager__item--next a'):
            break
        if page and not added:
            break
    events = []
    for url, (title, summary, tags) in links.items():
        soup = get(url)
        description = text(soup.select_one('.field--name-field-description')) or summary
        location = text(soup.select_one('.icon-field--address'))
        price = text(soup.select_one('.field--name-field-tickets-pricing'))
        sessions = soup.select('.field--name-field-smart-date > .field__item')
        # Some recurring events publish per-session venue/time only in a table.
        rows = []
        for row in soup.select('.field--name-field-description table tr'):
            cells = [text(c) for c in row.select('td')]
            if len(cells) >= 3 and re.search(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', cells[0]):
                rows.append(cells)
        for session in sessions:
            raw_date = text(session.select_one('.smart-date--date'))
            raw_time = text(session.select_one('.smart-date--time'))
            loc = location
            try:
                date = parser.parse(raw_date).date()
                for cells in rows:
                    try:
                        rowdate = parser.parse(cells[0].replace('.', ''), fuzzy=True, default=datetime(date.year, 1, 1)).date()
                    except (ValueError, OverflowError):
                        continue
                    if rowdate == date:
                        if not raw_time:
                            raw_time = cells[1]
                        if len(cells) == 3 and 'age' not in cells[2].lower():
                            loc = cells[2]
                        elif len(cells) >= 5:
                            loc = ', '.join(cells[3:])
            except (ValueError, OverflowError):
                pass
            events.append(record('Surrey', title, url, raw_date, raw_time, loc, description, tags, price))
    return events

def form_data(soup):
    data = {}
    for el in soup.select('input[name], select[name], textarea[name]'):
        name = el['name']
        if el.name == 'input':
            typ = el.get('type', '').lower()
            if typ in ('submit', 'button', 'image') or (typ in ('checkbox', 'radio') and not el.has_attr('checked')):
                continue
            data[name] = el.get('value', '')
        elif el.name == 'select':
            option = el.select_one('option[selected]') or el.select_one('option')
            if option:
                data[name] = option.get('value', text(option))
    return data

def richmond():
    base = 'https://www.richmond.ca/culture/calendar/search/'
    soup = get(base + 'default.aspx')
    data = form_data(soup)
    data.update({'ctl00$main$ddlDateRange': '90', '__EVENTTARGET': 'ctl00$main$ddlDateRange', '__EVENTARGUMENT': ''})
    soup = get(base + 'default.aspx', data)
    links = {}
    for page in range(1, 25):
        for card in soup.select('.list-item__content'):
            a = card.select_one('h4 a')
            if a:
                ps = card.find_all('p', recursive=False)
                links[urljoin(base, a['href'])] = (text(a), text(ps[0]) if ps else '', text(ps[1]) if len(ps) > 1 else '')
        nextlink = soup.select_one(f'.pager a[aria-label="Page {page + 1}"]')
        if not nextlink:
            break
        match = re.search(r'WebForm_PostBackOptions\("([^"]+)"', nextlink.get('href', ''))
        if not match:
            raise RuntimeError('Richmond pagination format changed')
        data = form_data(soup)
        data.update({'__EVENTTARGET': match[1], '__EVENTARGUMENT': ''})
        soup = get(base + 'default.aspx', data)
    events = []
    for url, (title, dateplace, timing) in links.items():
        soup = get(url)
        container = soup.select_one('#main_evEventDetails')
        if not container:
            raise RuntimeError('Richmond detail selector changed')
        date_node = container.select_one('.event-details p')
        raw_date = text(date_node) or dateplace
        venue = text(container.select_one('[id$="lnkVenueName"]'))
        address = text(container.select_one('[id$="lnkVenueAddress"]'))
        loc = ', '.join(dict.fromkeys(v for v in (venue, address) if v))
        tags = text(container.select_one('.cta__label')) + ' ' + text(container.select_one('.cta__heading'))
        price = 'Free' if re.search(r'(?:event is|event:?)\s*free', text(container), re.I) else ''
        for el in container.select('.event-details, .cta--large, address'):
            el.decompose()
        description = text(container)
        start, end = dates(dateplace)
        events.append(record('Richmond', title, url, raw_date, timing, loc, description, tags, price, start, end))
    return events

def main():
    old = json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {'events': [], 'sources': {}}
    events, statuses = [], {}
    now = datetime.now(TZ).isoformat(timespec='seconds')
    failed = []
    for city, fn in [('Surrey', surrey), ('Richmond', richmond)]:
        try:
            fresh = fn()
            if not fresh:
                raise RuntimeError('No events extracted; keeping last successful data')
            events.extend(fresh)
            statuses[city] = {'updatedAt': now, 'status': 'ok', 'count': len(fresh)}
            print(f'{city}: {len(fresh)} sessions', flush=True)
        except Exception as exc:
            failed.append(city)
            retained = [e for e in old['events'] if e['city'] == city]
            events.extend(retained)
            statuses[city] = {**old.get('sources', {}).get(city, {}), 'status': 'stale', 'error': 'Source refresh failed; showing last successful data.'}
            print(f'{city}: {exc}', file=sys.stderr, flush=True)
    events = list({e['id']: e for e in events}.values())
    events = [e for e in events if not e['endDate'] or e['endDate'] >= TODAY.isoformat()]
    events.sort(key=lambda e: (e['startDate'] or '9999', e['title']))
    if not events:
        raise RuntimeError('No data available from either city')
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({'updatedAt': now, 'timezone': 'America/Vancouver', 'sources': statuses, 'events': events}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Saved {len(events)} current sessions', flush=True)

if __name__ == '__main__':
    main()
