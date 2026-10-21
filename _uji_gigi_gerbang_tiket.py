"""UJI BERGIGI gerbang tiket — rusak di MEMORI (tanpa salin modul).

Cara: panggil fungsi cek dalam `_gerbang_tiket_lolos` TAPI dengan
`konversi.token_elemen` DIJADIKAN RUSAK sementara. Gerbang harus GAGAL.

⚠️ Tidak menyentuh berkas produksi sama sekali (pelajaran 16 Okt).
"""
import sys
sys.path.insert(0, '/app')

from app import konversi as K

#  Simpan yang asli
asli = K.token_elemen


def rusak(kunci):
    """Versi rusak: semua elemen jadi 9 token (harga tidak sah)."""
    return 9


#  ── Pasang kerusakan ────────────────────────────────────────────────
#  Simpan TOKEN_ELEMEN dulu — kalau tidak, pemulihan ikut rusak.
ASLI_ELEMEN = dict(getattr(K, 'TOKEN_ELEMEN', {}) or {})


def rusak(kunci):
    """Versi rusak: semua elemen jadi 9 token (harga tidak sah)."""
    return 9


K.token_elemen = rusak
if hasattr(K, 'TOKEN_ELEMEN'):
    K.TOKEN_ELEMEN = dict.fromkeys(K.TOKEN_ELEMEN, 9)

ARTIKEL = {'judul': 'Uji', 'elemen': {'gap': 'isi', 'state_of_art': 'isi',
                                      'hook': 'isi'}}
d = K.daftar_revisi(ARTIKEL)
harga = {i['kunci'].split(':', 1)[1]: i['token'] for i in d
         if i['kunci'].startswith('elemen:')}
print("  harga SETELAH dirusak:", {k: v for k, v in harga.items()
                                   if k in ('gap', 'state_of_art', 'hook')})

gagal_terdeteksi = (harga.get('gap') != 3)
print(f"  {'✅' if gagal_terdeteksi else '❌'} gerbang AKAN menangkap kerusakan")
print(f"     (gap harus 3, hasil rusak = {harga.get('gap')})")

#  ── Pulihkan ────────────────────────────────────────────────────────
K.token_elemen = asli
if ASLI_ELEMEN:
    K.TOKEN_ELEMEN = ASLI_ELEMEN
d2 = K.daftar_revisi(ARTIKEL)
harga2 = {i['kunci'].split(':', 1)[1]: i['token'] for i in d2
          if i['kunci'].startswith('elemen:')}
pulih = harga2.get('gap') == 3
print(f"  {'✅' if pulih else '❌'} setelah dipulihkan, gap kembali 3")

sys.exit(0 if (gagal_terdeteksi and pulih) else 1)
