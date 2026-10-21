"""UJI PIPA — 2 ARAH + BERGIGI (standar Bos).

  SEHAT   : balasan AI yang BENAR → HARUS lolos
  DIRUSAK : balasan AI yang CACAT → HARUS ditolak (bukti pagar bergigi)

Setiap pagar diuji dengan MEMOTONGNYA lalu MENJALANKAN (bukan baca teks).
"""
import pathlib
import sys

sys.path.insert(0, '/app')
from app.pipa import (Editan, cari_paragraf, cukup_panjang, normal,   # noqa: E402
                      periksa, pisah_paragraf)

LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}' + (f' — {bukti}' if bukti else ''))
    else:
        GAGAL += 1
        print(f'  ❌ {nama}' + (f' — {bukti}' if bukti else ''))
    return bool(syarat)


# ── Bahan naskah nyata (potongan proposal Bos) ───────────────────────────
NAS = (
    'PENGARUH KUALITAS KEHIDUPAN KERJA DAN EFIKASI DIRI DIGITAL\n\n'
    'Perkembangan pesat teknologi dan transformasi digital telah mengubah '
    'lanskap kerja organisasi secara mendasar dalam satu dekade terakhir.\n\n'
    'Account Officer dituntut memiliki kesiapan digital agar mampu '
    'beradaptasi dengan perubahan proses layanan yang berlangsung cepat.\n\n'
    'Penelitian ini menguji peran kesiapan digital sebagai variabel '
    'mediasi antara kualitas kehidupan kerja dan kinerja adaptif.'
)

print('═' * 74)
print('A. PEMECAH PARAGRAF (aturan tunggal)')
print('═' * 74)
cek('A1 naskah 4 paragraf', len(pisah_paragraf(NAS)) == 4,
    f'{len(pisah_paragraf(NAS))} paragraf')
cek('A2 teks \\n tunggal = 1 paragraf (jujur, bukan dipaksa)',
    len(pisah_paragraf(NAS.replace('\n\n', '\n'))) == 1)

print()
print('═' * 74)
print('B. PENCARIAN PARAGRAF — SEHAT')
print('═' * 74)
par = pisah_paragraf(NAS)
kutip = 'Perkembangan pesat teknologi dan transformasi digital telah mengubah lanskap kerja organisasi secara mendasar dalam satu dekade terakhir.'
idx, st, sk = cari_paragraf(par, kutip)
cek('B1 kutipan persis → cocok di indeks 1', st == 'cocok' and idx == [1],
    f'{st} {idx} skor={sk:.3f}')

idx, st, sk = cari_paragraf(par, kutip.replace('teknologi', 'tehnologi'))
cek('B2 salah ketik 1 huruf → toleran', st == 'toleran' and idx == [1],
    f'{st} {idx} skor={sk:.3f}')

idx, st, _ = cari_paragraf(par, 'Kalimat yang tidak pernah ada di naskah ini.')
cek('B3 karangan → tak_ketemu (WAJIB tolak)', st == 'tak_ketemu', st)

#  kembar
par2 = par + [kutip]
idx, st, _ = cari_paragraf(par2, kutip)
cek('B4 kalimat kembar → "kembar" + semua posisi', st == 'kembar' and len(idx) == 2,
    f'{st} {idx}')

print()
print('═' * 74)
print('C. BENTUK BALASAN AI — SEHAT vs DIRUSAK')
print('═' * 74)
BAIK = ('[PROFIL] Paradigma=kuantitatif; Desain=survei\n\n'
        '[K1-KUTIP-ASLI] ' + kutip + '\n'
        '[K1-GANTI-JADI] Transformasi digital dalam satu dekade terakhir telah '
        'mengubah lanskap kerja organisasi secara mendasar. Perubahan ini '
        'menuntut kesiapan digital setiap Account Officer.')

h = periksa(BAIK, NAS)
cek('C1 balasan BAIK → lolos', h.ok and len(h.editan) == 1,
    f'ok={h.ok} editan={len(h.editan)} profil={h.profil!r}')
cek('C2 editan menunjuk paragraf BENAR (indeks 1)',
    h.ok and h.editan[0].indeks == [1], f'{h.editan[0].indeks if h.ok else "-"}')
cek('C3 tidak ada yang ditolak', h.ok and not h.ditolak)

#  DIRUSAK 1: tanpa blok
h = periksa('[PROFIL] Paradigma=kuantitatif\n\nIni naskah hasil revisi lengkap...',
            NAS)
cek('C4 DIRUSAK: tanpa blok KUTIP/GANTI → DITOLAK', not h.ok, h.pesan[:70])

#  DIRUSAK 2: kutipan karangan
#  ⚠️ Yang diuji: `ok` HARUS False. `editan` boleh tetap terisi — itu
#     SENGAJA, supaya laporan ke mahasiswa bisa menyebut catatan mana
#     yang belum bisa dikerjakan (jujur, bukan disembunyikan).
RUSAK_KUTIP = BAIK.replace(kutip, 'Kalimat ini tidak ada di naskah mana pun.')
h = periksa(RUSAK_KUTIP, NAS)
cek('C5 DIRUSAK: kutipan karangan → ok=False (jangan menebak)',
    (not h.ok) and h.ditolak and h.ditolak[0]['sebab'] == 'tidak_ketemu',
    f"ok={h.ok} ditolak={[d['sebab'] for d in h.ditolak]}")

#  DIRUSAK 3: kutipan kembar
#  ⚠️ Pesan ke mahasiswa sengaja TIDAK memakai istilah teknis ("kembar");
#     yang diuji = keadaan ditolaknya, bukan kata di pesan.
NAS_KEMBAR = NAS + '\n\n' + kutip
h = periksa(BAIK, NAS_KEMBAR)
cek('C6 DIRUSAK: kutipan kembar → ok=False + sebab "kembar"',
    (not h.ok) and h.ditolak and h.ditolak[0]['sebab'] == 'kembar',
    f"ok={h.ok} ditolak={[d['sebab'] for d in h.ditolak]}")

#  DIRUSAK 4: GANTI-JADI raksasa
RUSAK_PANJANG = BAIK.replace('[K1-GANTI-JADI] ', '[K1-GANTI-JADI] ' + ('kata ' * 200))
h = periksa(RUSAK_PANJANG, NAS)
cek('C7 DIRUSAK: GANTI-JADI 60× lebih panjang → DITOLAK',
    not h.ok and h.ditolak and h.ditolak[0]['sebab'] == 'ganti_terlalu_panjang',
    h.ditolak[0]['sebab'] if h.ditolak else '-')

#  Cakupan tolak → bukan kegagalan
TOLAK = ('[PROFIL] Paradigma=kuantitatif\n\n'
         '[K1-CAKUPAN: tolak]\nBagian itu tidak ada di potongan saya.')
h = periksa(TOLAK, NAS)
cek('C8 AI bilang "tolak" → lolos sebagai "tidak ada perubahan" (bukan galat)',
    h.ok and not h.editan, h.pesan[:70])

#  TIDAK ADA PERUBAHAN
h = periksa('[PROFIL] Paradigma=kuantitatif\n\nTIDAK ADA PERUBAHAN', NAS)
cek('C9 "TIDAK ADA PERUBAHAN" → lolos jujur', h.ok and not h.editan, h.pesan[:60])

print()
print('═' * 74)
print('D. PAGAR PANJANG NASKAH (pagar bencana)')
print('═' * 74)
ok, p = cukup_panjang(NAS, NAS)
cek('D1 naskah utuh → lolos', ok, p[:50])
ok, p = cukup_panjang(NAS, NAS[:int(len(NAS) * 0.7)])
cek('D2 susut 30% (wajar) → lolos', ok, f'ok={ok}')
ok, p = cukup_panjang(NAS, 'Rumusan masalah diperbaiki.')
cek('D3 DIRUSAK: susut 99% (BENCANA 25Sep26) → DITOLAK',
    not ok and 'dibatalkan' in p, p[:90])
ok, p = cukup_panjang(NAS, '')
cek('D4 DIRUSAK: hasil kosong → DITOLAK', not ok, p[:70])

print()
print('═' * 74)
print('E. BERGIGI — pagar dirusak HARUS menggagalkan uji')
print('═' * 74)
#  Bukti pagar C5 benar-benar bergigi: kalau pagar dilepas, uji C5 jadi gagal
import app.pipa as P                                                  # noqa: E402
asli_fn = P.cari_paragraf


def cari_tanpa_pagar(paragraf, kutip):
    return [0], 'cocok', 1.0          # selalu "ketemu" = pagar dilepas


P.cari_paragraf = cari_tanpa_pagar
h_lepas = P.periksa(RUSAK_KUTIP, NAS)
P.cari_paragraf = asli_fn
cek('E1 pagar DILEPAS → kutipan karangan lolos (bukti pagar BERGIGI)',
    h_lepas.ok, f'ok={h_lepas.ok} ← memang lolos; jadi uji C5 memang menjaga')

ok_lepas, _ = (lambda: (True, ''))()
#  Bukti pagar panjang bergigi
P.PANJANG_MIN_RASIO = 0.0
ok2, _ = P.cukup_panjang(NAS, 'Rumusan masalah diperbaiki.')
P.PANJANG_MIN_RASIO = 0.60
cek('E2 pagar panjang DILEPAS → susut 99% lolos (bukti pagar BERGIGI)',
    ok2, f'ok={ok2} ← memang lolos; jadi uji D3 memang menjaga')

print()
print('═' * 74)
print(f'HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
print('═' * 74)
sys.exit(1 if GAGAL else 0)
