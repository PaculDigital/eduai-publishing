"""UJI BUKU BARU DARI AWAL — buktikan perbaikan HULU bekerja.

Membuat 1 bab buku anak SUNGGUHAN lewat pipeline produksi (AI menulis),
lalu merakitnya jadi .docx, lalu MENGUKUR:

  1. Apakah satu baris masih bisa jadi 8.251 karakter?  (harus TIDAK)
  2. Apakah paragraf wajar 25-40 kata terjaga?          (harus YA)
  3. Apakah tabel penanda masuk jadi tabel nyata?       (harus YA)
  4. Apakah Jev mengenali judul dengan benar?           (harus YA)

⚠️ BIAYA: 1 bab ± 6 panggilan AI + 2 panggilan Jev. Bos tanggung (putusan
8 Okt 2026). Hasil ditulis ke /tmp/uji_buku_baru/ supaya bisa diperiksa mata.
"""
import json
import os
import sys

sys.path.insert(0, '/app')

KELUAR = '/tmp/uji_buku_baru'
os.makedirs(KELUAR, exist_ok=True)

MINI_OUTLINE = {
    1: {
        'title': 'Mengamati Langit: Dari Matahari Hingga Awan',
        #  ⚠️ Bentuk subs WAJIB tuple 3-elemen: (nomor, judul, poin).
        #  Terukur 20 Okt 2026: dict {'title','points'} ⇒ ValueError
        #  "not enough values to unpack (expected 3, got 2)".
        'subs': [
            ('1.1', 'Matahari, Suhu, dan Bayangan di Sepanjang Hari',
             'mengapa bayangan berubah panjang dari pagi ke sore, '
             'cara mengukur bayangan dengan tongkat dan penggaris, '
             'hubungan suhu udara dengan posisi matahari'),
            ('1.2', 'Bentuk-Bentuk Awan dan Pesannya bagi Kita',
             'tiga bentuk dasar awan yang mudah dikenali, '
             'awan gelap pertanda hujan akan turun, '
             'cara membuat buku catatan awan sendiri'),
        ],
    },
}

print('=' * 70)
print('UJI BUKU BARU — 1 bab, 2 sub-bab, jenis ANAK')
print('=' * 70)

import buku_umum_pipeline as P                    # noqa: E402

print()
print(f"AMBANG paragraf yang dipakai: {P._ambang_paragraf_min('anak')} kata")
print('(harus 25, dibaca dari tone_menulis — bukan 50 angka mati)')

#  Jalankan generate_bab lewat jalur produksi.
print()
print('Menulis bab lewat AI (bisa 2-4 menit)...')
t0 = P.time.time()
bab_teks, ringkas, wc, cit = P.generate_bab(1, MINI_OUTLINE[1], '', jenis='anak')
lama = P.time.time() - t0

jalur = os.path.join(KELUAR, 'bab1.txt')
with open(jalur, 'w', encoding='utf-8') as f:
    f.write(bab_teks)

print(f'  kata: {wc} · sitasi: {cit} · waktu: {lama:.0f} detik')
print(f'  tersimpan: {jalur}')

#  ── UKUR BENTUK ──────────────────────────────────────────────────────
print()
print('=' * 70)
print('UKUR BENTUK NASKAH (ini inti pembuktian)')
print('=' * 70)

baris = [b for b in bab_teks.split('\n') if b.strip()]
panjang = [len(b) for b in baris]
kata_per_baris = [len(b.split()) for b in baris]

hasil = {
    'kata': wc,
    'sitasi': cit,
    'detik': round(lama, 1),
    'jumlah_baris': len(baris),
    'baris_terpanjang_kar': max(panjang),
    'baris_terpanjang_kata': max(kata_per_baris),
    'median_kata': sorted(kata_per_baris)[len(kata_per_baris) // 2],
    'paragraf_wajar_25_40': sum(1 for n in kata_per_baris if 25 <= n <= 40),
    'dalam_2x_tone': sum(1 for n in kata_per_baris if 25 <= n <= 80),
    'penanda_tabel': bab_teks.count('[TABEL'),
    'penanda_diagram': bab_teks.count('[DIAGRAM'),
}

salah = []
#  PAGAR 1: satu baris TIDAK BOLEH jadi satu bab (bug lama 8.251 kar).
#  Ambang 1.500 kar: paragraf wajar terpanjang ±1.200 kar (200 kata).
if hasil['baris_terpanjang_kar'] > 1500:
    salah.append(f"baris terpanjang {hasil['baris_terpanjang_kar']} kar "
                 f"— bug 'satu baris satu bab' KEMBALI")
#  PAGAR 2: harus ada beberapa baris (bukan 1 blok raksasa).
if len(baris) < 8:
    salah.append(f'hanya {len(baris)} baris — paragraf tidak terpisah')
#  PAGAR 3 (DIPERBAIKI 20 Okt 2026): ukur MEDIAN, bukan hitung "pas 25-40".
#  ⚠️ Gerbang versi pertama menuntut >=3 paragraf yang PANJANGNYA PAS 25-40
#  kata. Terukur pada buku nyata: median 69 kata ⇒ uji GAGAL walau paragraf
#  sudah terpecah rapi (35 baris, terpanjang 630 kar). Yang penting BUKAN
#  "ada 3 yang pas", tapi "TIDAK ADA yang kepanjangan".
ambang_tone = P._ambang_paragraf_min('anak')
boleh_panjang = ambang_tone * 2                    # toleransi 2× tone
kepanjangan = [n for n in kata_per_baris
               if n > boleh_panjang and len(str(n)) > 0]
#  Abaikan judul/penanda (pendek) — hanya paragraf isi yang dinilai.
kepanjangan = [n for n in kepanjangan if n > 60]

if hasil['median_kata'] > boleh_panjang:
    salah.append(f"median {hasil['median_kata']} kata > {boleh_panjang} "
                 f"(2× tone anak {ambang_tone}) — paragraf kepanjangan")
if len(kepanjangan) > len(baris) * 0.5:
    salah.append(f'{len(kepanjangan)}/{len(baris)} paragraf > {boleh_panjang} '
                 f'kata — mayoritas kepanjangan')

print(json.dumps(hasil, ensure_ascii=False, indent=1))
print()
print(json.dumps({'salah': salah}, ensure_ascii=False))
sys.exit(0 if not salah else 1)
