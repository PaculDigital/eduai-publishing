"""UJI MESIN DETEKSI BAB — apa mesin benar menemukan BAB I..V?

Tujuan (pertanyaan Bos 03Okt26): Mode Belajar tumbuh mengikuti bab
(BAB I → mini insight · BAB III → ujian proposal · BAB V → ujian skripsi).
SEBELUM menjanjikan itu, WAJIB dibuktikan mesin `deteksi_bab` benar
menemukan bab-bab pada naskah NYATA (bukan dugaan).

Diuji pada 3 naskah nyata di produksi:
  id=71/76  TESIS-S2  (manajemen digital marketing)
  id=72/75  DISERTASI-S3 (kesehatan stunting)
  id=60     SKRIPSI-S1 (unmul fazrigading, 5 MB — naskah besar)

Cara: baca berkas dari dalam container (bind-mount tak menembus dari Hermes),
parse docx → versi.deteksi_bab() → laporkan bab yang ditemukan.
"""
import glob
import os
import sys
import zipfile

sys.path.insert(0, '/app')

from app import versi  # noqa: E402


def teks_docx(path: str) -> str:
    """Ambil teks dari .docx TANPA python-docx (baca XML mentah)."""
    with zipfile.ZipFile(path) as z:
        nama = [n for n in z.namelist() if n == 'word/document.xml']
        if not nama:
            return ''
        xml = z.read(nama[0]).decode('utf-8', 'replace')
    #  buang tag, jadikan paragraf
    import re
    xml = re.sub(r'</w:p>', '\n', xml)
    xml = re.sub(r'<[^>]+>', '', xml)
    import html
    return html.unescape(xml)


def cari_berkas(fid: int) -> str | None:
    """Cari berkas fisik: /app/uploads/<user_id>/<nama_simpan> (pola nyata)."""
    try:
        from app.models import SessionLocal, FileBerkas
        db = SessionLocal()
        f = db.query(FileBerkas).filter(FileBerkas.id == fid).first()
        db.close()
        if f:
            p = f'/app/uploads/{f.user_id}/{f.nama_simpan}'
            if os.path.exists(p):
                return p
            #  cadangan: cari bila nama_simpan berbeda
            h = glob.glob(f'/app/uploads/{f.user_id}/*')
            for x in h:
                if x.endswith(str(f.nama_simpan)):
                    return x
    except Exception as e:
        print('   (db err:', e, ')')
    return None


def uji(fid: int, sebutan: str):
    print(f'\n═══ {sebutan} (file_id={fid}) ═══')
    jalur = cari_berkas(fid)
    if not jalur:
        print('   ⚠️ berkas fisik tidak ketemu — dilewati')
        return None
    print(f'   berkas: {jalur} ({os.path.getsize(jalur)} byte)')
    try:
        teks = teks_docx(jalur)
    except Exception as e:
        print('   ❌ gagal baca:', e)
        return None
    print(f'   teks terbaca: {len(teks)} karakter')
    if len(teks) < 100:
        print('   ⚠️ teks terlalu pendek — dilewati')
        return None

    bab = versi.deteksi_bab(teks)
    print(f'   → JUMLAH BAB TERDETEKSI: {len(bab)}')
    for b in bab:
        isi = len(str(b.get('isi') or ''))
        print(f'      · {b.get("label"):12s} | nomor={b.get("nomor")} '
              f'| judul={str(b.get("judul"))[:42]:42s} | {isi} kar')
    nomor = {str(b.get('nomor')) for b in bab}
    print(f'   → nomor bab: {sorted(nomor)}')
    return {'fid': fid, 'sebutan': sebutan, 'jumlah': len(bab),
            'nomor': sorted(nomor)}


hasil = []
for fid, sebutan in ((71, 'TESIS S2'), (72, 'DISERTASI S3'),
                     (60, 'SKRIPSI S1 (5 MB)')):
    r = uji(fid, sebutan)
    if r:
        hasil.append(r)

print('\n\n════════ RINGKASAN ════════')
for h in hasil:
    print(f'  {h["sebutan"]:18s}: {h["jumlah"]} bab → {h["nomor"]}')
