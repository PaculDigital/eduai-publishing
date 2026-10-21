#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
#  ukur_beban_oo.sh — UKUR BEBAN ONLYOFFICE saat 1 vs 2 vs 3 sesi dibuka
# ═══════════════════════════════════════════════════════════════════════════
#  Tujuan: jawab pertanyaan Bos "apakah resource lebih banyak kalau
#  mahasiswa DAN pembimbing sama-sama pakai OnlyOffice?"
#
#  Cara: buka sesi OO lewat CDP (mahasiswa /edit/9), ukur RAM/CPU
#  oo-converter sebelum & sesudah. Lalu simulasi sesi ke-2 (pembimbing)
#  dengan mode view pada dokumen yang sama.
# ═══════════════════════════════════════════════════════════════════════════
set -uo pipefail

OO=oo-converter
CDP=http://127.0.0.1:9333
TOKEN_KUE="${1:-}"

g() { printf '\n\033[1;36m══ %s ══\033[0m\n' "$1"; }

ukur() {
  printf '   %-12s RAM=%-22s CPU=%-8s\n' "$1" \
    "$(docker stats $OO --no-stream --format '{{.MemUsage}}' 2>/dev/null)" \
    "$(docker stats $OO --no-stream --format '{{.CPUPerc}}' 2>/dev/null)"
}

g "0. KEADAAN AWAL (belum ada sesi)"
ukur "kosong"
echo "   server RAM: $(free -m | awk 'NR==2{print $3" MB terpakai dari "$2" MB"}')"

g "1. BUKA 1 SESI OO — MAHASISWA (edit) dokumen 590 KB"
python3 - "$TOKEN_KUE" <<'PYEOF' 2>&1 | tail -6
import base64, json, os, socket, sys, time, urllib.request
CDP='http://127.0.0.1:9333'
TOKEN=sys.argv[1]
def tab():
    r=urllib.request.Request(f'{CDP}/json/new?about:blank', method='PUT')
    try: return json.loads(urllib.request.urlopen(r,timeout=15).read())
    except Exception: return json.loads(urllib.request.urlopen(f'{CDP}/json/new?about:blank',timeout=15).read())
t=tab(); tid=t['id']
hp,path=t['webSocketDebuggerUrl'].split('://',1)[1].split('/',1)
s=socket.create_connection((hp.split(':')[0],int(hp.split(':')[1])),timeout=120)
k=base64.b64encode(os.urandom(16)).decode()
s.sendall((f'GET /{path} HTTP/1.1\r\nHost: {hp}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {k}\r\nSec-WebSocket-Version: 13\r\n\r\n').encode())
b=b''
while b'\r\n\r\n' not in b: b+=s.recv(4096)
i=[0]
def kr(m,p):
    i[0]+=1; d=json.dumps({'id':i[0],'method':m,'params':p or {}}).encode()
    mk=os.urandom(4); tp=bytes(x^mk[j%4] for j,x in enumerate(d))
    h=bytes([0x81,0x80|len(d)]) if len(d)<126 else bytes([0x81,0x80|126])+len(d).to_bytes(2,'big')
    s.sendall(h+mk+tp); return i[0]
def tr():
    h=s.recv(2)
    if not h: return None
    n=h[1]&0x7F
    if n==126: n=int.from_bytes(s.recv(2),'big')
    elif n==127: n=int.from_bytes(s.recv(8),'big')
    d=b''
    while len(d)<n: d+=s.recv(n-len(d))
    return json.loads(d)
def cmd(m,p=None):
    pid=kr(m,p)
    for _ in range(500):
        r=tr()
        if r is None: return None
        if r.get('id')==pid: return r
    return None
#  cookie login
cmd('Network.setCookie',{'name':'eduai_session','value':TOKEN,'domain':'eduai.bikinaja.id','path':'/','secure':True})
cmd('Page.enable')
cmd('Page.navigate',{'url':'https://eduai.bikinaja.id/edit/9'})
time.sleep(45)   #  beri OO waktu memuat dokumen
r=cmd('Runtime.evaluate',{'expression':"document.querySelector('iframe')?document.querySelector('iframe').src.slice(0,60):'TIDAK ADA IFRAME'",'returnByValue':True})
print('   iframe OO:', (r or {}).get('result',{}).get('result',{}).get('value'))
print('   tab dibiarkan TERBUKA (id=%s)' % tid)
open('/tmp/oo_tab_1.txt','w').write(tid)
PYEOF

ukur "sesi ke-1"
echo "   server RAM: $(free -m | awk 'NR==2{print $3" MB terpakai dari "$2" MB"}')"

g "2. TUNGGU 10 DETIK, UKUR LAGI (stabil?)"
sleep 10
ukur "stabil"

g "SELESAI — tab masih terbuka untuk ukur sesi ke-2"
