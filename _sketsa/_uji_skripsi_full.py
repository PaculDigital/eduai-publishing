"""UJI NYATA: skripsi FULL 7 MB (Bos) — berapa token & biayanya?

Dokumen: SKRIPSI WULAN.docx (7,29 MB, tapi 6,83 MB = GAMBAR; teks nyata 700.599 kar)
Uji: kirim BERTAHAP (sesuai mekanisme potong) + ukur token NYATA tiap bagian.
"""
import json, subprocess, time, urllib.request

insp = subprocess.run(['docker','inspect','eduai-app','--format','{{json .Config.Env}}'],
                      capture_output=True, text=True).stdout
E = dict(e.split('=',1) for e in json.loads(insp) if '=' in e)
BASE, KEY, MODEL = E['EDUAI_ROUTER_BASE'], E['EDUAI_ROUTER_KEY'], E['EDUAI_AI_MODEL']
TARIF = 0.0155915

def panggil(user, max_out=2000, timeout=420):
    body = json.dumps({'model': MODEL,'messages':[{'role':'user','content':user}],
                       'max_tokens': max_out}).encode()
    req = urllib.request.Request(f'{BASE}/chat/completions', data=body,
        headers={'Authorization': f'Bearer {KEY}','Content-Type':'application/json'})
    t0=time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            m = r.read().decode('utf-8','replace')
    except Exception as e:
        return dict(ok=False, err=str(e)[:150], detik=round(time.time()-t0,1))
    dec=json.JSONDecoder(); i=0; u={}; mdl='?'; jw=''
    while i < len(m):
        while i<len(m) and m[i] not in '{[': i+=1
        if i>=len(m): break
        try:
            o,j=dec.raw_decode(m,i)
            if isinstance(o,dict):
                if o.get('usage'): u=o['usage']
                if o.get('model'): mdl=o['model']
                try: jw=o['choices'][0]['message'].get('content') or jw
                except: pass
            i=j
        except: i+=1
    return dict(ok=bool(u), masuk=u.get('prompt_tokens',0), keluar=u.get('completion_tokens',0),
                total=u.get('total_tokens',0), detik=round(time.time()-t0,1), model=mdl,
                rp=round(u.get('total_tokens',0)*TARIF), jawab=jw[:100].replace('\n',' '))

T = open('/tmp/skripsi_full.txt').read()
print(f'TEKS SKRIPSI FULL: {len(T):,} karakter ({len(T.split()):,} kata)')
print(f'Combo: {MODEL}\n' + '='*78)

POTONG = 55000
n_bagian = (len(T) + POTONG - 1)//POTONG
print(f'Kalau dipotong {POTONG:,} kar/bagian -> {n_bagian} bagian\n')

hasil = []
# Uji POTONGAN PERTAMA dulu (mewakili), bukan semua (hemat waktu)
for label, isi in [
    ('A. Potongan 1 (55rb kar)', T[:POTONG]),
    ('B. Potongan 1+2 (110rb kar)', T[:110000]),
]:
    h = panggil(f"Baca naskah ini. Sebutkan: judul, bab yang ada, metode, dan 2 saran.\n\n{isi}")
    hasil.append((label, len(isi), h))
    if h.get('ok'):
        print(f"{label}")
        print(f"   masuk={h['masuk']:,} tok · keluar={h['keluar']:,} tok · {h['detik']}s")
        print(f"   BIAYA = Rp {h['rp']:,} · {h['model']}")
        print(f"   → rasio {h['masuk']/len(isi):.3f} token/karakter")
    else:
        print(f'{label} ❌ {h}')
    print('-'*78)
    time.sleep(2)

json.dump(hasil, open('/tmp/uji_skripsi.json','w'), indent=1)
print('\n✓ /tmp/uji_skripsi.json')
