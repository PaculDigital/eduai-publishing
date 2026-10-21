"""UJI NYATA TOKEN — tesis asli Bos (perbaikan: _teks_dari_berkas butuh 2 arg)."""
import json, subprocess, re

CT = 'eduai-app'
def sh(cmd):
    r = subprocess.run(['docker','exec',CT,'sh','-c',cmd], capture_output=True, text=True)
    if r.stderr.strip(): print('[stderr]', r.stderr.strip()[:300])
    return r.stdout

insp = subprocess.run(['docker','inspect',CT,'--format','{{json .Config.Env}}'],
                      capture_output=True, text=True).stdout
envs = dict(e.split('=',1) for e in json.loads(insp) if '=' in e)
print('BASE  :', envs.get('EDUAI_ROUTER_BASE'))
print('MODEL :', envs.get('EDUAI_AI_MODEL'))

kode = '''
import sys
sys.path.insert(0,"/app")
from app.ai import _teks_dari_berkas, deteksi_bab
from pathlib import Path
p = Path("/app/uploads/3/9c5d6f0e79c4cbf6.docx")
t = _teks_dari_berkas(p, p.name)
print("PANJANG=" + str(len(t)))
print("AWAL=" + t[:200].replace(chr(10)," | "))
bab = deteksi_bab(t)
print("BAB=" + str(bab))
'''
out = sh(f'cd /app && python3 -c {json.dumps(kode)}')
print('\n─── EKSTRAK TESIS ASLI BOS ───')
for b in out.strip().splitlines():
    print(' ', b[:300])
m = re.search(r'PANJANG=(\d+)', out)
if m:
    print(f"\n>>> TEKS NYATA: {int(m.group(1)):,} karakter")
