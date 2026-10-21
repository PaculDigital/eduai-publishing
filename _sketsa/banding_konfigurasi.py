"""UJI BERPASANGAN: halaman baca (pembimbing) vs halaman mahasiswa.

Tujuan: cari BEDA keduanya. Kalau mahasiswa BISA tampil penuh dan baca
TIDAK, bedanya jadi akar. Kalau DUA-DUANYA skeleton, akarnya bukan di fitur
baru (melainkan di lingkungan/naskah).

Cara mengakses halaman mahasiswa: /edit/60 butuh login. Karena browser CDP
belum punya sesi login, jalan pintas yang SAH: bandingkan KONFIGURASI yang
dikirim kedua halaman (dari DB + mesin yang sama), bukan tampilan.
"""
import sys

sys.path.insert(0, '/app')
from app import onlyoffice as OO
from app.main import _token_berkas
from app.models import SessionLocal, FileBerkas

db = SessionLocal()
fb = db.query(FileBerkas).filter(FileBerkas.id == 60).one()
tk = _token_berkas(fb.id, fb.user_id)

print('=== KONFIGURASI HALAMAN MAHASISWA (/edit/60) ===')
cfg_mhs = OO.konfigurasi_editor(
    kunci=f'e{fb.id}v{int(fb.diubah.timestamp())}',
    nama=fb.nama,
    url_unduh=f'https://eduai.bikinaja.id/oo/unduh/{tk}',
    url_simpan=f'http://172.17.0.2:8000/oo/simpan/{tk}',
    user_id=str(fb.user_id), user_nama='Pemilik', extensi='.docx')
print('editorConfig.lang  :', cfg_mhs['editorConfig'].get('lang'))
print('editorConfig.mode  :', cfg_mhs['editorConfig'].get('mode'))
print('customization      :', list(cfg_mhs.get('editorConfig', {})
                                   .get('customization', {}).keys()))
print('permissions        :', cfg_mhs['document']['permissions'])
print('documentType       :', cfg_mhs['documentType'])
print('fileType           :', cfg_mhs['document']['fileType'])
print('url                :', cfg_mhs['document']['url'][:80])

print()
print('=== KONFIGURASI HALAMAN BACA (pembimbing) ===')
cfg_baca = OO.konfigurasi_editor(
    kunci=f'baca{fb.id}v{int(fb.diubah.timestamp())}',
    nama=fb.nama,
    url_unduh=f'https://eduai.bikinaja.id/oo/unduh/{tk}',
    url_simpan=f'http://172.17.0.2:8000/oo/simpan/{tk}',
    user_id='tinjau-1', user_nama='Pembimbing', extensi='.docx',
    mode_baca=True)
print('editorConfig.lang  :', cfg_baca['editorConfig'].get('lang'))
print('editorConfig.mode  :', cfg_baca['editorConfig'].get('mode'))
print('customization      :', list(cfg_baca.get('editorConfig', {})
                                   .get('customization', {}).keys()))
print('permissions        :', cfg_baca['document']['permissions'])
print('documentType       :', cfg_baca['documentType'])
print('fileType           :', cfg_baca['document']['fileType'])
print('url                :', cfg_baca['document']['url'][:80])

print()
print('=== BEDA KUNCI ===')
for bagian in ('editorConfig', 'document', 'documentType'):
    a, b = cfg_mhs.get(bagian, {}), cfg_baca.get(bagian, {})
    for k in set(a) | set(b):
        if a.get(k) != b.get(k):
            print(f'  {bagian}.{k}: mhs={a.get(k)!r}  baca={b.get(k)!r}')
db.close()
