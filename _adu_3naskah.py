"""ADU 3 NASKAH: MESIN KASAR + MESIN HALUS vs JEV (permintaan Bos, pilihan B).

Bos: "ukur dulu secara jujur: jalankan _cari_bab_skripsi + deteksi_subbab (2 mesin)
     vs Jev di 3 naskah → dapat angka pasti 'mesin kehilangan berapa %'."

Yang diukur per naskah:
  A. MESIN KASAR  : state.deteksi_bab_besar()      → jumlah bab + apakah JUDUL terisi
  B. MESIN KASAR-2: konversi._cari_bab_skripsi()   → cadangan bab (kalau Jev mati)
  C. MESIN HALUS  : state.deteksi_subbab()         → jumlah sub-bab
  D. JEV          : hasil peta3 (dari HASIL_PETA3_*.json kalau ada)

TIDAK memanggil Jev kalau json sudah ada (hemat). Cetak tabel perbandingan.
"""
import sys, json, os
sys.path.insert(0, '/app')
from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR
from app.models import FileBerkas
from app import state
from app import konversi

FIDS = [81, 78, 103]

db = SessionLocal()
for fid in FIDS:
    fb = db.get(FileBerkas, fid)
    if fb is None:
        print('fid=%d TIDAK ADA' % fid); continue
    p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
    try:
        mentah = _teks_dari_berkas(p, fb.nama or '') or ''
    except Exception as e:
        print('fid=%d GAGAL BACA: %s' % (fid, e)); continue
    if not mentah.strip():
        print('fid=%d KOSONG' % fid); continue

    print('=' * 78)
    print('fid=%d  %s  (%d kar)' % (fid, (fb.nama or '')[:50], len(mentah)))
    print('=' * 78)

    # A. MESIN KASAR
    try:
        bm = state.deteksi_bab_besar(mentah)
    except Exception as e:
        bm = []; print('  A. deteksi_bab_besar ERROR:', e)
    judul_isi = sum(1 for b in bm if str(b.get('judul', b.get('title', ''))).strip() not in ('', '?', 'None'))
    print('  A. MESIN KASAR  deteksi_bab_besar   : %2d bab · judul terisi %d/%d' % (len(bm), judul_isi, len(bm)))

    # B. MESIN KASAR-2 (cadangan Jev mati)
    try:
        baris = mentah.split('\n')
        kb = konversi._cari_bab_skripsi(baris)
    except Exception as e:
        kb = []; print('  B. _cari_bab_skripsi ERROR:', e)
    isi_kb = sum(1 for (i, n) in kb if str(n).strip())
    print('  B. CADANGAN BAB _cari_bab_skripsi   : %2d bab · nama terisi %d/%d' % (len(kb), isi_kb, len(kb)))
    for (i, n) in kb[:6]:
        print('        L%06d  %s' % (i, str(n)[:56]))

    # C. MESIN HALUS
    try:
        sm = state.deteksi_subbab(state.buang_daftar_isi(mentah))
    except Exception as e:
        sm = []; print('  C. deteksi_subbab ERROR:', e)
    print('  C. MESIN HALUS  deteksi_subbab      : %2d sub-bab' % len(sm))
    for s in sm[:6]:
        print('        %s' % str(s.get('judul', s.get('title', '?')))[:60])

    # D. JEV (json kalau ada)
    jf = '/app/HASIL_PETA3_%s.json' % ('ASIH' if fid == 81 else str(fid))
    if os.path.exists(jf):
        dj = json.load(open(jf))
        lab = dj['label']
        nb = sum(1 for v in lab.values() if v == 'bab')
        ns = sum(1 for v in lab.values() if v == 'subbab')
        np_ = sum(1 for v in lab.values() if v == 'paragraf')
        print('  D. JEV          peta3               : %2d bab · %3d sub-bab · %d paragraf' % (nb, ns, np_))
    else:
        print('  D. JEV          peta3               : (belum ada json — %s)' % jf)
    print()

db.close()
