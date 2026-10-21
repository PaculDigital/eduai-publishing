#!/usr/bin/env python3
"""UJI CEK SALDO DI TAHAP 2 (perbaikan cacat 26Sep26) — 2 ARAH.

Arah 1 (SEHAT): saldo cukup → boleh_setuju True + pesan sisa.
Arah 2 (DIRUSAK): saldo kurang → boleh_setuju False + arahkan ADDON/UPGRADE.
"""
import os, sys, tempfile
os.environ['EDUAI_DATA_DIR'] = tempfile.mkdtemp(prefix='uji_t2_')
sys.path.insert(0, '/app')
from app import kerangka as K
L = GA = 0

def cek(nama, syarat, bukti=''):
    global L, GA
    if syarat:
        L += 1; print(f'  ✅ {nama}')
    else:
        GA += 1; print(f'  ❌ {nama}  {bukti}')

print('══ UJI CEK SALDO TAHAP 2 ══')
J = 'Pengaruh Kualitas Layanan terhadap Kepuasan Pelanggan'
D = dict(judul=J, jenis_dok='skripsi', jenis_penelitian='kuantitatif')

print('\n── A. SALDO CUKUP (harus boleh setuju) ──')
r = K.susun_rencana(bab='1', saldo=50, paket='penulis', **D)
st = r.get('status_saldo') or {}
cek('A1. boleh_setuju True', r.get('boleh_setuju') is True, str(r.get('boleh_setuju')))
cek('A2. cukup=True', st.get('cukup') is True, str(st))
cek('A3. sebut sisa setelah (50-15=35)', st.get('sisa_setelah') == 35, str(st))
cek('A4. harga tetap terkirim', r.get('harga_token') == 15, str(r.get('harga_token')))

print('\n── B. 🔴 SALDO KURANG — berbayar → ADDON ──')
r = K.susun_rencana(bab='4', saldo=12, paket='penulis', **D)
st = r.get('status_saldo') or {}
cek('B1. boleh_setuju False (tak bisa klik Setuju)', r.get('boleh_setuju') is False, str(r.get('boleh_setuju')))
cek('B2. kurang = 30-12 = 18', st.get('kurang') == 18, str(st.get('kurang')))
cek('B3. arahkan ADDON (penulis boleh beli AddOn)', st.get('arahkan') == 'ADDON', str(st.get('arahkan')))
cek('B4. pesan sebut AddOn + tidak hangus',
    'AddOn' in (st.get('pesan') or '') and 'hangus' in (st.get('pesan') or ''), st.get('pesan', '')[:60])

print('\n── C. 🔴 SALDO KURANG — GRATIS → UPGRADE ──')
r = K.susun_rencana(bab='2', saldo=3, paket='gratis', **D)
st = r.get('status_saldo') or {}
cek('C1. boleh_setuju False', r.get('boleh_setuju') is False, str(r.get('boleh_setuju')))
cek('C2. arahkan UPGRADE (gratis tak boleh AddOn)', st.get('arahkan') == 'UPGRADE', str(st.get('arahkan')))
cek('C3. pesan sebut Penulis', 'Penulis' in (st.get('pesan') or ''), st.get('pesan', '')[:60])

print('\n── D. TEPAT PAS (saldo == harga) ──')
r = K.susun_rencana(bab='1', saldo=15, paket='penulis', **D)
st = r.get('status_saldo') or {}
cek('D1. boleh_setuju True (15 >= 15)', r.get('boleh_setuju') is True, str(r.get('boleh_setuju')))
cek('D2. sisa_setelah = 0', st.get('sisa_setelah') == 0, str(st.get('sisa_setelah')))

print('\n── E. TANPA INFO SALDO (pemanggil lama) — jangan meledak ──')
r = K.susun_rencana(bab='1', **D)
cek('E1. tetap ok (kompatibel mundur)', r.get('ok') is True, str(r.get('ok')))
cek('E2. boleh_setuju True saat saldo tidak dikirim', r.get('boleh_setuju') is True, str(r.get('boleh_setuju')))
cek('E3. status_saldo None', r.get('status_saldo') is None, str(r.get('status_saldo')))

print('\n── F. BAB IV: DUA LAYANAN + cek saldo berlaku ──')
r = K.susun_rencana(bab='4', saldo=100, paket='penerbit', **D)
lay = r.get('harga_layanan') or []
cek('F1. ada 2 layanan (analisa & olah data)', len(lay) == 2, str([x['kode'] for x in lay]))
cek('F2. keduanya 30 token', all(x['token'] == 30 for x in lay), str(lay))
cek('F3. boleh_setuju True (100 >= 30)', r.get('boleh_setuju') is True, str(r.get('boleh_setuju')))

print(f'\n══ HASIL: {L} LULUS / {GA} GAGAL ══')
sys.exit(1 if GA else 0)
