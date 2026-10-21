"""BUKTI GERBANG BERGIGI — asersi O baru HARUS bisa GAGAL.

Menjalankan potongan asersi BARU terhadap 3 body berbeda:
  1. 402 + KUOTA_HABIS   → harus ✅ (perilaku benar)
  2. 409 + butuh_izin    → harus ❌ (DULU ✅ — inilah lubangnya)
  3. 200 + jawaban asli  → harus ❌ (app tidak menolak padahal saldo nol)

Kalau nomor 2 TIDAK gagal, perbaikan Wulan tidak menutup lubang apa pun.
Jalankan dari HOST:  python3 _sketsa/bukti_o_bergigi.py
"""
import json
import sys

GAGAL = []


def cek(nama, syarat, bukti=''):
    print(f'  {"LULUS" if syarat else "GAGAL"}  {nama}  {bukti}')
    if not syarat:
        GAGAL.append(nama)


def asersi_O_baru(s, b):
    """Salinan PERSIS logika O1/O2/O3 yang baru dipasang di _uji_publik_komentar.py."""
    try:
        jO = json.loads(b)
        djO = jO.get('detail') if isinstance(jO.get('detail'), dict) else jO
    except Exception:
        djO = {}
    kode_O = str(djO.get('kode') or '')
    pesan_O = str(djO.get('pesan') or b or '')
    return {
        'O1': (s == 402) and (kode_O == 'KUOTA_HABIS'),
        'O2': (not djO.get('kode_kerja')) and djO.get('ok') is not True
              and 'berhasil' not in pesan_O.lower(),
        'O3': any(k in pesan_O.lower()
                  for k in ('addon', 'tambah', 'paket', 'upgrade')),
    }


def asersi_O_LAMA(s, b):
    """Logika LAMA — sebagai pembanding (harus salah di kasus 2 & 3)."""
    return {'O1': s in (402, 403, 409),
            'O2': any(k in b.lower()
                      for k in ('addon', 'tambah', 'paket', 'upgrade'))}


print('═' * 74)
print('BUKTI GERBANG BERGIGI — asersi O (05Okt26)')
print('═' * 74)

KASUS = [
    ('1. 402 + KUOTA_HABIS (benar)', 402,
     '{"detail":{"kode":"KUOTA_HABIS","pesan":"Kuota habis. Beli AddOn."}}',
     {'O1': True, 'O2': True, 'O3': True}),
    ('2. 409 + butuh_izin (LUBANG LAMA)', 409,
     '{"detail":{"kode":"butuh_izin","pesan":"Naskah dipotong 3 bagian."}}',
     {'O1': False, 'O2': True, 'O3': False}),
    ('3. 200 + jawaban BERHASIL (app tidak tolak)', 200,
     '{"ok":true,"kode_kerja":"abc123","pesan":"Revisi berhasil dijalankan."}',
     {'O1': False, 'O2': False, 'O3': False}),
]

for judul, s, b, harap in KASUS:
    print(f'\n── {judul} ──')
    baru = asersi_O_baru(s, b)
    lama = asersi_O_LAMA(s, b)
    for k in ('O1', 'O2', 'O3'):
        if k not in harap:
            continue
        cek(f'{k} baru = {baru[k]} (harap {harap[k]})', baru[k] == harap[k])
    print(f'   pembanding LAMA O1={lama["O1"]} O2={lama["O2"]}'
          f'  ← {"terbukti TIDAK menangkap kerusakan" if lama["O1"] else ""}')

print()
print('═' * 74)
if GAGAL:
    print(f'❌ BUKTI GAGAL — {len(GAGAL)} — gerbang baru TIDAK bergigi:')
    for g in GAGAL:
        print(f'   · {g}')
    sys.exit(1)
print('✅ TERBUKTI: gerbang baru menangkap 2 kerusakan yang dulu lolos.')
sys.exit(0)
