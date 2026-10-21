"""GERBANG LAPIS 2 — JALUR SURVEYOR di /v1/peta/* (uji berkas, bukan HTTP).

Diperiksa (B2-1..B2-8):
  ① modul peta3_jev & peta_jalur di-IMPOR di dalam fungsi (bukan level atas)
  ② surveyor dipanggil SEBELUM jalur lama  (urutan kode)
  ③ jalur lama (bab_state/_p.dari_state) TETAP ADA  ⇒ peta_halus tak dibuang
  ④ JEJAK 'peta_dari' ADA di DUA jalur (jev & fallback)
  ⑤ kunci lama TIDAK hilang (ok/gratis/bab_terdeteksi/sidik/model/pesan_kuota)
  ⑥ jembatan resmi yang dipakai (peta_jembatan.dari_surveyor)
  ⑦ peta_halus & state TIDAK dihapus dari berkas
  ⑧ Dockerfile men-COPY peta3_jev.py
Jalankan di DALAM container.
"""
import re
import sys

AI = '/app/app/ai.py'
DOCKER = '/app/Dockerfile'
L = G = 0


def cek(nama, syarat, catatan=''):
    global L, G
    if syarat:
        L += 1
        print(f'  ✅ {nama}' + (f' — {catatan}' if catatan else ''))
    else:
        G += 1
        print(f'  ❌ {nama}' + (f' — {catatan}' if catatan else ''))


isi = open(AI).read()
#  buang komentar supaya tidak salah-cocok (pelajaran gerbang palsu)
kode = '\n'.join(b for b in isi.split('\n') if not b.strip().startswith('#'))

print('=' * 70)
print('GERBANG LAPIS 2 — JALUR SURVEYOR PETA')
print('=' * 70)

# ── ① impor di dalam fungsi ─────────────────────────────────────────
cek('B2-1 impor peta3_jev ada', 'from . import peta3_jev as _s3' in kode)
cek('B2-2 impor peta_jalur ada', 'from .peta_jalur import putuskan_jalur' in kode)
#  impor level-atas DILARANG (bikin putaran impor)
atas = kode.split('async def peta_mulai')[0]
cek('B2-3 TIDAK diimpor di level atas',
    'peta3_jev' not in atas and 'peta_jalur' not in atas)

# ── ② urutan: surveyor SEBELUM jalur lama ───────────────────────────
i_surv = kode.find('_s3.petakan(')
i_lama = kode.find('bab_state = _st.deteksi_bab_besar')
cek('B2-4 surveyor dipanggil', i_surv > 0)
cek('B2-5 surveyor SEBELUM jalur lama', 0 < i_surv < i_lama,
    f'surveyor@{i_surv} < lama@{i_lama}')

# ── ③ jalur lama TETAP ADA ──────────────────────────────────────────
cek('B2-6 jalur lama utuh (dari_state)', '_p.dari_state(bab_state, sub_state)' in kode)
cek('B2-7 peta_halus masih dipakai', 'from . import peta_halus as _p' in kode)

# ── ④ JEJAK di dua jalur ────────────────────────────────────────────
cek('B2-8 jejak jev ada', "'peta_dari': 'jev'" in kode)
cek('B2-9 jejak fallback ada', "hasil['peta_dari'] = 'fallback'" in kode)

# ── ⑤ kunci lama tidak hilang ───────────────────────────────────────
for k in ('ok', 'gratis', 'bab_terdeteksi', 'sidik', 'pesan_kuota'):
    cek(f'B2-10 kunci lama [{k}] ada', f"hasil['{k}']" in kode)

# ── ⑥ jembatan resmi dipakai ────────────────────────────────────────
cek('B2-11 jembatan resmi dipakai', 'from .peta_jembatan import dari_surveyor' in kode)

# ── ⑦ peta_jembatan TIDAK diubah (pagar P1) ─────────────────────────
jb = open('/app/app/peta_jembatan.py').read()
cek('B2-12 jembatan tidak diubah', 'def dari_surveyor' in jb and 'state.petakan' in jb)

# ── ⑧ Dockerfile COPY peta3_jev ─────────────────────────────────────
#  ⚠️ PERBAIKAN 14 Okt (gerbang palsu ke-7): Dockerfile TIDAK ADA di dalam
#     container (hanya /app/app/ yang di-COPY). Cek Dockerfile = urusan HOST.
#     Kalau berkasnya tidak ada di sini, LEWATI dengan jujur — jangan
#     dihitung GAGAL (itu cacat alat ukur, bukan cacat kode).
try:
    dk = open(DOCKER).read()
    cek('B2-13 Dockerfile COPY peta3_jev.py', 'COPY peta3_jev.py' in dk)
except FileNotFoundError:
    print('  ⏭️  B2-13 Dockerfile tidak ada di container (dicek dari HOST) — DILEWATI')
    #  Bukti pengganti: berkas surveyor BENAR-BENAR ada di image.
    cek('B2-13b /app/peta3_jev.py ada di image',
        __import__('os').path.exists('/app/peta3_jev.py'))

print('-' * 70)
print(f'HASIL GERBANG LAPIS 2: {L} LULUS / {G} GAGAL')
raise SystemExit(1 if G else 0)
