"""HAKIM — menilai hasil revisi dari _uji_mutu_v2.json (TANPA bayar ulang revisi).

KRITERIA BOS (24Sep26, verbatim):
  "ketersambungan makna, cerita, data dan konsisten, terhadap kontek global,
   bab sebelum dan sesudah, sub bab yang terkait. Intinya adalah presisi,
   tepat dan Natural berbahasa nya."

Dijalankan sebagai BERKAS (bukan `python -c`) — pelajaran 24Sep26:
`python -c` dengan kutip bersarang MERUSAK JSON yang dikirim ke 9router.

Hakim = 2 penilai berbeda (biar tidak 1 sudut pandang):
  H1: nilai mutlak 1-5 per butir
  H2: BANDING BUTA (mana yang lebih nyambung? A atau B) — tanpa tahu mana
      yang PENUH vs POTONG (juri tersamar)
"""
import asyncio, json, os, re, sys
sys.path.insert(0, '/app')
from _hakim_mentah import tanya_mentah

DATA = '/app/_uji_mutu_v2.json'
KOMENTAR = ("1. Pada Rumusan Masalah, kaitkan kembali dengan fenomena yang kamu "
            "uraikan di Latar Belakang supaya benang merahnya terlihat.\n"
            "2. Perbaiki kalimat yang terlalu panjang agar lebih mudah dipahami.")

P_NILAI = """Kamu dosen pembimbing yang menilai hasil revisi mahasiswa.

KOMENTAR YANG DIMINTA DIKERJAKAN:
{komentar}

HASIL REVISI YANG DINILAI:
{hasil}

Nilai 1-5 (1=sangat buruk, 5=sangat baik) untuk SETIAP butir:
A. SAMBUNG_MAKNA = nyambung dengan bab sebelum & sesudah, tidak terputus
B. KONSISTEN = istilah/variabel/angka tidak berubah atau bertabrakan
C. PRESISI = benar-benar menjawab komentar, tidak melebar
D. NATURAI = bahasanya wajar seperti manusia, tidak kaku

Balas HANYA satu baris JSON, tanpa penjelasan tambahan:
{{"A": <angka 1-5>, "B": <angka 1-5>, "C": <angka 1-5>, "D": <angka 1-5>, "alasan": "<maks 20 kata>"}}"""

P_HITAM = """Kamu dosen penguji. Dua mahasiswa mengerjakan KOMENTAR yang sama
pada naskah yang sama. Nilai mana hasilnya LEBIH BAIK menurut kriteria:
ketersambungan makna dengan bab sebelum & sesudah, konsistensi istilah/data,
ketepatan menjawab komentar, dan kealamian bahasa.

KOMENTAR:
{komentar}

=== HASIL 1 ===
{h1}

=== HASIL 2 ===
{h2}

Balas HANYA JSON: {{"pemenang": "1" atau "2" atau "seri", "alasan": "<maks 25 kata>"}}"""


def ambil_json(teks):
    m = re.search(r'\{.*\}', teks or '', re.S)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except Exception:
        return {}


async def main():
    data = json.load(open(DATA))
    print('=' * 104)
    print('HAKIM — MUTU POTONGAN vs PENUH (kriteria Bos)')
    print('=' * 104)

    # ── H1: nilai mutlak per tulisan ────────────────────────────────────
    for d in data:
        teks = d.get('hasil_teks', '')
        if not teks:
            d['nilaiH1'] = {}; continue
        try:
            jw, info = await tanya_mentah(P_NILAI.format(komentar=KOMENTAR[:350], hasil=teks[:3500]))
            d['nilaiH1'] = ambil_json(jw)
            d['model_h1'] = info.get('model')
        except Exception as e:
            d['nilaiH1'] = {'err': f'{type(e).__name__}: {str(e)[:60]}'}
        n = d['nilaiH1']
        v = [n.get(k) for k in 'ABCD' if isinstance(n.get(k), int)]
        rata = round(sum(v)/len(v), 2) if v else '-'
        print(f'  {d["naskah"][:22]:<24}{d["sisi"]:<8} rev={d["token_revisi"]} '
              f'kirim={d["kirim_kar"]:>7,}  A={n.get("A","?")} B={n.get("B","?")} '
              f'C={n.get("C","?")} D={n.get("D","?")}  rata={rata}  {str(n.get("alasan",""))[:40]}')

    # ── H2: banding buta (PENUH vs POTONG) ──────────────────────────────
    print(f'\n{"="*104}\nHAKIM 2 — BANDING BUTA (juri tidak tahu mana yang penuh/potong)\n{"="*104}')
    hasil_buta = []
    for nama in dict.fromkeys(d['naskah'] for d in data):
        p = next((d for d in data if d['naskah'] == nama and d['sisi'] == 'PENUH'), None)
        q = next((d for d in data if d['naskah'] == nama and d['sisi'] == 'POTONG'), None)
        if not p or not q:
            continue
        # ACAK urutan (juri tersamar) — dicatat supaya bisa dibalik
        import random
        acak = random.Random(hash(nama) & 0xffff).random() < 0.5
        h1, h2 = (q, p) if acak else (p, q)
        try:
            jw, _ = await tanya_mentah(P_HITAM.format(
                komentar=KOMENTAR[:300], h1=h1.get('hasil_teks','')[:2000],
                h2=h2.get('hasil_teks','')[:2000]))
            j = ambil_json(jw)
            menang = j.get('pemenang', '?')
            # petakan balik: kalau acak, "1"=POTONG
            if menang == 'seri':
                siapa = 'SERI'
            elif acak:
                siapa = {'1': 'POTONG', '2': 'PENUH'}.get(menang, '?')
            else:
                siapa = {'1': 'PENUH', '2': 'POTONG'}.get(menang, '?')
            hasil_buta.append({'naskah': nama, 'menang': siapa, 'alasan': j.get('alasan', '')})
            print(f'  {nama[:24]:<26} pemenang: {siapa:<8} {str(j.get("alasan",""))[:60]}')
        except Exception as e:
            print(f'  {nama[:24]:<26} ❌ {type(e).__name__}: {str(e)[:60]}')
        await asyncio.sleep(1)

    # ── RINGKASAN ───────────────────────────────────────────────────────
    print(f'\n{"="*104}\nRINGKASAN AKHIR\n{"="*104}')
    print(f'{"naskah":<26}{"PENUH (rev)":>14}{"POTONG (rev)":>14}{"hemat":>9}'
          f'{"nilai PENUH":>13}{"nilai POTONG":>14}{"selisih":>9}')
    for nama in dict.fromkeys(d['naskah'] for d in data):
        p = next((d for d in data if d['naskah'] == nama and d['sisi'] == 'PENUH'), None)
        q = next((d for d in data if d['naskah'] == nama and d['sisi'] == 'POTONG'), None)
        if not p or not q: continue
        vp = [p['nilaiH1'].get(k) for k in 'ABCD' if isinstance(p['nilaiH1'].get(k), int)]
        vq = [q['nilaiH1'].get(k) for k in 'ABCD' if isinstance(q['nilaiH1'].get(k), int)]
        rp = sum(vp)/len(vp) if vp else 0; rq = sum(vq)/len(vq) if vq else 0
        tp = p['token_in']+p['token_out']; tq = q['token_in']+q['token_out']
        print(f'{nama[:24]:<26}{p["token_revisi"]:>10} rev{q["token_revisi"]:>10} rev'
              f'{tp/max(1,tq):>8.1f}×{rp:>13.2f}{rq:>14.2f}{rq-rp:>+9.2f}')

    seri = sum(1 for h in hasil_buta if h['menang'] == 'SERI')
    pot = sum(1 for h in hasil_buta if h['menang'] == 'POTONG')
    pen = sum(1 for h in hasil_buta if h['menang'] == 'PENUH')
    print(f'\nJURI BUTA: POTONG menang {pot} · PENUH menang {pen} · SERI {seri}')

    json.dump({'data': data, 'buta': hasil_buta}, open('/app/_uji_mutu_v2_nilai.json', 'w'),
              indent=1, ensure_ascii=False)

asyncio.run(main())
