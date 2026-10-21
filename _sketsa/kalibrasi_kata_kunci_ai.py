"""KALIBRASI PAGAR KATA KUNCI AI (13 Okt 2026).

TUJUAN — menjawab kekhawatiran Bos: "jangan sampai AI merekomendasikan tapi
artikel setelah dicari tidak ada / variabel tidak ada / halusinasi."

CARA — 10 judul NYATA (berbagai bidang, termasuk yang SULIT), lalu ukur:
   1. AI berhasil memetakan jadi konsep? (dan berapa lama)
   2. Hasil pencarian: berapa artikel NYATA yang ditemukan?
   3. Berapa yang TERVERIFIKASI (DOI lolos CrossRef)?
   4. Apakah konsep yang disusun AI memang MUNCUL di judul artikel hasil?

Jalankan DI DALAM container eduai-app.
"""
import sys
import time
sys.path.insert(0, '/app')

import asyncio
import json
import re

import app.ai as A
import app.pustaka as P

#  ⚠️ 10 JUDUL NYATA — dipilih mewakili bidang berbeda + tingkat kesulitan
#     berbeda. 4 terakhir SENGAJA SULIT (kata umum: faktor/analisis/peran).
JUDUL = [
    # ── mudah: variabel jelas, umum ──
    ('pengaruh kualitas produk terhadap keputusan pembelian', 'Manajemen'),
    ('pengaruh motivasi terhadap kinerja karyawan', 'Manajemen'),
    ('pengaruh literasi digital terhadap hasil belajar', 'Pendidikan'),
    ('pengaruh kepemimpinan terhadap kepuasan kerja', 'Manajemen'),
    # ── sedang: multi-variabel / bidang lain ──
    ('Pengaruh Kualitas Layanan dan Kepercayaan terhadap Loyalitas Pelanggan', 'Manajemen'),
    ('Pengaruh Media Pembelajaran Interaktif terhadap Minat Belajar Siswa', 'Pendidikan'),
    ('Pengaruh Stres Kerja terhadap Kinerja Perawat di Rumah Sakit', 'Kesehatan'),
    ('Pengaruh Modal Usaha dan Inovasi terhadap Kinerja UMKM', 'Ekonomi'),
    # ── SULIT: kata umum, tidak ada di kamus, variabel kabur ──
    ('Analisis Faktor-Faktor yang Mempengaruhi Kepuasan Pelanggan E-Commerce di Indonesia', 'Manajemen'),
    ('Peran Mediasi Kepuasan Kerja pada Hubungan Kepemimpinan dan Kinerja Karyawan', 'Manajemen'),
]

PROMPT = '''Kamu ahli metodologi penelitian. Dari JUDUL penelitian, hasilkan KONSEP pencarian literatur.

JUDUL: {judul}

ATURAN:
- Abaikan kata umum (analisis, faktor-faktor, mempengaruhi, pengaruh, studi, hubungan).
- Ambil VARIABEL inti + OBJEK/POPULASI + KONTEKS.
- Tiap konsep: 2-4 sinonim INGGRIS (untuk Scopus/OpenAlex) + sinonim INDONESIA (untuk Garuda).
- Maksimal 4 konsep, urut dari paling penting.
- Kalau judul tidak punya variabel yang jelas, TETAP coba (jangan bilang tidak bisa).

Balas HANYA JSON: {{"konsep":[{{"nama":"..","en":[".."],"id":[".."]}}]}}'''


def konsep_ai(judul: str) -> tuple[list | None, float]:
    """Panggil AI 9router → daftar konsep. Kembalikan (konsep, lama)."""
    t = time.time()
    try:
        jawab, _ = asyncio.run(A._panggil_9router(PROMPT.format(judul=judul), 60))
        lama = time.time() - t
    except Exception as e:                                        # noqa: BLE001
        print('   AI GAGAL:', str(e)[:120])
        return None, time.time() - t
    m = re.search(r'\{.*\}', jawab or '', re.S)
    if not m:
        return None, lama
    try:
        d = json.loads(m.group(0))
        k = d.get('konsep') or []
        return (k if k else None), lama
    except Exception:                                             # noqa: BLE001
        return None, lama


def main() -> None:
    print('=' * 74)
    print('KALIBRASI PAGAR KATA KUNCI AI — %d judul nyata' % len(JUDUL))
    print('=' * 74)
    baris = []
    for i, (judul, bidang) in enumerate(JUDUL, 1):
        print()
        print('%2d. [%s] %s' % (i, bidang, judul[:70]))
        k, lama = konsep_ai(judul)
        if not k:
            print('    ❌ AI TIDAK berhasil memetakan (%.1f dtk)' % lama)
            baris.append({'judul': judul, 'bidang': bidang, 'konsep': [],
                          'lama_ai': lama, 'artikel': 0, 'verified': 0,
                          'nyambung': 0, 'sumber': {}, 'gagal': True})
            continue
        print('    ✅ konsep: %s  (%.1f dtk)' % (
            ' | '.join(x.get('nama', '?') for x in k), lama))

        #  Pakai rumus yang SUDAH ADA — jangan bikin mesin baru
        q_scopus = P.rumus_scopus(k)
        en = [w for x in k for w in (x.get('en') or [])]
        idk = [w for x in k for w in (x.get('id') or [])]

        t2 = time.time()
        hasil = P.cari_semua_from_konsep(k) if hasattr(P, 'cari_semua_from_konsep') else None
        if hasil is None:
            #  cari_semua() normal pakai KAMUS — untuk uji ini kita panggil
            #  mesin langsung dengan konsep AI (persis yang akan dipakai).
            semua, jumlah = [], {}
            for nama, hs in (
                ('Scopus', P.cari_scopus(en, query_siap=q_scopus)),
                ('OpenAlex', P.cari_openalex(en, idk, frasa=P.rumus_openalex(k))),
                ('Garuda', P.cari_garuda(P.konsep_id(k)[:3])),
                ('CrossRef', P.cari_crossref(en, frasa=P.rumus_crossref(k))),
            ):
                jumlah[nama] = len(hs)
                semua.extend(hs)
            unik = {}
            for r in semua:
                kunci = P._kunci_dedup(r)
                if kunci and kunci not in unik:
                    unik[kunci] = r
            daftar = list(unik.values())
            daftar = [r for r in daftar
                      if not r.get('year')
                      or P.TAHUN_AWAL <= int(r['year']) <= P.TAHUN_AKHIR]
            kw = {'en': en, 'id': idk, 'konsep': k, 'sisa': []}
            sebelum = len(daftar)
            daftar = [r for r in daftar if P._nyambung(r, kw)]
            hasil = {'artikel': daftar, 'jumlah_per_sumber': jumlah,
                     'sebelum_saring': sebelum}
        lama_cari = time.time() - t2

        #  Audit DOI — pagar anti-halusinasi
        ver = 0
        for r in hasil['artikel']:
            if r.get('doi'):
                r['doi_status'] = ('verified' if P.audit_doi(r['doi'])
                                   else 'unverified')
                ver += 1 if r['doi_status'] == 'verified' else 0
            else:
                r['doi_status'] = 'no_doi'

        print('    cari: %s → %d unik → %d nyambung → %d verified (%.1f dtk)'
              % (hasil['jumlah_per_sumber'], hasil.get('sebelum_saring', 0),
                 len(hasil['artikel']), ver, lama_cari))
        for a in hasil['artikel'][:3]:
            print('        · %s [%s]' % ((a.get('title') or '')[:58],
                                         a.get('doi_status')))
        baris.append({'judul': judul, 'bidang': bidang,
                      'konsep': [x.get('nama') for x in k],
                      'lama_ai': round(lama, 1),
                      'lama_cari': round(lama_cari, 1),
                      'artikel': len(hasil['artikel']),
                      'verified': ver, 'sumber': hasil['jumlah_per_sumber']})

    #  ── RINGKASAN ANGKA ──
    print()
    print('=' * 74)
    print('RINGKASAN')
    print('=' * 74)
    n = len(baris)
    ada = sum(1 for b in baris if b['artikel'] > 0)
    ver = sum(1 for b in baris if b['verified'] > 0)
    gagal = sum(1 for b in baris if b.get('gagal'))
    print('AI berhasil memetakan   : %d / %d' % (n - gagal, n))
    print('Dapat artikel > 0       : %d / %d' % (ada, n))
    print('Dapat artikel VERIFIED  : %d / %d' % (ver, n))
    print('Rata-rata lama AI       : %.1f dtk'
          % (sum(b['lama_ai'] for b in baris) / n))
    print()
    print('%-58s %5s %5s' % ('JUDUL', 'ART', 'VER'))
    for b in baris:
        print('%-58s %5d %5d' % (b['judul'][:58], b['artikel'], b['verified']))
    print()
    json.dump(baris, open('/tmp/kalibrasi_kata_kunci.json', 'w'),
              ensure_ascii=False, indent=1)
    print('hasil disimpan: /tmp/kalibrasi_kata_kunci.json')


if __name__ == '__main__':
    main()
