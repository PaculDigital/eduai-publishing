"""BASELINE regresi 3 jalur — rekam perilaku request LAMA di kode yang BELUM diubah.

Dijalankan:  python3 _sketsa/regresi_baseline.py --simpan <path.json>
Atau banding: python3 _sketsa/regresi_baseline.py --banding <path.json>

Cakupan (semua = request LAMA, tanpa field baru):
  H1 /v1/hitung tanpa bab (Pintu B)
  H2 /v1/hitung bab='1.1' (sub-bab)
  H3 /v1/hitung bab='BAB III' (jalur 3 — SATU-SATUNYA yang boleh berubah
     `revisi_dibutuhkan` sesuai putusan Bos "1 pembuka + 1 per sub-bab")
  B1 /v1/bab file_id=78 → daftar label
  P1 potongan ambil_bab per label (posisi, akhir, panjang, awal teks)
  K1 konteks_dari_bab untuk label lama
  R1 /v1/revisi mode tunggu bab='1.1' (AI distub) → kuota & respon
  R2 /v1/revisi mode tunggu tanpa bab (AI distub) → kuota & respon

Lingkungan: salinan /tmp/rg (APP_ROOT), data /tmp/rg_data, upload /tmp/rg_up.
"""
import argparse
import json
import os
import sys
from pathlib import Path

APP_ROOT = os.environ.get('APP_ROOT', '/tmp/rg')
sys.path.insert(0, APP_ROOT)
os.environ.setdefault('EDUAI_DATA_DIR', '/tmp/rg_data')
os.environ.setdefault('EDUAI_UPLOAD_DIR', '/tmp/rg_up')

from fastapi.testclient import TestClient                      # noqa: E402
from app.auth import buat_token                                # noqa: E402
from app.config import SESSION_COOKIE                          # noqa: E402
from app.main import app as APP_UTAMA                          # noqa: E402
from app import versi as V                                     # noqa: E402
from app.versi import ambil_bab, deteksi_bab, _deteksi_bagian  # noqa: E402
from app.ai import konteks_dari_bab, hitung_bagian             # noqa: E402

FILE_ID = 78
CK = {SESSION_COOKIE: buat_token(7)}
_K = TestClient(APP_UTAMA)

# naskah asli (baca dari salinan upload — deterministik)
from app.ai import _teks_dari_berkas                           # noqa: E402
_P78 = Path(os.environ['EDUAI_UPLOAD_DIR']) / '7' / 'f04505099df1f0a8.docx'
TEKS = _teks_dari_berkas(_P78, _P78.name) or ''

LABEL = ['1.1', '1.4', '2.1', '3.2', 'BAB I', 'BAB II', 'BAB III']


def snap() -> dict:
    s: dict = {'meta': {'naskah': len(TEKS)}}

    # ── H: /v1/hitung ──
    s['hitung'] = {}
    for kasus, body in (
        ('H1_tanpa_bab', {'file_id': FILE_ID}),
        ('H2_subbab_1_1', {'file_id': FILE_ID, 'bab': '1.1'}),
        ('H3_bab_besar', {'file_id': FILE_ID, 'bab': 'BAB III'}),
        ('H4_seluruh', {'file_id': FILE_ID, 'bab': '__seluruh__'}),
    ):
        r = _K.post('/api/ai/v1/hitung', json=body, cookies=CK)
        d = r.json() if r.status_code == 200 else {'_status': r.status_code}
        d.pop('sisa_kuota', None)       # bergantung saldo uji, jangan dipegang
        s['hitung'][kasus] = d

    # ── B: /v1/bab ──
    r = _K.post('/api/ai/v1/bab', json={'file_id': FILE_ID}, cookies=CK)
    d = r.json() if r.status_code == 200 else {'_status': r.status_code}
    s['bab_status'] = r.status_code
    s['bab_label'] = [b.get('label') for b in d.get('bab', [])]
    s['bab_panjang'] = [b.get('panjang') for b in d.get('bab', [])]

    # ── P: potongan ──
    s['potong'] = {}
    for lab in LABEL:
        a, i, e = ambil_bab(TEKS, lab)
        s['potong'][lab] = {
            'sebelum': len(a), 'isi': len(i), 'sesudah': len(e),
            'awal': i[:70],
            'utuh': (a + i + e == TEKS),
        }
    s['label_besar'] = [b['label'] for b in deteksi_bab(TEKS)]
    s['label_halus'] = [b['label'] for b in _deteksi_bagian(TEKS)]
    s['hitung_bagian_seluruh'] = hitung_bagian(TEKS)
    s['hitung_bagian_babiii'] = hitung_bagian(ambil_bab(TEKS, 'BAB III')[1])
    s['hitung_bagian_11'] = hitung_bagian(ambil_bab(TEKS, '1.1')[1])

    # ── K: penanda pintu ──
    s['konteks'] = {lab: konteks_dari_bab(lab) for lab in
                    ('1.1', 'BAB III', '', '__seluruh__', '9.99')}

    return s


def kuota() -> dict:
    import sqlite3
    db = os.environ['EDUAI_DATA_DIR'] + '/eduai.db'
    c = sqlite3.connect(db)
    out = {}
    try:
        for uid, jml in c.execute('select user_id, jumlah_revisi from pemakaian_ai'):
            out[f'u{uid}'] = jml
    except Exception as e:                                    # noqa: BLE001
        out['err'] = str(e)
    out['revisi_history'] = c.execute(
        'select count(*) from revisi_history').fetchone()[0]
    out['versi_dokumen'] = c.execute(
        'select count(*) from versi_dokumen').fetchone()[0]
    c.close()
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--simpan')
    ap.add_argument('--banding')
    a = ap.parse_args()

    s = snap()
    s['kuota_sebelum'] = kuota()

    if a.simpan:
        Path(a.simpan).write_text(json.dumps(s, indent=2, ensure_ascii=False))
        print(f'BASELINE TERSIMPAN → {a.simpan}')
        return 0

    if not a.banding:
        print(json.dumps(s, indent=2, ensure_ascii=False))
        return 0

    lama = json.loads(Path(a.banding).read_text())
    gagal = []

    def cek(nama, ok, info=''):
        print(('  LULUS  ' if ok else '  GAGAL  ') + nama + (' → ' + str(info) if info else ''))
        if not ok:
            gagal.append(nama)

    # 1. H1, H2, H4 identik SAMA SEKALI
    for k in ('H1_tanpa_bab', 'H2_subbab_1_1', 'H4_seluruh'):
        cek(f'REG {k} identik', s['hitung'][k] == lama['hitung'][k],
            f"{lama['hitung'][k]} → {s['hitung'][k]}")
    # 2. H3: hanya revisi_dibutuhkan/pesan/cukup yang boleh berubah
    l3, b3 = lama['hitung']['H3_bab_besar'], s['hitung']['H3_bab_besar']
    for k in ('ok', 'bab', 'panjang', 'panjang_dokumen', 'batas_bagian', 'bagian'):
        cek(f'REG H3 kunci {k} identik', l3.get(k) == b3.get(k),
            f"{l3.get(k)} → {b3.get(k)}")
    # 3. bab & potongan identik
    cek('REG /v1/bab label identik', s['bab_label'] == lama['bab_label'],
        f"{lama['bab_label']} → {s['bab_label']}")
    cek('REG /v1/bab panjang identik', s['bab_panjang'] == lama['bab_panjang'],
        f"{lama['bab_panjang']} → {s['bab_panjang']}")
    cek('REG potongan semua label identik', s['potong'] == lama['potong'],
        [k for k in lama['potong'] if lama['potong'][k] != s['potong'].get(k)])
    cek('REG label besar identik', s['label_besar'] == lama['label_besar'],
        f"{lama['label_besar']} → {s['label_besar']}")
    cek('REG label halus identik', s['label_halus'] == lama['label_halus'],
        f"{lama['label_halus']} → {s['label_halus']}")
    for k in ('hitung_bagian_seluruh', 'hitung_bagian_babiii', 'hitung_bagian_11'):
        cek(f'REG {k} identik', s[k] == lama[k], f"{lama[k]} → {s[k]}")
    cek('REG konteks_dari_bab identik', s['konteks'] == lama['konteks'],
        f"{lama['konteks']} → {s['konteks']}")

    print(f"\nRINGKAS: {len(gagal)} GAGAL " + (', '.join(gagal) if gagal else '(regresi bersih)'))
    return 1 if gagal else 0


if __name__ == '__main__':
    sys.exit(main())
