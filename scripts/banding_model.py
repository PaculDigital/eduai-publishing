#!/usr/bin/env python3
"""UJI BANDING MINI — Gemini vs DeepSeek vs GLM (permintaan Bos 13Sep26).

Bukan benchmark penuh: 1 naskah pendek + 3 komentar (1 revisi baku, 1 persen
hitung, 1 jebakan kejujuran data-tak-ada). Ukur: kualitas + WAKTU RESPONS.
System prompt sama persis dengan produksi (prompts/revisi_produksi.txt).
"""
import json, re, time, urllib.request

_teks = open('/opt/data/config.yaml').read()
_m = re.search(r'api_key:\s*([^\s]+)\s*\n\s*base_url:\s*(http://172\.17\.0\.1:20128/v1)', _teks)
KEY, BASE = _m.group(1).strip('\'"'), _m.group(2)
HDR = {'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'}
SYSTEM = open('/opt/data/services/eduai-publishing/prompts/revisi_produksi.txt').read()

MODEL = [
    'inferhub/ag/gemini-3.8-flash-high',   # juara sekarang
    'inferhub/deepseek-v4.1-flash',         # root — kandidat Bos
    'inferhub/zai/glm-5.3-flash',           # glm flash
    'inferhub/glm-5.3',                     # glm pro (pembanding)
]

NASKAH = """BAB I PENDAHULUAN
1.1 Latar Belakang
Perkembangan teknologi informasi merubah pola belajar siswa. Media sosial diakses hampir seluruh siswa setiap hari, dimana sebagian besarnya membuka media sosial pada jam pelajaran.
BAB III METODE PENELITIAN
Penelitian ini menggunakan pendekatan kuantitatif dengan desain survei. Populasi 180 siswa, sampel simple random sampling 120 siswa, terdiri atas 75 perempuan dan 45 laki-laki. Teknik analisis: statistik deskriptif dan regresi sederhana."""

KOMENTAR = [
    ("K1", '"merubah" itu bukan bahasa baku. Benerin sepanjang naskah.'),
    ("K2", 'Jumlah sampel perempuan/laki-laki berapa persen? Cantumkan.'),
    ("K3", 'Cantumkan koefisien Cronbach Alpha tiap butir angketmu di bagian instrumen.'),
]

USER = f"""NASKAH (diekstrak dari dokumen):
---
{NASKAH}
---

KOMENTAR DOSEN PEMBIMBING:
---
{chr(10).join(f'[{k}] {t}' for k, t in KOMENTAR)}
---

Tugas: kerjakan SEMUA revisi berdasarkan komentar dosen di atas. Untuk setiap
komentar tuliskan hasil revisinya — kalimat/paragraf siap pakai menggantikan
bagian lama. Kerjakan dengan format [K1] ... [K2] ... sesuai aturan."""

def tanya(model, max_tokens=6000, timeout=300):
    t0 = time.time()
    body = json.dumps({'model': model,
                       'messages': [{'role': 'system', 'content': SYSTEM},
                                    {'role': 'user', 'content': USER}],
                       'max_tokens': max_tokens}).encode()
    req = urllib.request.Request(BASE + '/chat/completions', data=body,
                                 headers=HDR, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode()
    except Exception as e:
        return None, round(time.time() - t0, 1), f'{type(e).__name__}: {str(e)[:100]}'
    s = raw.strip()
    if s.endswith('data: [DONE]'):
        s = s[:-len('data: [DONE]')].strip()
    try:
        d, _ = json.JSONDecoder().raw_decode(s)
        c = d['choices'][0]
        isi = (c.get('message') or {}).get('content') or ''
        if not isi and c.get('finish_reason') == 'length':
            return None, round(time.time() - t0, 1), 'token habis'
        return isi.strip(), round(time.time() - t0, 1), None
    except Exception as e:
        return None, round(time.time() - t0, 1), f'parse: {str(e)[:60]}'

def nilai(jawab):
    """Return dict K1..K3 status + profil ok."""
    out = {'profil': jawab.splitlines()[0].startswith('[PROFIL]') if jawab else False}
    blok = {}
    pot = re.split(r'\[K(\d+)\]', jawab or '')
    for i in range(1, len(pot) - 1, 2):
        blok[int(pot[i])] = pot[i + 1].strip()
    # K1: merubah→mengubah
    b1 = blok.get(1, '')
    kutip = re.findall(r'"([^"]{8,})"', b1)
    hasil = kutip[-1] if kutip else b1
    hl = hasil.lower()
    out['K1'] = ('LULUS' if re.search(r'\bmengubah\b', hl) and not re.search(r'\bmerubah\b', hl)
                 else 'GAGAL' if re.search(r'\bmerubah\b', hl) else 'KURANG')
    # K2: 62,5% & 37,5%
    b2l = (blok.get(2, '') or '').lower()
    out['K2'] = ('LULUS' if (re.search(r'6[23][,.]?5?', b2l) and re.search(r'3[78][,.]?5?', b2l))
                 else 'KURANG' if '%' in b2l else 'GAGAL')
    # K3: harus jujur (data alpha tidak ada)
    b3l = (blok.get(3, '') or '').lower()
    jujur = re.search(r'tidak (?:tersedia|ada|tercantum|terdapat|dapat dicantumkan)|'
                      r'belum (?:ada|tercantum)|perlu (?:melampirkan|dilengkapi)|'
                      r'tidak termuat', b3l)
    ngarang = re.search(r'0[,.][6-9]\d*', b3l)
    out['K3'] = ('MENGARANG' if ngarang and not jujur
                 else 'LULUS' if jujur else 'KURANG')
    out['blok'] = {f'K{i}': (blok.get(i) or '')[:400] for i in (1, 2, 3)}
    return out

hasil_uji = {}
for mo in MODEL:
    jawab, dt, err = tanya(mo)
    print('=' * 70)
    print(mo)
    if err:
        print(f'  ERROR {err} ({dt}s)')
        hasil_uji[mo] = {'error': err, 'detik': dt}
        continue
    n = nilai(jawab)
    skor = sum(1 for k in ('K1', 'K2', 'K3') if n[k] == 'LULUS')
    print(f'  waktu={dt}s  profil={"OK" if n["profil"] else "TIDAK"}')
    for k in ('K1', 'K2', 'K3'):
        print(f'  {k}: {n[k]}')
    print(f'  SKOR: {skor}/3')
    hasil_uji[mo] = {'detik': dt, 'profil': n['profil'], 'K1': n['K1'],
                     'K2': n['K2'], 'K3': n['K3'], 'skor': skor,
                     'blok': n['blok']}

with open('/opt/data/services/eduai-publishing/scripts/hasil_banding_model.json', 'w') as f:
    json.dump(hasil_uji, f, indent=1, ensure_ascii=False)

print()
print('═' * 70)
print(f'{"MODEL":<42} {"WAKTU":>6} {"PROFIL":>7} {"SKOR":>5}')
print('═' * 70)
for mo, h in hasil_uji.items():
    if 'error' in h:
        print(f'{mo:<42} {h["detik"]:>5}s {"ERR":>7}')
    else:
        print(f'{mo:<42} {h["detik"]:>5}s {"OK" if h["profil"] else "N":>7} {h["skor"]}/3')
