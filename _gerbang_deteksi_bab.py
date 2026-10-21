#!/usr/bin/env python3
"""GERBANG DETEKSI BAB — uji mesin pada NASKAH NYATA (dibuat 03Okt26).

⚠️ KENAPA GERBANG INI ADA:
   Bug "BAB IPENDAHULUAN" (judul menempel) hidup di produksi BERTAHUN tanpa
   ketahuan karena uji selalu pakai naskah yang "kebetulan benar". Gerbang
   ini memakai naskah NYATA yang tersimpan di app/uploads, sehingga bug
   seperti itu TIDAK BISA lagi lolos diam-diam.

CARA JALAN (di dalam container):
   docker exec -e PYTHONPATH=/app eduai-app python3 /app/scripts/gerbang_deteksi_bab.py
   → EXIT 0 = LULUS · EXIT 1 = GAGAL (deploy DILARANG)

HARAPAN (diukur 03Okt26 — bukan tebakan):
   SKRIPSI S1 unmul (60)  → 5 bab (I–V) dengan JUDUL terbaca
   TESIS S2 unhas   (71)  → 3 bab (naskah baru sampai BAB III; daftar isi 7)
   DISERTASI S3     (72)  → 5 bab (I–V)
   SKRIPSI S1 unhas (70)  → 5 bab (II–VI)
   TESIS Goras      (9)   → 1 bab (PROPOSAL: isi baru BAB I + sistematika)

KALAU NASKAH DIHAPUS dari app/uploads, gerbang ini LEWAT (bukan GAGAL) —
supaya tidak menghalangi deploy karena prasarana, bukan kode.
"""
import html
import os
import re
import sys
import zipfile

sys.path.insert(0, '/app')

LEWAT = 77   # kode lewat (prasarana tak siap) — BUKAN gagal

HARAP = [
    #  (file_id, sebutan, jumlah_bab, wajib_ada_judul)
    (60, 'SKRIPSI S1 unmul 5MB', 5, True),
    (71, 'TESIS S2 unhas', 3, False),
    (72, 'DISERTASI S3 unhas', 5, False),
    (70, 'SKRIPSI S1 unhas', 5, True),
    (9,  'TESIS Goras (proposal)', 1, False),
]

#  Kasus teks: harus BENAR menolak kalimat biasa & menerima judul menempel
KASUS_TEKS = [
    ('BAB I PENDAHULUAN', True),
    ('BAB IPENDAHULUAN', True),
    ('BAB IIIMETODOLOGI PENELITIAN', True),
    ('BAB IVHASIL DAN PEMBAHASAN', True),
    ('BAB VKESIMPULAN DAN SARAN', True),
    ('Bab II Kajian Pustaka', True),
    ('bab ini menjelaskan metode penelitian', False),
    ('Tabel bab 3 menyajikan hasil', False),
    ('pada bab 5 akan dibahas nanti', False),
]


def teks_docx(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read('word/document.xml').decode('utf-8', 'replace')
    xml = re.sub(r'</w:p>', '\n', xml)
    xml = re.sub(r'<[^>]+>', '', xml)
    return html.unescape(xml)


def jalur(fid):
    try:
        from app.models import SessionLocal, FileBerkas
        db = SessionLocal()
        f = db.query(FileBerkas).filter(FileBerkas.id == fid).first()
        db.close()
        if f:
            p = f'/app/uploads/{f.user_id}/{f.nama_simpan}'
            if os.path.exists(p):
                return p
    except Exception:
        pass
    return None


def main() -> int:
    from app import versi, tulis_docx, cari_bagian

    lulus = gagal = 0
    dilewati = 0
    print('╔══════════════════════════════════════════════════════════════╗')
    print('║  GERBANG DETEKSI BAB — NASKAH NYATA                          ║')
    print('╚══════════════════════════════════════════════════════════════╝')

    #  ── A. Pola teks (murah, selalu jalan) ─────────────────────────────
    print('\n── A. POLA TEKS (judul menempel vs kalimat biasa) ──')
    for teks, harus in KASUS_TEKS:
        m = versi._POLA_BAB.match(teks)
        ketemu = bool(m)
        if ketemu == harus:
            lulus += 1
            print(f'  ✅ {teks!r:44s} → {"cocok" if ketemu else "ditolak"}')
        else:
            gagal += 1
            print(f'  ❌ {teks!r:44s} → {"cocok" if ketemu else "ditolak"} '
                  f'(HARUSNYA {"cocok" if harus else "ditolak"})')

    print('\n── B. tulis_docx._mirip_judul ──')
    for teks, harus in KASUS_TEKS:
        got = tulis_docx._mirip_judul(teks, '')
        if got == harus:
            lulus += 1
        else:
            gagal += 1
            print(f'  ❌ {teks!r:44s} → {got} (harusnya {harus})')
    print('  (semua benar)' if gagal == 0 else '')

    print('\n── C. cari_bagian (TIDAK boleh salah tangkap "Tabel bab 3") ──')
    pola_bab = [p for p in cari_bagian._POLA_KHAS if 'BAB' in p.pattern]
    if pola_bab:
        P = pola_bab[0]
        for teks, harus in [('Tabel bab 3 menyajikan', False),
                            ('bab ini menjelaskan', False),
                            ('BAB IPENDAHULUAN', True),
                            ('BAB III METODE', True)]:
            got = bool(P.search(teks))
            if got == harus:
                lulus += 1
            else:
                gagal += 1
                print(f'  ❌ {teks!r:44s} → {got} (harusnya {harus})')
        print('  (semua benar)')

    #  ── D. Naskah NYATA ───────────────────────────────────────────────
    print('\n── D. NASKAH NYATA ──')
    for fid, sebutan, harap, wajib_judul in HARAP:
        p = jalur(fid)
        if not p:
            dilewati += 1
            print(f'  ⏭️  {sebutan:28s} — berkas tak ada (LEWAT)')
            continue
        try:
            teks = teks_docx(p)
            bab = versi.deteksi_bab(teks)
        except Exception as e:
            gagal += 1
            print(f'  ❌ {sebutan:28s} — ERROR: {e}')
            continue
        jml = len(bab)
        if jml != harap:
            gagal += 1
            print(f'  ❌ {sebutan:28s} — {jml} bab (harap {harap})')
            continue
        if wajib_judul and not all(b.get('judul') for b in bab):
            gagal += 1
            print(f'  ❌ {sebutan:28s} — {jml} bab tapi JUDUL ada yang kosong')
            continue
        lulus += 1
        judul_ada = sum(1 for b in bab if b.get('judul'))
        print(f'  ✅ {sebutan:28s} — {jml} bab ({judul_ada} berjudul)')

    print(f'\n═══ {lulus} LULUS / {gagal} GAGAL / {dilewati} LEWAT ═══')
    if gagal:
        print('🚨 GERBANG GAGAL — DEPLOY DILARANG')
        return 1
    if dilewati and not lulus:
        print('⏭️  Hanya prasarana — LEWAT')
        return LEWAT
    print('✅ GERBANG LULUS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
