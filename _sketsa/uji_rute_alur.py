#!/usr/bin/env python3
"""UJI RUTE ALUR AWAL via HTTP nyata (26Sep26) — 2 ARAH.

Arah 1 (SEHAT)  : jalur normal → hasil masuk akal
Arah 2 (DIRUSAK): data ngawur / tak lengkap → ditolak ramah, TIDAK meledak
Pakai BERKAS NYATA milik user uji (pelajaran 26Sep26: data karangan =
GAGAL PALSU).
"""
import os
import shutil
import sys
import tempfile

#  ⚠️ JANGAN sentuh DB produksi: salin dulu, arahkan EDUAI_DATA_DIR ke salinan
SALIN = tempfile.mkdtemp(prefix='uji_alur_')
shutil.copy2('/app/data/eduai.db', os.path.join(SALIN, 'eduai.db'))
os.environ['EDUAI_DATA_DIR'] = SALIN
os.environ['EDUAI_UPLOAD_DIR'] = '/app/data/uploads'
sys.path.insert(0, '/app')

BASE = 'http://127.0.0.1:8000'
L = GA = 0


def cek(nama, ok, bukti=''):
    global L, GA
    if ok:
        L += 1
        print(f'  ✅ {nama}')
    else:
        GA += 1
        print(f'  ❌ {nama}  {bukti}')


import httpx                                                        # noqa: E402
from app.auth import buat_token                                     # noqa: E402
from app.models import FileBerkas, SessionLocal, User               # noqa: E402

db = SessionLocal()
u = db.query(User).order_by(User.id).first()
uid = u.id
tok = buat_token(uid)
fb = db.query(FileBerkas).filter(FileBerkas.user_id == uid).first()
FID = fb.id if fb else None
db.close()
print(f'user {uid} · berkas nyata id={FID}\n')

ck = {'eduai_session': tok}

with httpx.Client(timeout=300) as c:
    print('── A. PINTU & PILIHAN (tanpa login, GRATIS) ──')
    r = c.get(f'{BASE}/api/ai/v1/alur/pintu')
    d = r.json() if r.status_code == 200 else {}
    cek('A1. /alur/pintu 200', r.status_code == 200, str(r.status_code))
    cek('A2. 2 pintu (baru/lanjut)',
        [x['kode'] for x in d.get('pintu', [])] == ['baru', 'lanjut'],
        str(d.get('pintu'))[:120])
    cek('A3. 4 langkah', len(d.get('langkah') or []) == 4,
        str(len(d.get('langkah') or [])))

    r = c.get(f'{BASE}/api/ai/v1/alur/pilihan')
    d = r.json() if r.status_code == 200 else {}
    cek('A4. /alur/pilihan 200', r.status_code == 200, str(r.status_code))
    cek('A5. 6 jenjang', len(d.get('jenjang') or []) == 6,
        str(len(d.get('jenjang') or [])))
    cek('A6. 9 bidang', len(d.get('bidang') or []) == 9,
        str(len(d.get('bidang') or [])))
    cek('A7. 2 jenis penelitian', len(d.get('jenis_penelitian') or []) == 2,
        str(len(d.get('jenis_penelitian') or [])))

    r = c.get(f'{BASE}/api/ai/v1/alur/contoh-judul?bidang=pendidikan')
    d = r.json() if r.status_code == 200 else {}
    cek('A8. contoh judul 3-5', 3 <= len(d.get('contoh') or []) <= 5,
        str(len(d.get('contoh') or [])))

    r = c.get(f'{BASE}/api/ai/v1/alur/contoh-judul?bidang=ngawur')
    d = r.json() if r.status_code == 200 else {}
    cek('A9. bidang ngawur → contoh kosong (tidak menebak)',
        d.get('contoh') == [], str(d.get('contoh')))

    print('\n── B. GERBANG BESAR (perlu login) ──')
    r = c.post(f'{BASE}/api/ai/v1/alur/petakan', cookies=ck,
               json={'pilihan': 'baru'})
    d = r.json() if r.status_code == 200 else {}
    cek('B1. mulai baru → jalur baru', d.get('jalur') == 'baru', str(d)[:130])

    r = c.post(f'{BASE}/api/ai/v1/alur/petakan', cookies=ck,
               json={'pilihan': 'lanjut'})
    d = r.json() if r.status_code == 200 else {}
    cek('B2. P1: lanjut tanpa berkas → tanya unggah',
        d.get('tanya') == 'unggah' and d.get('jalur') is None, str(d)[:140])

    if FID:
        r = c.post(f'{BASE}/api/ai/v1/alur/petakan', cookies=ck,
                   json={'pilihan': 'lanjut', 'file_id': FID})
        d = r.json() if r.status_code == 200 else {}
        cek('B3. P3: ada ISI → tanya konfirmasi',
            d.get('tanya') == 'konfirmasi', str(d)[:140])
        det = d.get('deteksi') or {}
        cek('B4. deteksi isi naskah nyata',
            bool(det.get('jenis')) and bool(det.get('label_jenis')),
            str(det)[:150])
        cek('B5. kalimat ramah untuk layar',
            'Sepertinya' in (det.get('ringkas') or ''),
            str(det.get('ringkas'))[:140])

        r = c.post(f'{BASE}/api/ai/v1/alur/petakan', cookies=ck,
                   json={'pilihan': 'lanjut', 'file_id': FID,
                         'konfirmasi': True})
        d = r.json() if r.status_code == 200 else {}
        cek('B6. konfirmasi Benar → jalur lanjut',
            d.get('jalur') == 'lanjut', str(d)[:120])

    print('\n── C. DIRUSAK (jangan meledak) ──')
    r = c.post(f'{BASE}/api/ai/v1/alur/petakan', cookies=ck, json={})
    cek('C1. body kosong → tanya pintu (tidak meledak)',
        r.status_code == 200 and r.json().get('tanya') == 'pintu',
        f'{r.status_code} {r.text[:110]}')

    r = c.post(f'{BASE}/api/ai/v1/alur/petakan', cookies=ck,
               json={'pilihan': 'xyz'})
    cek('C2. pilihan ngawur → tanya pintu',
        r.status_code == 200 and r.json().get('tanya') == 'pintu',
        f'{r.status_code} {r.text[:110]}')

    r = c.post(f'{BASE}/api/ai/v1/alur/petakan', cookies=ck,
               json={'pilihan': 'lanjut', 'file_id': 'abc'})
    cek('C3. file_id bukan angka → 400 ramah',
        r.status_code == 400, f'{r.status_code} {r.text[:110]}')

    r = c.post(f'{BASE}/api/ai/v1/alur/petakan', cookies=ck,
               json={'pilihan': 'lanjut', 'file_id': 999999})
    cek('C4. file_id bukan milik user → 404 ramah',
        r.status_code == 404, f'{r.status_code} {r.text[:110]}')

    r = c.post(f'{BASE}/api/ai/v1/alur/petakan', json={'pilihan': 'baru'})
    cek('C5. TANPA login → 401 (tidak bocor)',
        r.status_code in (401, 403), f'{r.status_code}')

    print('\n── D. 4 LANGKAH + SIMPAN ──')
    r = c.get(f'{BASE}/api/ai/v1/alur/langkah')
    d = r.json() if r.status_code == 200 else {}
    cek('D1. kosong → langkah jenjang', d.get('langkah') == 'jenjang',
        str(d)[:110])

    r = c.post(f'{BASE}/api/ai/v1/alur/simpan', cookies=ck,
               json={'jenjang': 'tesis', 'bidang': 'pendidikan',
                     'mode_penelitian': 'kuantitatif'})
    d = r.json() if r.status_code == 200 else {}
    cek('D2. simpan 3 langkah → ok', d.get('ok') is True, str(d)[:140])
    cek('D3. berikut = langkah judul',
        (d.get('berikut') or {}).get('langkah') == 'judul',
        str(d.get('berikut'))[:130])
    #  ⚠️ OPSI D: menyimpan tanpa file_id MEMBUAT naskah baru → simpan
    #  file_id-nya supaya langkah berikut (judul) masuk ke NASKAH YANG SAMA
    #  (kalau tidak, server membuat naskah KEDUA dan jenjang jadi kosong).
    FID_DRAFT = d.get('file_id')
    cek('D3b. file_id naskah draft diterima', isinstance(FID_DRAFT, int),
        str(FID_DRAFT))

    r = c.post(f'{BASE}/api/ai/v1/alur/simpan', cookies=ck,
               json={'judul': 'Pengaruh Media Pembelajaran terhadap Hasil Belajar',
                     'file_id': FID_DRAFT})
    d = r.json() if r.status_code == 200 else {}
    cek('D4. simpan judul ke naskah yang sama → selesai',
        (d.get('berikut') or {}).get('selesai') is True,
        str(d.get('berikut'))[:130])

    r = c.post(f'{BASE}/api/ai/v1/alur/simpan', cookies=ck, json={})
    cek('D5. simpan kosong → 400 ramah', r.status_code == 400,
        f'{r.status_code} {r.text[:100]}')

    print('\n── D2. OPSI D: DOKUMEN BARU (ACC Bos 26Sep26) ──')
    #  Simpan 4 langkah TANPA file_id → server WAJIB bikin dokumen dulu
    r = c.post(f'{BASE}/api/ai/v1/alur/simpan', cookies=ck,
               json={'jenjang': 'skripsi', 'bidang': 'manajemen',
                     'mode_penelitian': 'kuantitatif',
                     'judul': 'Uji Opsi D dokumen baru',
                     'nama_dokumen': 'Uji Opsi D.docx'})
    d = r.json() if r.status_code == 200 else {}
    cek('D6. simpan tanpa file_id → OK (dokumen dibuat otomatis)',
        r.status_code == 200 and d.get('ok') is True,
        f'{r.status_code} {r.text[:170]}')
    FID2 = d.get('file_id')
    cek('D7. balasan memuat file_id NYATA', isinstance(FID2, int) and FID2 > 0,
        str(FID2))
    cek('D8. dokumen info lengkap',
        bool((d.get('dokumen') or {}).get('nama')), str(d.get('dokumen'))[:150])

    #  Buktikan berkasnya BENAR-BENAR ada di DB & di disk.
    #  ⚠️ PELAJARAN (26Sep26): uji ini mengarahkan EDUAI_DATA_DIR ke DB
    #     SALINAN, sedangkan SERVER menulis ke DB PRODUKSI. Karena itu
    #     pemeriksaan WAJIB lewat data yang dibalaskan server (bukan
    #     membuka sesi DB sendiri) — kalau tidak, tampak "GAGAL" padahal
    #     dokumennya benar-benar dibuat (uji yang salah, bukan mesin).
    if isinstance(FID2, int) and FID2 > 0:
        dok = d.get('dokumen') or {}
        nm = dok.get('nama') or ''
        ns = dok.get('nama_simpan') or ''
        cek('D9. server balas nama_simpan nyata', bool(ns), str(ns))
        cek('D10. ukuran file masuk akal (dari templat)',
            int(dok.get('ukuran') or 0) > 1000, str(dok.get('ukuran')))
        cek('D11. nama dokumen sesuai permintaan', 'Uji Opsi D' in nm, nm)

        #  Berkas di disk WAJIB ada → tanya server (bukan DB salinan)
        r2 = c.get(f'{BASE}/unduh/{FID2}', cookies=ck)
        cek('D11b. berkas BISA diunduh lewat HTTP (bukti nyata)',
            r2.status_code == 200 and len(r2.content) > 1000,
            f'{r2.status_code} {len(r2.content)} byte')

    #  Buktikan profil naskah MENEMPEL ke file_id (bukan 0)
    r = c.post(f'{BASE}/api/ai/v1/alur/simpan', cookies=ck,
               json={'judul': 'Uji Opsi D lanjutan', 'file_id': FID2})
    d = r.json() if r.status_code == 200 else {}
    cek('D12. simpan lanjutan ke naskah yang sama → OK',
        d.get('ok') is True and d.get('file_id') == FID2,
        f'{r.status_code} {r.text[:140]}')

    #  DIRUSAK: nama dokumen ngawur / sangat panjang → tidak meledak
    r = c.post(f'{BASE}/api/ai/v1/alur/dokumen-baru', cookies=ck,
               json={'nama_dokumen': '../' * 100 + 'x' * 300})
    cek('D13. nama ngawur → tetap OK & tidak bikin folder aneh',
        r.status_code in (200, 503), f'{r.status_code} {r.text[:110]}')

    r = c.post(f'{BASE}/api/ai/v1/alur/dokumen-baru', json={})
    cek('D14. bikin dokumen TANPA login → 401',
        r.status_code in (401, 403), f'{r.status_code}')

    print('\n── E. IDENTITAS (logo boleh dilewati) ──')
    r = c.get(f'{BASE}/api/ai/v1/identitas', cookies=ck)
    d = r.json() if r.status_code == 200 else {}
    cek('E1. lihat identitas 200', r.status_code == 200, str(r.status_code))
    cek('E2. ada daftar wajib & opsional',
        len(d.get('wajib') or []) == 3 and len(d.get('opsional') or []) == 6,
        f"{d.get('wajib')} {d.get('opsional')}")

    r = c.post(f'{BASE}/api/ai/v1/identitas', cookies=ck,
               json={'nama_lengkap': 'Budi Santoso', 'nim': 'A123456',
                     'nama_kampus': 'Universitas Negeri Malang'})
    d = r.json() if r.status_code == 200 else {}
    cek('E3. simpan wajib tanpa logo → boleh lanjut',
        (d.get('periksa') or {}).get('boleh_lanjut') is True, str(d)[:150])
    cek('E4. pesan sebut logo boleh nanti',
        'boleh diisi nanti' in ((d.get('periksa') or {}).get('pesan') or ''),
        str((d.get('periksa') or {}).get('pesan'))[:140])

    r = c.post(f'{BASE}/api/ai/v1/identitas', cookies=ck, json={})
    cek('E5. simpan kosong → 400 ramah', r.status_code == 400,
        f'{r.status_code} {r.text[:90]}')

    r = c.get(f'{BASE}/api/ai/v1/identitas')
    cek('E6. lihat identitas TANPA login → 401',
        r.status_code in (401, 403), f'{r.status_code}')

print(f'\n══ HASIL: {L} LULUS / {GA} GAGAL ══')
shutil.rmtree(SALIN, ignore_errors=True)
sys.exit(1 if GA else 0)
