"""Uji FASE 5 jalur PRODUKSI — helper _brief_dan_peta + penyisipan ke prompt.

Dijalankan DI DALAM container eduai-app (DB nyata + file nyata).
Tidak memanggil AI (hemat); yang diuji adalah penyambungannya.
"""
import sys, json
sys.path.insert(0, '/app')
from app.models import SessionLocal, FileBerkas, ProfilDokumen, SectionState, User
from app import ai as AI
from app import brief as B
from app import konsistensi as K

db = SessionLocal()
lulus = gagal = 0
def cek(n, k, info=''):
    global lulus, gagal
    if k: lulus += 1; print(f"  OK   {n}")
    else: gagal += 1; print(f"  GAGAL {n} {info}")

print("=== 1. _brief_dan_peta dengan FILE NYATA ===")
fb = db.query(FileBerkas).first()
print(f"file: id={fb.id} user={fb.user_id} nama={fb.nama}")
br, peta = AI._brief_dan_peta(db, fb.id, '')
print(f"brief kunci: {sorted(br.keys())[:8]}")
print(f"peta bagian: {len(peta)}")
for p in peta[:12]:
    print(f"   {p['section_id']:14s} {len(p['isi_teks']):7,d} kar  {p['section_title'][:40]}")
cek("peta berisi >0 bagian", len(peta) > 0, len(peta))
cek("kunci peta sesuai kontrak konsistensi",
    all(set(p) == {'section_id','section_title','isi_teks'} for p in peta))
cek("brief balik dict", isinstance(br, dict))

print("\n=== 2. check_consistency dari DATA NYATA ===")
hasil = K.check_consistency(br, peta)
print(f"counts={hasil['summary']['counts']} ok={hasil['ok']} temuan={len(hasil['issues'])}")
laporan = K.format_laporan(hasil)
print("--- laporan ---"); print(laporan[:700])
cek("laporan tidak kosong", len(laporan) > 20)
low = laporan.lower()
cek("tanpa kata terlarang", not any(t in low for t in ('kuota','rupiah','addon','token ai')))

print("\n=== 3. UJI TAHAN BANTING _brief_dan_peta ===")
cek("file_id 999999 (tidak ada)", isinstance(AI._brief_dan_peta(db, 999999, 'teks apa saja'), tuple))
cek("naskah None", isinstance(AI._brief_dan_peta(db, fb.id, None), tuple))
_p0 = AI._brief_dan_peta(db, fb.id, open('/dev/null').read())[1]
from pathlib import Path as _P
_t = AI._teks_dari_berkas(_P('/app/uploads/3/9c5d6f0e79c4cbf6.docx'), 'x.docx')
_br0, _peta_nyata = AI._brief_dan_peta(db, fb.id, _t)
print(f'peta dari teks NYATA: {len(_peta_nyata)} bagian')
for _p in _peta_nyata[:9]: print(f"   {_p['section_id']:14s} {len(_p['isi_teks']):7,d} kar")
cek('peta nyata >0 bagian', len(_peta_nyata) > 3, len(_peta_nyata))
cek("naskah kosong", isinstance(AI._brief_dan_peta(db, fb.id, ''), tuple))

print("\n=== 4. SIMULASI PROFIL + BRIEF NYATA (tulis lalu bersihkan) ===")
# pakai user & file nyata, tapi DB percobaan dikembalikan seperti semula
lama = db.query(ProfilDokumen).filter(ProfilDokumen.file_id == fb.id).one_or_none()
tersimpan_lama = None
if lama is not None:
    tersimpan_lama = json.dumps({c.name: str(getattr(lama, c.name)) for c in lama.__table__.columns}, default=str)
try:
    brief_uji = {
        "judul": "Pengaruh Kepemimpinan terhadap Kinerja Karyawan",
        "variabel": ["Kepemimpinan", "Motivasi", "Kinerja Karyawan"],
        "hipotesis": ["H1", "H2", "H3", "H4", "H5", "H6", "H7"],
        "alur": "kuantitatif_deduktif",
    }
    if lama is None:
        lama = ProfilDokumen(file_id=fb.id, user_id=fb.user_id, sumber='unggah')
        db.add(lama)
    lama.brief_json = B.simpan(brief_uji)
    db.commit()
    br2, peta2 = AI._brief_dan_peta(db, fb.id, _t)
    cek("brief terbaca dari DB", br2.get('judul') == brief_uji['judul'], br2.get('judul'))
    cek("variabel terbaca", len(br2.get('variabel') or []) == 3, br2.get('variabel'))
    hasil2 = K.check_consistency(br2, peta2)
    print(f"hasil dengan brief nyata: {hasil2['summary']['counts']}")
    for i in hasil2['issues'][:10]:
        print(f"   [{i['level']:7s}] {str(i.get('section')):12s} {i['message'][:100]}")
    catatan = K.catatan_untuk_ai(hasil2)
    print(f"catatan_untuk_ai: {len(catatan)} kar")
    if catatan:
        print("--- cuplikan catatan (yang disisipkan ke prompt) ---")
        print(catatan[:400])
    # Brief di atas SENGAJA cocok dengan naskah -> 0 temuan itu JAWABAN BENAR.
    # Jadi uji sesungguhnya: brief yang MEMANG menyimpang HARUS memunculkan temuan.
    brief_salah = {"judul": "Judul Yang Tidak Ada Di Naskah Sama Sekali",
                   "variabel": ["Variabel Karangan Yang Tidak Ada"],
                   "hipotesis": ["H99"]}
    lama.brief_json = B.simpan(brief_salah)
    db.commit()
    br3, _ = AI._brief_dan_peta(db, fb.id, _t)
    hasil3 = K.check_consistency(br3, _peta_nyata)
    catatan3 = K.catatan_untuk_ai(hasil3)
    print(f"brief MENYIMPANG -> {hasil3['summary']['counts']} · catatan {len(catatan3)} kar")
    for i in hasil3['issues'][:6]:
        print(f"   [{i['level']:7s}] {str(i.get('section')):14s} {i['message'][:95]}")
    cek("brief menyimpang MUNCULKAN temuan", len(hasil3['issues']) > 0, hasil3['issues'])
    cek("catatan untuk AI terbentuk saat ada temuan", len(catatan3) > 0)
    cek("catatan TIDAK memuat kata terlarang",
        not any(t in catatan.lower() for t in ('kuota','rupiah','rp ')))
finally:
    # BERSIHKAN: kembalikan DB ke kondisi semula
    if tersimpan_lama is None:
        db.query(ProfilDokumen).filter(ProfilDokumen.file_id == fb.id).delete()
    else:
        data_lama = json.loads(tersimpan_lama)
        p = db.query(ProfilDokumen).filter(ProfilDokumen.file_id == fb.id).one()
        p.brief_json = data_lama.get('brief_json', '{}')
    db.commit()
    print("\n(DB dikembalikan ke kondisi semula)")

print(f"\n{'='*50}\n{lulus} OK / {gagal} GAGAL\n{'='*50}")
sys.exit(1 if gagal else 0)
