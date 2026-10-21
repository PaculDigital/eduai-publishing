"""UJI NON-DETERMINISME: apakah hasil beda-beda tapi MAKNANYA SAMA?

Arahan Bos 16Sep26: "Lanjutkan uji kenapa hasil berbeda beda, tapi kalo masih
semantik tidak Masalah. Semantiknya 80% lebih artinya mirip."

MASALAH UJI LAMA: Wulan pakai `similarity()` = Jaccard per-KATA. Itu SALAH
untuk kasus ini — AI mengubah kata (sinonim, susunan) tapi makna tetap sama.
Contoh nyata: 1.190 vs 1.232 kar, Jaccard 0.672 → terbaca "beda" padahal
maknanya bisa identik.

CARA BENAR: ukur KEMIRIPAN MAKNA memakai MODEL AI (semantic similarity),
bukan cocok-cocokan kata. Uji ini memakai 2 lapis:
  Lapis 1 (Rp 0)  : ukur kata kunci akademik yang WAJIB ada (angka, variabel,
                    nama teori, istilah metodologi) — kalau semua sama, makna
                    terjaga.
  Lapis 2 (AI)    : minta model menilai "seberapa mirip MAKNA dua teks ini,
                    dalam persen" — penilai yang mengerti arti.

Jalankan: docker exec -w /app eduai-app python3 _uji_semantik.py
"""
import json
import os
import re
import time
import urllib.request

B = os.getenv('EDUAI_ROUTER_BASE', 'http://172.17.0.1:20128/v1')
K = os.getenv('EDUAI_ROUTER_KEY', '')


def panggil(pesan: str, model: str = 'EduAi', maks: int = 4000) -> dict:
    body = json.dumps({'model': model,
                       'messages': [{'role': 'user', 'content': pesan}],
                       'max_tokens': maks, 'temperature': 0}).encode()
    r = urllib.request.Request(B + '/chat/completions', data=body,
        headers={'Authorization': 'Bearer ' + K, 'Content-Type': 'application/json'})
    t0 = time.monotonic()
    raw = urllib.request.urlopen(r, timeout=300).read().decode('utf-8', 'ignore')
    dt = time.monotonic() - t0
    i = raw.find('data: [DONE]')
    j = json.JSONDecoder().raw_decode(raw[:i] if i > 0 else raw)[0]
    ch = j['choices'][0]
    u = j.get('usage') or {}
    return {'isi': ch['message'].get('content') or '', 'detik': dt,
            'dipakai': j.get('model'), 'finish': ch.get('finish_reason'),
            'tin': u.get('prompt_tokens'), 'tout': u.get('completion_tokens')}


# ── NASKAH UJI + KOMENTAR PEMBIMBING (mirip situasi nyata) ────────────────
NASKAH = """Latar Belakang
Kinerja karyawan merupakan faktor penting bagi keberhasilan organisasi. Fenomena
yang terjadi pada PT Maju Bersama menunjukkan penurunan produktivitas sebesar 12%
selama periode 2023-2024. Penelitian ini mengkaji pengaruh motivasi kerja dan
lingkungan kerja terhadap kinerja karyawan dengan kepuasan kerja sebagai variabel
mediasi. Grand Theory yang digunakan adalah Teori Expectancy dari Vroom (1964).
Penelitian sebelumnya oleh Sari (2022) menemukan motivasi berpengaruh positif
signifikan terhadap kinerja (β=0,432; p<0,05), namun belum menguji peran mediasi.
Gap penelitian ini adalah belum adanya kajian pada sektor manufaktur menengah di
Indonesia. Rumusan masalah: apakah motivasi kerja berpengaruh terhadap kinerja
karyawan? Apakah lingkungan kerja berpengaruh terhadap kinerja karyawan?"""

KOMENTAR = ("Tolong perkaya latar belakang ini dengan data terbaru dan "
            "perkuat bagian gap penelitian. Jangan ubah rumusan masalah.")

print('=' * 96)
print('UJI NON-DETERMINISME — apakah hasil beda KATA tapi sama MAKNA?')
print('=' * 96)
print(f'naskah {len(NASKAH)} kar · komentar {len(KOMENTAR)} kar')
print()

# ── Putaran 1 & 2 dengan pesan IDENTIK ────────────────────────────────────
pesan = (f'NASKAH:\n{NASKAH}\n\nKOMENTAR PEMBIMBING:\n{KOMENTAR}\n\n'
         'Revisi naskah sesuai komentar. Balas HANYA naskah hasil revisi '
         '(maksimal 250 kata).')
hasil = []
for put in (1, 2):
    h = panggil(pesan)
    hasil.append(h)
    print(f"PUTARAN {put}: model={h['dipakai']} · {h['detik']:.1f}s · "
          f"len={len(h['isi'])} · finish={h['finish']} · "
          f"tok={h['tin']}/{h['tout']}")
    print(f"  kutipan: {h['isi'][:150].replace(chr(10),' ')}...")
    print()
    time.sleep(1)

a, b = hasil[0]['isi'], hasil[1]['isi']
print('=' * 96)
print('UKURAN 1 (Rp 0) — KATA KUNCI AKADEMIK YANG WAJIB SAMA')
print('=' * 96)


def kunci(teks):
    """Ambil penanda akademik: angka, %, variabel, teori, nama+thn, istilah."""
    t = teks.lower()
    keluar = set()
    keluar |= set(re.findall(r'\b\d+[.,]?\d*\s*%', t))              # persen
    keluar |= set(re.findall(r'\b(?:19|20)\d{2}\b', t))             # tahun
    for v in ['motivasi kerja', 'lingkungan kerja', 'kinerja karyawan',
              'kepuasan kerja', 'mediasi', 'expectancy', 'vroom',
              'rumusan masalah', 'gap', 'produktivitas', 'manufaktur']:
        if v in t:
            keluar.add(v)
    return keluar


ka, kb = kunci(a), kunci(b)
sama = ka & kb
beda = (ka | kb) - sama
print(f'  kata kunci putaran 1 : {len(ka)} → {sorted(ka)}')
print(f'  kata kunci putaran 2 : {len(kb)} → {sorted(kb)}')
print()
print(f'  SAMA   : {len(sama)}/{len(ka|kb)} = '
      f'{100*len(sama)/max(len(ka|kb),1):.0f}% → {sorted(sama)}')
print(f'  BEDA   : {sorted(beda) if beda else "(tidak ada)"}')

print()
print('=' * 96)
print('UKURAN 2 (Jaccard per-kata — cara LAMA Wulan, hanya pembanding)')
print('=' * 96)


def jaccard(x, y):
    wx = set(re.findall(r'\w+', x.lower()))
    wy = set(re.findall(r'\w+', y.lower()))
    return len(wx & wy) / max(len(wx | wy), 1)


print(f'  Jaccard = {jaccard(a,b):.3f}  ← cara lama, TERLALU KASAR')

print()
print('=' * 96)
print('UKURAN 3 (AI sebagai penilai MAKNA — cara yang benar)')
print('=' * 96)
tanya = f"""Nilai KEMIRIPAN MAKNA (semantik) dua teks berikut, untuk keperluan
akademik. Fokus pada MAKNA, abaikan perbedaan pilihan kata.

TEKS A:
{a[:1800]}

TEKS B:
{b[:1800]}

Balas HANYA JSON: {{"mirip_persen": <0-100>,
"makna_sama": <true|false>,
"yang_berubah": "<ringkas, maks 25 kata>",
"yang_dipertahankan": "<ringkas, maks 25 kata>"}}"""
nm = panggil(tanya, maks=2000)
try:
    js = re.search(r'\{.*\}', nm['isi'], re.S).group(0)
    n = json.loads(js)
    print(f"  Kemiripan makna : {n.get('mirip_persen')}%")
    print(f"  Makna sama?     : {n.get('makna_sama')}")
    print(f"  Yang berubah    : {n.get('yang_berubah')}")
    print(f"  Yang dijaga     : {n.get('yang_dipertahankan')}")
    mirip = n.get('mirip_persen') or 0
    print()
    if mirip >= 80:
        print(f'  ✅ LULUS — {mirip}% ≥ 80% (batas Bos). Beda KATA itu wajar,')
        print('     yang penting MAKNA terjaga.')
    else:
        print(f'  ⚠️ PERHATIAN — {mirip}% < 80%. Makna bergeser, perlu dikejar.')
except Exception as e:
    print('  gagal mengurai jawaban penilai:', e)
    print('  mentah:', nm['isi'][:400])

print()
print(f"  (penilai dipakai: {nm['dipakai']})")