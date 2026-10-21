#!/usr/bin/env python3
"""UJI NYATA — 1 konversi naskah Asih (fid=81) lewat AI sungguhan.

Mengukur: waktu, token in/out, biaya, model, panjang artikel, .docx hasil.
JALAN DI DALAM container. Tanpa AI palsu — ini uji produksi.
"""
import json
import sys
import time
import urllib.error
import urllib.request

BASE = 'http://127.0.0.1:8000'
sys.path.insert(0, '/app')
from app import auth as A                                          # noqa: E402
from app.models import User, FileBerkas, SessionLocal              # noqa: E402

FID = 81
db = SessionLocal()

print('═' * 66)
print('UJI NYATA KONVERSI — naskah Asih')
print('═' * 66)

f = db.get(FileBerkas, FID)
if not f:
    print(f'❌ berkas fid={FID} tidak ada')
    sys.exit(1)
u = db.get(User, f.user_id)
print(f'naskah : {f.nama}  ({f.ukuran:,} byte)')
print(f'pemilik: id={u.id} {u.email}')

#  Kuota SEBELUM
from app import kuota as Q                                         # noqa: E402
j0 = Q.jatah_konversi(db, u)
print(f'jatah SEBELUM: {j0}')

tok = A.buat_token(u.id)
ck = f'{A.SESSION_COOKIE}={tok}'
print(f'token  : {tok[:24]}...')
print('─' * 66)

#  ── Panggil POST ──
import http.client

konek = http.client.HTTPConnection('127.0.0.1', 8000, timeout=900)
kepala = {'Cookie': ck, 'Content-Type': 'application/json'}
konek.request('POST', f'/artikel/{FID}/konversi', body='{}', headers=kepala)

t0 = time.time()
r = konek.getresponse()
teks = r.read().decode('utf-8', 'replace')
detik = time.time() - t0
konek.close()

print(f'HTTP {r.status}  ({detik:.1f} detik)')
print('─' * 66)

if r.status != 200:
    print('❌ GAGAL. Balasan:')
    print(teks[:2500])
    db.close()
    sys.exit(1)

d = json.loads(teks)
a = d.get('artikel') or {}

print('✅ BERHASIL')
print(f'  model       : {d.get("model")}')
print(f'  jenis       : {d.get("jenis")}  template: {d.get("template")}')
print(f'  berkas      : {d.get("nama_berkas")} (file_id={d.get("file_id")})')
print(f'  tersimpan   : {d.get("berkas_tersimpan")}')
print(f'  link unduh  : {d.get("link_unduh")}')
print()
print('  ISI ARTIKEL:')
print(f'    judul      : {(a.get("judul") or "")[:100]}')
print(f'    penulis    : {len(a.get("penulis") or [])} orang')
print(f'    abstrak ID : {len(a.get("abstrak_id") or "")} kar')
print(f'    abstrak EN : {len(a.get("abstract_en") or "")} kar')
print(f'    kata kunci : {(a.get("kata_kunci") or [])}')
print(f'    pendahuluan: {len(a.get("pendahuluan") or "")} kar')
print(f'    metode     : {len(a.get("metode") or "")} kar')
print(f'    hasil      : {len(a.get("hasil_pembahasan") or "")} kar')
print(f'    kesimpulan : {len(a.get("kesimpulan") or "")} kar')
print(f'    pustaka    : {len(a.get("daftar_pustaka") or [])} entri')
el = a.get('elemen') or {}
print(f'    elemen     : {len(el)} terisi -> {list(el.keys())}')
print()
print(f'  PERIKSA (mesin, gratis): {json.dumps(d.get("periksa") or {}, ensure_ascii=False)[:400]}')
print(f'  teks total : {len(d.get("teks") or "")} kar')
print()
j1 = Q.jatah_konversi(db, u)
print(f'jatah SESUDAH: {j1}')

#  Berkas hasil benar-benar ada?
if d.get('file_id'):
    fb2 = db.get(FileBerkas, d['file_id'])
    if fb2:
        from app.config import UPLOAD_DIR                          # noqa: E402
        p = UPLOAD_DIR / str(fb2.user_id) / fb2.nama_simpan
        print(f'  berkas di disk: {p.exists()}  {p.stat().st_size if p.exists() else 0:,} byte')
        print(f'  nama tampil   : {fb2.nama}')

#  Simpan hasil untuk pemeriksaan mata
try:
    with open('/tmp/hasil_konversi_nyata.json', 'w', encoding='utf-8') as fh:
        json.dump(d, fh, ensure_ascii=False, indent=1)
    print('  (balasan lengkap disimpan /tmp/hasil_konversi_nyata.json)')
except Exception as e:                                             # noqa: BLE001
    print(f'  (gagal simpan: {e})')

db.close()
print('═' * 66)
print(f'RINGKAS: HTTP {r.status} · {detik:.1f} detik · '
      f'{len(d.get("teks") or "")} kar teks artikel')
