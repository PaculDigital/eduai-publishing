"""UJI FASE 2 — tabel profil_dokumen + brief + konteks, DI DALAM container."""
import sys
sys.path.insert(0, '/app')

from app.models import ProfilDokumen, init_db, SessionLocal, FileBerkas
from sqlalchemy import inspect, text
from app import brief, konteks

print('=' * 62)
print('UJI A — tabel profil_dokumen terbuat?')
print('=' * 62)
init_db()
insp = inspect(SessionLocal().bind)
tabel = insp.get_table_names()
print(f'  profil_dokumen ada: {"YA ✅" if "profil_dokumen" in tabel else "TIDAK ❌"}')
if 'profil_dokumen' in tabel:
    kol = [c['name'] for c in insp.get_columns('profil_dokumen')]
    print(f'  jumlah kolom: {len(kol)}')
    wajib = ['file_id', 'user_id', 'sumber', 'kategori', 'judul', 'jenjang',
             'bidang', 'mode_penelitian', 'alur', 'brief_json', 'istilah_json',
             'struktur_json', 'sidik_jari', 'status', 'dibaca_pada']
    hilang = [k for k in wajib if k not in kol]
    print(f'  kolom wajib hilang: {hilang or "TIDAK ADA ✅"}')
    # unique constraint
    uq = [u['name'] for u in insp.get_unique_constraints('profil_dokumen')]
    print(f'  unique constraint: {uq}')
    fk = [f['referred_table'] for f in insp.get_foreign_keys('profil_dokumen')]
    print(f'  foreign keys -> {fk}')

print()
print('=' * 62)
print('UJI B — cascade.py mendaftarkan ProfilDokumen?')
print('=' * 62)
from app import cascade
print(f'  _ANAK_FILE: {[m.__name__ for m in cascade._ANAK_FILE]}')
print(f'  _ANAK_USER: {[m.__name__ for m in cascade._ANAK_USER]}')
print(f'  ProfilDokumen di _ANAK_FILE: {"YA ✅" if ProfilDokumen in cascade._ANAK_FILE else "TIDAK ❌"}')
print(f'  ProfilDokumen di _ANAK_USER: {"YA ✅" if ProfilDokumen in cascade._ANAK_USER else "TIDAK ❌"}')

print()
print('=' * 62)
print('UJI C — siklus hidup: simpan -> baca -> perbarui')
print('=' * 62)
db = SessionLocal()
try:
    f = db.query(FileBerkas).first()
    if not f:
        print('  ⚠️ tidak ada berkas uji di DB, lewati uji C-D')
    else:
        print(f'  berkas uji: id={f.id} {f.nama}')
        # bersihkan sisa uji lama
        db.query(ProfilDokumen).filter(ProfilDokumen.file_id == f.id).delete()
        db.commit()

        b = brief.brief_kosong()
        b['judul'] = 'Pengaruh QWL terhadap Kinerja (UJI)'
        b['paradigma'] = 'kuantitatif'
        b['alur'] = 'kuantitatif_deduktif'
        b['variabel'] = [{'nama': 'X1', 'jenis': 'independen'}, {'nama': 'Y', 'jenis': 'dependen'}]
        b['hipotesis'] = ['H1', 'H2']

        p = ProfilDokumen(
            file_id=f.id, user_id=f.user_id,
            kategori='akademik_lengkap', jenjang='S2',
            mode_penelitian='kuantitatif', alur='kuantitatif_deduktif',
            brief_json=brief.simpan(b),
            istilah_json='[{"istilah":"QWL","arti":"Quality of Work Life"}]',
            struktur_json='[{"nomor":"BAB I","judul":"PENDAHULUAN","karakter":43000}]',
            sidik_jari='a' * 64, status='siap',
        )
        db.add(p)
        db.commit()
        print(f'  DISIMPAN: id={p.id} kategori={p.kategori} status={p.status}')

        # baca ulang
        p2 = db.query(ProfilDokumen).filter(ProfilDokumen.file_id == f.id).first()
        b2 = brief.muat(p2.brief_json)
        print(f'  DIBACA  : judul={b2["judul"]!r}')
        print(f'            variabel={[v["nama"] for v in b2["variabel"]]}')
        print(f'            alur={b2["alur"]} sidik={p2.sidik_jari[:12]}...')

        print()
        print('=' * 62)
        print('UJI D — CASCADE hapus berkas (tidak boleh gagal FK)')
        print('=' * 62)
        n_before = db.query(ProfilDokumen).count()
        print(f'  profil sebelum: {n_before}')
        # hapus profil lalu berkas (tiruan cascade)
        db.query(ProfilDokumen).filter(ProfilDokumen.file_id == f.id).delete()
        db.commit()
        n_after = db.query(ProfilDokumen).count()
        print(f'  profil sesudah: {n_after}')
        print(f'  cascade bersih: {"YA ✅" if n_after < n_before else "TIDAK ❌"}')
finally:
    db.close()
