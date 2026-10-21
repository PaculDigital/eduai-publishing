"""12 KASUS BATAS — diverifikasi ke NASKAH (bukan tebakan indeks).

PELAJARAN: indeks baris BERGESER antar-perubahan susun()/buang_daftar_isi().
⇒ JANGAN pakai indeks hardcoded. Cara aman: CARI baris lewat ISI TEKSNYA
   (substring unik), lalu ambil indeksnya dari pembacaan NASKAH yang sama.

Semua kunci dibaca dari naskah + JENDELA tetangganya.
Kategori:
  N baris ANGKA TABEL        → BUKAN
  H kepala kolom / header     → BUKAN
  K keterangan gambar/tabel   → BUKAN
  S fragmen sitasi / "(…)"    → BUKAN
  B butir daftar              → BUKAN
  J judul bernomor bertingkat → JUDUL
  T judul bagian sah          → JUDUL
"""
from __future__ import annotations

import json
import sys

sys.path.insert(0, '/app')

from app import ai, models                               # noqa: E402
from app.ai import SessionLocal, UPLOAD_DIR              # noqa: E402


def baris_fid(fid: int) -> list[str]:
    db = SessionLocal()
    fb = db.get(models.FileBerkas, fid)
    p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
    return (ai._teks_dari_berkas(p, fb.nama or '') or '').split('\n')


#  (fid, CIRI UNIK baris, kunci, kategori, alasan-yang-DIBACA-dari-naskah)
KASUS = [
    # ── N: baris ANGKA TABEL (paling keras — nol kata) ──
    (81, '3 | 4 | 4 | 4 | 4 | 4 | 4 | 4', 'BUKAN', 'N',
     'baris angka tabel kuesioner — deret nilai, nol kata'),
    (81, '3 | 4 | 4 | 4 | 3 | 4 | 3 | 2', 'BUKAN', 'N',
     'baris angka tabel kuesioner — deret nilai, nol kata'),
    (81, '4 | 3 | 3 | 4 | 4 | 3 | 4 | 4', 'BUKAN', 'N',
     'baris angka tabel kuesioner — deret nilai, nol kata'),
    # ── H: kepala kolom & header tabel ──
    (81, 'X1.1 | X1.2 | X1.3', 'BUKAN', 'H',
     'kepala kolom tabel — kode item dipisah garis tegak'),
    (81, '23 | Usaha saya menerapkan praktik kerja', 'BUKAN', 'H',
     'baris isi tabel kuesioner — nomor+teks+kode item'),
    # ── K: keterangan gambar/tabel ──
    (81, 'Hasil Pra-Survei Variabel Digital Marketing', 'BUKAN', 'K',
     'keterangan di atas tabel — bukan kepala bagian'),
    # ── H: header tabel (fid=115, temuan U-KUNCI) ──
    (115, 'Kategori Hasil Kutipan Informan', 'BUKAN', 'H',
     'header tabel hasil analisis SWOT — diikuti "(Divisi …)"'),
    (115, 'Strengths - Model praktis', 'BUKAN', 'H',
     'kepala kolom tabel SWOT — diikuti butir "- Pelanggan …"'),
    # ── S: fragmen sitasi/kurung ──
    (115, 'AyuMeera)', 'BUKAN', 'S',
     'fragmen penutup kutipan wawancara — potongan nama'),
    (115, '(Divisi AyuMeera)', 'BUKAN', 'S',
     'keterangan sumber di dalam tabel, dalam kurung'),
    # ── T: judul bagian SAH ──
    (115, '3. Tinjauan Literatur', 'JUDUL', 'T',
     'judul bagian berdiri sendiri, diikuti paragraf baru'),
    # ── B: butir daftar ──
    (115, '2. Wawancara', 'BUKAN', 'B',
     'butir daftar metode, diikuti penjelasan "Wawancara merupakan kegiatan…"'),
]


def main():
    cache: dict[int, list[str]] = {}
    keluar = []
    for fid, ciri, kunci, kat, sebab in KASUS:
        b = cache.setdefault(fid, baris_fid(fid))
        idx = [j for j, s in enumerate(b) if ciri in s]
        if not idx:
            print(f'  ❌ TIDAK KETEMU fid={fid} {ciri[:40]!r}')
            continue
        i = idx[0]
        jendela = [f'L{j:06d}| {b[j][:80]}'
                   for j in range(max(0, i - 2), min(len(b), i + 3))]
        keluar.append({'fid': fid, 'i': i, 'kode': kat, 'teks': b[i][:80],
                       'jendela': jendela, 'kunci_asli': kunci, 'sebut': sebab})
        print(f'  ✅ {kat:<2} {kunci:<5} fid={fid} L{i:06d} {b[i][:46]!r}')

    json.dump(keluar, open('/app/BATAS_12.json', 'w'),
              ensure_ascii=False, indent=1)
    from collections import Counter
    print(f'\n→ {len(keluar)} kasus batas · '
          f'sebaran: {dict(Counter(x["kunci_asli"] for x in keluar))} · '
          f'kategori: {dict(Counter(x["kode"] for x in keluar))}')


if __name__ == '__main__':
    sys.exit(main())
