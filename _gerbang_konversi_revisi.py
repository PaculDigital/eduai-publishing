#!/usr/bin/env python3
"""GERBANG TAHAP 3 & 4 KONVERSI — SIMPAN HASIL, TOKEN, REVISI PER-ITEM.

WAJIB dari DALAM container:
    docker cp _gerbang_konversi_revisi.py eduai-app:/app/
    docker exec -w /app eduai-app python3 _gerbang_konversi_revisi.py

MENGUJI:
  [A] RAKIT & SIMPAN HASIL (anti tekan-back) : artikel → teks + baris 'beres'
  [B] GAGAL TEKNIS → jatah KEMBALI           : kuota tidak hilang
  [C] TOKEN REVISI = 2 per item              : 1 item=2 · 2 item=4 (§N no.9)
  [D] PESAN REVISI terbatas pada item pilih  : AI tak boleh rombak semua
  [E] TERAPKAN REVISI hanya kunci balik AI   : item lain UTUH
  [F] DAFTAR REVISI lengkap (bagian + 11 elemen)
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, '/app')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import konversi                                              # noqa: E402
from app.models import Base, FileBerkas, KonversiNaskah, User         # noqa: E402

LULUS = 0
GAGAL = 0


def cek(nama, benar, bukti=''):
    global LULUS, GAGAL
    if benar:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama}' + (f'  → {bukti}' if bukti else ''))


def db_baru():
    b = '/tmp/gerbang_konversi_revisi.sqlite'
    if os.path.exists(b):
        os.remove(b)
    eng = create_engine(f'sqlite:///{b}')
    Base.metadata.create_all(eng)
    return sessionmaker(bind=eng)()


def user(db, paket='peneliti', email='u@uji.id'):
    u = User(nama='Uji', email=email, paket=paket, password_hash='x')
    db.add(u); db.commit(); return u


def naskah(db, uid, nama='n.docx'):
    f = FileBerkas(user_id=uid, nama=nama, nama_simpan=nama,
                   ukuran=99, tipe='application/docx')
    db.add(f); db.commit(); return f


ARTIKEL = {
    'judul': 'Pengaruh Harga terhadap Keputusan Pembelian',
    'penulis': [{'nama': 'Budi Santoso', 'email': 'budi@univ.ac.id',
                 'afiliasi': 'Universitas Uji'}],
    'abstrak_id': 'a' * 400,
    'kata_kunci': ['harga', 'keputusan pembelian'],
    'abstract_en': 'b' * 400,
    'keywords': ['price', 'purchase decision'],
    'pendahuluan': 'p' * 500,
    'metode': 'm' * 500,
    'hasil_pembahasan': 'h' * 500,
    'kesimpulan': 'k' * 500,
    'daftar_pustaka': ['Santoso, B. (2020). Buku A.', 'Aminah, S. (2021). Artikel B.'],
    'lampiran': ['Tabel mentah A', 'Grafik B'],
    'elemen': {k: f'kutipan {k}' for k, _l, _t in konversi.ELEMEN_11},
}


def main() -> int:
    print('══ GERBANG TAHAP 3 & 4 KONVERSI ══')
    db = db_baru()

    #  ── [A] RAKIT & SIMPAN HASIL ───────────────────────────────────────
    print('\n[A] RAKIT & SIMPAN HASIL (anti tekan-back)')
    teks = konversi.artikel_ke_teks(ARTIKEL)
    cek('teks memuat judul', 'Pengaruh Harga' in teks, teks[:60])
    cek('teks memuat penulis + email', 'Budi Santoso' in teks
        and 'budi@univ.ac.id' in teks, '')
    cek('teks memuat ABSTRAK & ABSTRACT', 'ABSTRAK' in teks and 'ABSTRACT' in teks, '')
    cek('teks memuat 4 bagian IMRAD',
        all(x in teks for x in ('PENDAHULUAN', 'METODE', 'HASIL DAN PEMBAHASAN',
                                'KESIMPULAN')), '')
    cek('teks memuat DAFTAR PUSTAKA bernomor', '1. Santoso, B. (2020)' in teks, '')
    cek('teks memuat LAMPIRAN', 'LAMPIRAN' in teks, '')

    u1 = user(db, 'peneliti', 'a1@uji.id')
    f1 = naskah(db, u1.id, 'a1.docx')
    from app import kuota
    kuota.potong_konversi(db, u1, f1.id)
    hasil = konversi.simpan_hasil(db, u1, f1.id, ARTIKEL, jenis='kuantitatif')
    cek('simpan_hasil → tersimpan', hasil['tersimpan'] is True, str(hasil)[:80])
    baris = db.query(KonversiNaskah).filter(KonversiNaskah.file_id == f1.id).first()
    cek("status baris = 'beres'", baris.status == 'beres', baris.status)
    cek('hasil_json memuat artikel', 'Pengaruh Harga' in (baris.hasil_json or ''), '')

    #  ── [B] GAGAL TEKNIS → JATAH KEMBALI ───────────────────────────────
    print('\n[B] GAGAL TEKNIS → jatah KEMBALI (user tak dirugikan)')
    u2 = user(db, 'peneliti', 'a2@uji.id')
    f2 = naskah(db, u2.id, 'a2.docx')
    kuota.potong_konversi(db, u2, f2.id)
    cek('sebelum gagal: sisa = 0', kuota.jatah_konversi(db, u2)['sisa'] == 0, '')
    konversi.gagalkan(db, u2, f2.id, 'AI timeout saat konversi')
    cek('setelah gagalkan: sisa = 1 (KEMBALI)',
        kuota.jatah_konversi(db, u2)['sisa'] == 1,
        str(kuota.jatah_konversi(db, u2)))
    b2 = db.query(KonversiNaskah).filter(KonversiNaskah.file_id == f2.id).first()
    cek("status = 'gagal'", b2.status == 'gagal', b2.status)
    cek('alasan galat tersimpan', 'timeout' in (b2.galat or ''), b2.galat)

    #  ── [C] TOKEN REVISI ───────────────────────────────────────────────
    #  ⚠️ DIPERBARUI 15 Okt 2026: BAGIAN artikel tetap 2 token; ELEMEN MUTU
    #     BERTINGKAT Berat 5 / Sedang 3 / Standar 2 (putusan Bos 15 Okt).
    #     Contoh lama (Abstrak + Novelty = 4) kini menjadi 2 + 3 = 5.
    print('\n[C] TOKEN REVISI = 2 per BAGIAN · elemen mutu bertingkat 5/3/2')
    cek('konstanta TOKEN_PER_REVISI = 2', konversi.TOKEN_PER_REVISI == 2, '')
    h1 = konversi.hitung_biaya_revisi(['abstrak_id'])
    cek('1 item BAGIAN (Abstrak) = 2 token', h1['token'] == 2, str(h1))
    h2 = konversi.hitung_biaya_revisi(['abstrak_id', 'elemen:novelty'])
    cek('Abstrak (2) + Novelty (3) = 5 token', h2['token'] == 5, str(h2))
    cek('   jumlah item tetap 2', h2['jumlah'] == 2, str(h2))
    h2b = konversi.hitung_biaya_revisi(['elemen:state_of_art'])
    cek('elemen BERAT (state_of_art) = 5 token', h2b['token'] == 5, str(h2b))
    h2c = konversi.hitung_biaya_revisi(['elemen:hook'])
    cek('elemen STANDAR (hook) = 2 token', h2c['token'] == 2, str(h2c))
    h3 = konversi.hitung_biaya_revisi([])
    cek('0 item = 0 token', h3['token'] == 0, str(h3))
    h4 = konversi.hitung_biaya_revisi(['judul', 'metode', 'kesimpulan'])
    cek('3 item BAGIAN = 6 token', h4['token'] == 6, str(h4))

    #  ── [D] PESAN REVISI TERBATAS ──────────────────────────────────────
    print('\n[D] PESAN REVISI — hanya item yang dipilih')
    pesan = konversi.susun_pesan_revisi(ARTIKEL, ['abstrak_id'],
                                        catatan_pengguna='perkuat angka')
    cek('pesan sebut item yang diminta', 'abstrak_id' in pesan, '')
    cek('pesan memuat catatan penulis', 'perkuat angka' in pesan, '')
    cek('pesan melarang ubah item lain', 'JANGAN mengubah item lain' in pesan, '')
    cek('pesan memuat artikel sekarang', 'Pengaruh Harga' in pesan, '')
    cek('pesan minta JSON sah', 'JSON' in pesan, '')

    pesan2 = konversi.susun_pesan_revisi(ARTIKEL, ['elemen:novelty'])
    cek('pesan revisi ELEMEN terbaca', 'novelty' in pesan2.lower(), '')

    #  ── [E] TERAPKAN REVISI ────────────────────────────────────────────
    print('\n[E] TERAPKAN REVISI — hanya kunci yang dikirim AI')
    asli = dict(ARTIKEL)
    baru = konversi.terapkan_revisi(
        ARTIKEL, {'abstrak_id': 'ABSTRAK BARU', 'elemen': {'novelty': 'NOVEL BARU'}})
    cek('abstrak_id terbarui', baru['abstrak_id'] == 'ABSTRAK BARU', baru['abstrak_id'])
    cek('elemen novelty terbarui',
        (baru.get('elemen') or {}).get('novelty') == 'NOVEL BARU', '')
    cek('judul TIDAK berubah (di luar pilihan)',
        baru['judul'] == asli['judul'], baru['judul'])
    cek('metode TIDAK berubah', baru['metode'] == asli['metode'], '')
    cek('11 elemen lain UTUH',
        len(baru.get('elemen') or {}) == 11, str(len(baru.get('elemen') or {})))
    cek('ARTIKEL ASLI tidak dirusak (salinan)',
        ARTIKEL['abstrak_id'] == 'a' * 400, ARTIKEL['abstrak_id'][:20])

    #  revisi elemen lewat kunci langsung (tanpa 'elemen:')
    baru2 = konversi.terapkan_revisi(ARTIKEL, {'limitasi': 'LIMIT BARU'})
    cek('elemen lewat kunci langsung juga jalan',
        (baru2.get('elemen') or {}).get('limitasi') == 'LIMIT BARU', '')

    #  ── [F] DAFTAR REVISI ──────────────────────────────────────────────
    print('\n[F] DAFTAR REVISI — bagian + 11 elemen')
    d = konversi.daftar_revisi(ARTIKEL)
    cek('jumlah item = 8 bagian + 11 elemen = 19', len(d) == 19, str(len(d)))
    #  ⚠️ DIPERBARUI 15 Okt 2026: elemen mutu kini BERTINGKAT (5/3/2),
    #     bagian artikel tetap 2. Putusan Bos: "harga bisa saya variasi
    #     tidak seragam 2 token, karena beban kerja ai juga lebih banyak".
    _bagian = [x for x in d if not str(x['kunci']).startswith('elemen:')]
    _elemen = [x for x in d if str(x['kunci']).startswith('elemen:')]
    cek('semua BAGIAN token = 2', all(x['token'] == 2 for x in _bagian),
        str({x['kunci']: x['token'] for x in _bagian if x['token'] != 2}))
    cek('semua ELEMEN token ada di {2,3,5}',
        all(x['token'] in (2, 3, 5) for x in _elemen),
        str({x['kunci']: x['token'] for x in _elemen
             if x['token'] not in (2, 3, 5)}))
    cek('elemen berat = 5 (state_of_art & diskusi_komparatif)',
        all(x['token'] == 5 for x in _elemen
            if x['kunci'] in ('elemen:state_of_art', 'elemen:diskusi_komparatif')),
        str({x['kunci']: x['token'] for x in _elemen
             if x['kunci'] in ('elemen:state_of_art', 'elemen:diskusi_komparatif')}))
    cek('harga TIDAK seragam semua (bukti bertingkat)',
        len({x['token'] for x in _elemen}) > 1,
        str(sorted({x['token'] for x in _elemen})))
    cek('semua item ADA terisi', all(x['ada'] for x in d),
        str([x['kunci'] for x in d if not x['ada']]))
    cek('ada item elemen: hook', any(x['kunci'] == 'elemen:hook' for x in d), '')

    d_kosong = konversi.daftar_revisi({'judul': 'X'})
    cek('artikel kosong → item tidak ada isinya',
        sum(1 for x in d_kosong if x['ada']) == 1,
        str(sum(1 for x in d_kosong if x['ada'])))

    print(f'\n══ HASIL: {LULUS} LULUS / {GAGAL} GAGAL ══')
    return 1 if GAGAL else 0


if __name__ == '__main__':
    sys.exit(main())
