from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from html.parser import HTMLParser
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import json, re, time, math

BASE = 'https://www.finn.no'
UA = 'Hyllejakt/1.0 (authorized personal search)'
SEARCH = BASE + '/recommerce/forsale/search?'

class Cards(HTMLParser):
    def __init__(self):
        super().__init__(); self.items=[]; self.card=None; self.h2=False
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='article': self.card={'url':'','title':'','lines':[]}; return
        if self.card is not None:
            if tag=='h2': self.h2=True
            if tag=='a' and '/recommerce/forsale/item/' in a.get('href','') and not self.card['url']: self.card['url']=a['href']
    def handle_endtag(self, tag):
        if self.card is not None:
            if tag=='h2': self.h2=False
            if tag=='article':
                if self.card['url']: self.items.append(self.card)
                self.card=None
    def handle_data(self, data):
        if self.card is not None:
            s=' '.join(data.split())
            if s:
                self.card['lines'].append(s)
                if self.h2: self.card['title'] += s

def fetch(url):
    req=Request(url, headers={'User-Agent':UA, 'Accept':'text/html'})
    with urlopen(req, timeout=18) as r: return r.read().decode('utf-8','replace')

def extract_detail(url):
    html=fetch(url)
    ld=re.search(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',html,re.S|re.I)
    product={}
    if ld:
        try: product=json.loads(ld.group(1))
        except Exception: pass
    desc=product.get('description','')
    title=product.get('name','')
    offers=product.get('offers') or {}
    if isinstance(offers,list): offers=offers[0] if offers else {}
    price=offers.get('price') if isinstance(offers,dict) else None
    geo=re.search(r'"lat"\s*:\s*(-?\d+(?:\.\d+)?)\s*,\s*"lng"\s*:\s*(-?\d+(?:\.\d+)?)',html)
    if not geo: geo=re.search(r'lat=([\d.]+)(?:&amp;|&)lon=([\d.]+)',html)
    coords=[float(geo.group(1)),float(geo.group(2))] if geo else None
    q=re.search(r'\b(\d+)\s*(?:stk\.?|stykker|hyller)\b',title+' '+desc,re.I)
    qty=int(q.group(1)) if q else 1
    if not price:
        pm=re.search(r'"price"\s*:\s*"?(\d+)',html)
        if pm: price=pm.group(1)
    return {'title':title,'price':int(float(price or 0)),'qty':qty,'coords':coords}

def haversine(a,b):
    r=6371; p1,p2=map(math.radians,[a[0],b[0]]); dp=p2-p1; dl=math.radians(b[1]-a[1]); x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return round(2*r*math.asin(math.sqrt(x)))

def search_events():
    query=urlencode([('q','billy hylle'),('height_cm_from','200'),('width_cm_from','80'),('product_category','2.78.8345.219'),('location','0.20061'),('location','0.20003')])
    html=fetch(SEARCH+query)
    parser=Cards(); parser.feed(html)
    cards=[]; seen=set()
    for card in parser.items:
        if card['url'] not in seen: seen.add(card['url']); cards.append(card)
    total=len(cards); yield {'type':'start','total':total}
    found=0; failures=0
    for index,card in enumerate(cards,1):
        try:
            ad=extract_detail(card['url'])
            alltext=' '.join(card['lines'])
            loc=next((x for x in card['lines'] if x.lower() in ('oslo','akershus') or any(k in x.lower() for k in ('lørenskog','bærum','asker','lillestrøm','nesodden','drøbak','ski','kolbotn','ås','oppegård','nittedal','rælingen','ullensaker','moss','vestby','nes'))), 'Oslo')
            pm=re.search(r'(\d[\d\s\u00a0]*)\s*kr',alltext,re.I)
            if pm: ad['price']=int(re.sub(r'\D','',pm.group(1)) or 0)
            age_match=re.search(r'(?<!\w)(\d+)\s*(min(?:\.|utter)?|t(?:\.|imer?)|dg\.?|d(?:\.|ager?)|u(?:\.|ker?)|mnd\.?|mån(?:ed(?:er)?)?)(?=\s|$)',alltext,re.I)
            age_minutes=10**12; age_label='Ukjent'
            if age_match:
                age_num=int(age_match.group(1)); age_unit=age_match.group(2).lower()
                age_factor=1 if age_unit.startswith('min') else 60 if age_unit.startswith('t') else 1440 if age_unit.startswith(('d','dg')) else 10080 if age_unit.startswith('u') else 43200
                age_minutes=age_num*age_factor; age_label=f'{age_num} {age_unit}'
            dist=haversine(ad['coords'],[59.94074,10.81329]) if ad['coords'] else 999
            ad.update({'place':loc,'url':card['url'],'distance':dist,'age_label':age_label,'age_minutes':age_minutes})
            found+=1
            yield {'type':'ad','ad':ad,'processed':index,'total':total,'found':found}
        except (HTTPError, URLError, TimeoutError, ValueError):
            failures+=1
            yield {'type':'progress','processed':index,'total':total,'found':found,'failures':failures}
        if index<total: time.sleep(1.0)
    yield {'type':'complete','processed':total,'total':total,'found':found,'failures':failures}

class Handler(SimpleHTTPRequestHandler):
    protocol_version='HTTP/1.1'
    def do_GET(self):
        if self.path.startswith('/api/search'):
            self.send_response(200)
            self.send_header('Content-Type','application/x-ndjson; charset=utf-8')
            self.send_header('Transfer-Encoding','chunked')
            self.send_header('Cache-Control','no-cache')
            self.end_headers()
            try:
                for event in search_events():
                    body=(json.dumps(event,ensure_ascii=False)+'\n').encode('utf-8')
                    self.wfile.write(f'{len(body):X}\r\n'.encode('ascii')+body+b'\r\n')
                    self.wfile.flush()
            except (HTTPError, URLError, TimeoutError, BrokenPipeError) as e:
                if not isinstance(e,BrokenPipeError):
                    body=(json.dumps({'type':'error','message':f'FINN-søket feilet: {e}'},ensure_ascii=False)+'\n').encode('utf-8')
                    self.wfile.write(f'{len(body):X}\r\n'.encode('ascii')+body+b'\r\n'); self.wfile.flush()
            finally:
                try: self.wfile.write(b'0\r\n\r\n'); self.wfile.flush()
                except BrokenPipeError: pass
        else: super().do_GET()
    def log_message(self, fmt, *args): print(fmt % args)

if __name__=='__main__':
    print('Hyllejakt kjører på http://localhost:8000')
    ThreadingHTTPServer(('127.0.0.1',8000),Handler).serve_forever()

