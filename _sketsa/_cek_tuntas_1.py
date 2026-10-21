"""OPSI 2 — cek TUNTAS: apakah 9router bisa menambah jenis provider/node
BARU tanpa mengubah kode (bundle)?

Yang diperiksa:
  1. Semua jenis node yang dikenali (prefix id-nya) — dari konstanta f.JH/f.Pd/f.DI
  2. Apakah ada endpoint lain yang menerima definisi provider bebas
  3. Apakah DB 9router menyimpan definisi node (bisa disuntik dari luar?)
  4. Apakah ada jenis node "decisions"/"systemone" yang sudah ada
"""
import re
import subprocess

# salin bundle yang memuat konstanta jenis node
for ck in ('9128', '318', '235', '3193', '9820', '4741', '1813'):
    subprocess.run(['docker', 'cp', f'9router:/app/.next/server/chunks/{ck}.js',
                    f'/tmp/9router_cek/{ck}.js'], check=False)

print('== 1. cari konstanta ID jenis node (JH/Pd/DI) ==')
for ck in ('9128', '318', '235', '3193', '9820', '4741', '1813'):
    try:
        src = open(f'/tmp/9router_cek/{ck}.js', encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    for m in re.finditer(r'(JH|Pd|DI)\s*[:=]\s*["\']([\w\-]{4,30})["\']', src):
        print(f'  chunk {ck}: {m.group(1)} = "{m.group(2)}"')

print()
print('== 2. cari semua "type" provider node yang dikenali ==')
jenis = set()
for ck in ('9128', '318', '235', '3193', '9820'):
    try:
        src = open(f'/tmp/9router_cek/{ck}.js', encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    for m in re.finditer(r'type\s*[:=]\s*["\']((?:openai|anthropic|custom|decisions|systemone)[\w\-]*)["\']', src):
        jenis.add(m.group(1))
print('  ', sorted(jenis))

print()
print('== 3. apakah ada sebutan decisions/systemone/hukum di bundle? ==')
for kata in ('decisions', 'systemone', 'system-one', 'typesafe', 'jev'):
    ada = []
    for ck in ('9128', '318', '235', '3193', '9820', '4741', '1813'):
        try:
            src = open(f'/tmp/9router_cek/{ck}.js', encoding='utf-8', errors='replace').read()
        except Exception:
            continue
        if kata in src:
            ada.append(ck)
    print(f'  {kata:12s} : {ada if ada else "TIDAK ADA"}')
