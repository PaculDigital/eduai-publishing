"""GERBANG PORSI ALAT — ID dokumen menentukan alat, bukan tebakan.

ACC Bos 19 Okt 2026 (verbatim):
  "harus punya id sendiri ... agar menggunakan jev dan hakim tepat dan tidak
   salah alat, tau ini dokumen perlu jev, hakim atau tidak, kalo perlu sudah
   sesuai porsinya."

Yang dijaga gerbang ini:
  A. 5 jenis buku PUNYA ID dan ID-nya SAMA dengan kartu di app/buku.py
     (kalau beda, satu buku punya dua identitas → sistem bingung).
  B. Buku TIDAK PERNAH dikirim ke Jev / Hakim.
  C. Skripsi/tesis/disertasi/artikel/proposal TIDAK kehilangan Jev/Hakim.
  D. Setiap jenis punya Standar lengkap (kalau tidak, prompt AI pecah).
  E. ID tak dikenal → SEMUA alat mati (fail-safe, bukan menebak).
  F. Fungsi pembantu konsisten dengan tabel (tidak ada dua kebenaran).

Jalankan:  .venv/bin/python _gerbang_porsi_alat.py
Atau dari dalam container: docker exec eduai-app python _gerbang_porsi_alat.py
"""
import os
import sys

LULUS = GAGAL = 0
PESAN = []


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        PESAN.append(f'  ✅ {nama}')
    else:
        GAGAL += 1
        PESAN.append(f'  ❌ {nama}   {bukti}')


def main():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from app import jenis as J

    # ── A. ID buku ADA dan COCOK dengan kartu Publish Buku ───────────────
    cek('A1 JENIS_BUKU berisi 5 jenis', len(J.JENIS_BUKU) == 5,
        f'dapat {len(J.JENIS_BUKU)}')

    try:
        from app import buku as B
        kode_kartu = [k['kode'] for k in B.JENIS_BUKU]
        # kartu pakai strip (buku-umum), identitas pakai garis bawah (buku_umum)
        kode_identitas = [k.replace('-', '_') for k in kode_kartu]
        cek('A2 ID jenis.py == kode kartu buku.py (setelah normalisasi)',
            sorted(kode_identitas) == sorted(J.JENIS_BUKU),
            f'kartu={sorted(kode_identitas)} vs identitas={sorted(J.JENIS_BUKU)}')
    except Exception as e:
        cek('A2 kartu app/buku.py bisa dibaca', False, type(e).__name__ + ': ' + str(e)[:80])

    # ── B. BUKU tidak pernah ke Jev / Hakim ───────────────────────────────
    for k in J.JENIS_BUKU:
        p = J.porsi_alat(k)
        cek(f'B {k}: jev MATI', p['jev'] is False, f"jev={p['jev']}")
        cek(f'B {k}: hakim MATI', p['hakim'] is False, f"hakim={p['hakim']}")
        cek(f'B {k}: mutu_buku HIDUP', p['mutu_buku'] is True, f"mutu={p['mutu_buku']}")

    # ── C. Naskah akademik TIDAK kehilangan Jev/Hakim ─────────────────────
    for k in J.JENIS_AKADEMIK:
        p = J.porsi_alat(k)
        cek(f'C {k}: jev HIDUP', p['jev'] is True, f"jev={p['jev']}")
        cek(f'C {k}: hakim HIDUP', p['hakim'] is True, f"hakim={p['hakim']}")
        cek(f'C {k}: mutu_buku MATI', p['mutu_buku'] is False, f"mutu={p['mutu_buku']}")

    # ── D. Setiap jenis punya Standar lengkap ─────────────────────────────
    semua = list(J.JENIS_AKADEMIK) + list(J.JENIS_BUKU) + [J.JENIS_UMUM]
    for k in semua:
        s = J.STANDAR.get(k)
        cek(f'D {k}: punya Standar', s is not None, 'tidak ada di STANDAR')
        cek(f'D {k}: punya label', bool(J.LABEL_JENIS.get(k)), 'label kosong')
        cek(f'D {k}: punya porsi alat', k in J.PORSI_ALAT, 'tidak ada di PORSI_ALAT')

    # Buku TIDAK boleh punya hipotesis (itu bahasa skripsi).
    # ⚠️ NOVELTY: bukan aturan seragam. Monograf MEMANG wajib bertumpu pada
    #    temuan (penelitian asal), jadi jangan dipaksa False. Yang dilarang
    #    untuk SEMUA buku: hipotesis & bahasa sidang.
    for k in J.JENIS_BUKU:
        s = J.STANDAR[k]
        cek(f'D {k}: hipotesis_maks = 0 (bukan bahasa skripsi)',
            s.hipotesis_maks == 0, f'maks={s.hipotesis_maks}')
        cek(f'D {k}: hipotesis_min = 0', s.hipotesis_min == 0,
            f'min={s.hipotesis_min}')
    # Novelty wajib hanya untuk monograf (bertumpu temuan penelitian asal)
    cek('D buku_monograf: novelty WAJIB (temuan penelitian asal)',
        J.STANDAR[J.JENIS_BUKU_MONOGRAF].wajib_novelty is True,
        'monograf tanpa temuan = bukan monograf')
    for k in (J.JENIS_BUKU_AJAR, J.JENIS_BUKU_UMUM,
              J.JENIS_BOOK_CHAPTER, J.JENIS_BUKU_REFERENSI):
        cek(f'D {k}: novelty TIDAK wajib',
            J.STANDAR[k].wajib_novelty is False,
            f'novelty={J.STANDAR[k].wajib_novelty}')

    # ── E. ID tak dikenal → semua alat MATI (fail-safe) ───────────────────
    for aneh in ('', None, 'buku', 'buku-buku', 'BUKU_UMUM', 'skripsi_x', '  '):
        p = J.porsi_alat(aneh)
        cek(f'E porsi_alat({aneh!r}) → semua alat MATI',
            p == {'jev': False, 'hakim': False, 'mutu_buku': False}, str(p))
        cek(f'E porsi_alat({aneh!r}) → apakah_buku False',
            J.apakah_buku(aneh) is False, str(J.apakah_buku(aneh)))

    # ── F. Fungsi pembantu tidak punya kebenaran sendiri ──────────────────
    for k in semua:
        p = J.porsi_alat(k)
        cek(f'F {k}: perlu_jev == tabel', J.perlu_jev(k) == p['jev'])
        cek(f'F {k}: perlu_hakim == tabel', J.perlu_hakim(k) == p['hakim'])
        cek(f'F {k}: perlu_mutu_buku == tabel', J.perlu_mutu_buku(k) == p['mutu_buku'])
    for k in J.JENIS_BUKU:
        cek(f'F {k}: apakah_buku True', J.apakah_buku(k) is True)
    for k in J.JENIS_AKADEMIK:
        cek(f'F {k}: apakah_buku False', J.apakah_buku(k) is False)

    # ── G. porsi_alat mengembalikan SALINAN (tidak bisa dirusak pemanggil) ─
    salinan = J.porsi_alat(J.JENIS_BUKU_UMUM)
    salinan['jev'] = True
    cek('G porsi_alat mengembalikan salinan (tabel tidak tercemar)',
        J.porsi_alat(J.JENIS_BUKU_UMUM)['jev'] is False,
        'tabel PORSI_ALAT ikut berubah — pemanggil bisa merusak kebenaran')

    print('\n'.join(PESAN))
    print(f'\n{"="*60}\nPORSI ALAT: {LULUS} LULUS / {GAGAL} GAGAL\n{"="*60}')
    return 0 if GAGAL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
