"""UJI NYATA TOKEN — v3 FINAL.

Perbaikan: JSON menempel dengan "data: [DONE]" -> pakai raw_decode bertahap.

Dokumen ASLI Bos: TESIS sampai BAB III = 63.797 karakter teks nyata.
  ⚠️ Bukan tesis full 5 bab (catatan Bos).
"""
import json, subprocess, time, urllib.request, re

CT='eduai-app'
insp = subprocess.run(['docker','inspect',CT,'--format','{{json .Config.Env}}'],
                      capture_output=True, text=True).stdout
E = dict(e.split('=',1) for e in json.loads(insp) if '=' in e)
BASE, KEY, MODEL = E['EDUAI_ROUTER_BASE'], E['EDUAI_ROUTER_KEY'], E['EDUAI_AI_MODEL']
TARIF_RP = 0.0155915      # Rp/token (terukur)

def panggil(user, max_out=4000, timeout=420):
    body = json.dumps({'model': MODEL,
                       'messages':[{'role':'user','content': user}],
                       'max_tokens': max_out}).encode()
    req = urllib.request.Request(f'{BASE}/chat/completions', data=body,
        headers={'Authorization': f'Bearer {KEY}', 'Content-Type':'application/json'})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            mentah = r.read().decode('utf-8','replace')
        dt = time.time()-t0
    except Exception as e:
        return dict(ok=False, err=str(e)[:180], detik=round(time.time()-t0,1))

    # ← KUNCI: pakai raw_decode bertahap (JSON menempel + 'data: [DONE]')
    dec = json.JSONDecoder(); i = 0; objs = []
    while i < len(mentah):
        while i < len(mentah) and mentah[i] not in '{[': i += 1
        if i >= len(mentah): break
        try:
            o, j = dec.raw_decode(mentah, i); objs.append(o); i = j
        except Exception: i += 1
    usage, mdl, jawab = {}, '?', ''
    for o in objs:
        if isinstance(o, dict):
            if o.get('usage'): usage = o['usage']
            if o.get('model'): mdl = o['model']
            try: jawab = o['choices'][0]['message'].get('content') or jawab
            except Exception: pass
    return dict(ok=bool(usage), masuk=usage.get('prompt_tokens',0),
                keluar=usage.get('completion_tokens',0),
                total=usage.get('total_tokens',0),
                reasoning=usage.get('completion_tokens_details',{}).get('reasoning_tokens',0),
                detik=round(dt,1), model=mdl,
                rp=round(usage.get('total_tokens',0)*TARIF_RP),
                jawab=jawab[:110].replace('\n',' '))

TEKS = subprocess.run(['docker','exec',CT,'cat','/tmp/tesis.txt'],
                      capture_output=True, text=True).stdout
print(f'TEKS TESIS BOS (sampai BAB III): {len(TEKS):,} karakter')
print(f'Combo: {MODEL} · tarif Rp {TARIF_RP}/token')
print('='*76)

hasil=[]
uji = [
    ('1. Tanya ringan (13 tok)',        'Sebutkan 1+1. Jawab singkat.'),
    ('2. BAB I saja (22.333 kar)',      'Baca naskah ini. Sebutkan judul, jumlah bab yang ADA, metode, dan 2 saran perbaikan.\n\n'+TEKS[7667:30000]),
    ('3. SELURUH tesis s.d. BAB III (63.797 kar)', 'Baca naskah ini. Sebutkan judul, jumlah bab yang ADA, metode, dan 2 saran perbaikan.\n\n'+TEKS),
]
for label, prompt in uji:
    h = panggil(prompt)
    hasil.append((label, len(prompt), h))
    if h.get('ok'):
        print(f"{label}")
        print(f"   ✅ masuk={h['masuk']:,} tok · keluar={h['keluar']:,} tok (reasoning {h['reasoning']:,})")
        print(f"      total={h['total']:,} tok · {h['detik']}s · {h['model']}")
        print(f"      BIAYA = Rp {h['rp']:,}")
        print(f"      jawab: {h['jawab']}")
    else:
        print(f'{label}\n   ❌ {h}')
    print('-'*76)
    time.sleep(3)

json.dump(hasil, open('/tmp/uji_token.json','w'), indent=1)
print('\n✓ tersimpan /tmp/uji_token.json')
