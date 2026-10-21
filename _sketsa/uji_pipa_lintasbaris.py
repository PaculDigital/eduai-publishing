#!/usr/bin/env python3
"""UJI 2 ARAH — FIX PIPA LINTAS POTONGAN (29Sep26).

Akaran: naskah tertentu keluar sbg potongan PER BARIS (`\\n\\n` tiap ~75
kar) → kutip 2+ kalimat melewati batas potongan → `tak_ketemu` walaupun
teks ADA (terukur: k in normal(naskah)=True).

SEHAT (harus LULUS):
  S1  kutip lintas 3 baris → periksa ok + editan 1
  S2  regresi: paragraf utuh normal (jalur lama) → tetap cocok
DIRUSAK (harus GAGAL):
  R1  kutip karangan (tak ada) → ok=False, ditolak 'tidak_ketemu'
  R2  kutip ambigu kembar (muncul 2×) → ditolak 'kembar'
  R3  kutip dicampur teks karangan → tak_ketemu (tidak dicocokkan sebagian)

Jalankan DARI HOST:  python3 _sketsa/uji_pipa_lintasbaris.py
"""
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('_pipa_uji', HERE / 'app' / 'pipa.py')
P = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = P          # dataclass butuh modul terdaftar (from __future__ annotations)
spec.loader.exec_module(P)

# ── naskah berbentuk BARIS (tiruan persis kasus nyata) ──
BARIS = [
    'Pesatnya perkembangan teknologi informasi pada era digital sekarang ini,',
    'mengharuskan para pelaku usaha untuk mengikuti perkembangan zaman. Sehingga',
    'dapat memenangkan persaingan terhadap perusahaan lainnya. Salah satu dampak',
    'perkembangan teknologi informasi itu adalah meningkatnya pengguna media sosial',
    'di kalangan masyarakat modern sehingga strategi pemasaran ikut berubah total',
    'dan perusahaan dituntut hadir secara digital pada setiap kanal interaksi.',
    'Saya setuju dengan penelitian ini.',
    'kerangka analisis yang dipakai penulis sebelumnya sudah tepat dan terukur',
    'Saya setuju dengan penelitian ini.',
    'namun perlu diperbarui agar sesuai dengan perkembangan metodologi terkini',
]
NASAH_BARIS = '\n\n'.join(BARIS)

# ── naskah paragraf normal (regresi jalur lama) ──
NASAH_PAR = ('\n\n'.join([
    'Latar belakang penelitian ini adalah meningkatnya pengguna media sosial '
    'di kalangan mahasiswa sehingga strategi pemasaran ikut berubah total dan '
    'perusahaan dituntut hadir secara digital pada setiap kanal interaksi.',
    'Berdasarkan uraian tersebut peneliti tertarik mengkaji fenomena itu '
    'lebih lanjut dengan pendekatan kuantitatif pada tahun berjalan.',
]))


def jawab(kutip, ganti):
    return ('[PROFIL] Paradigma=kuantitatif\n\n'
            '[K1-KUTIP-ASLI]\n' + kutip +
            '\n[K1-GANTI-JADI]\n' + ganti)


GANTI = ('Perkembangan teknologi informasi telah mengubah lanskap persaingan '
         'usaha secara mendasar, sehingga pelaku usaha dituntut menyesuaikan '
         'strategi pemasaran agar tetap mampu bersaing dengan perusahaan '
         'lainnya di era digital.')

hasil = []

# S1 — kutip lintas 3 baris (kasus G1/G3/B2)
kutip_lintas = '\n\n'.join(BARIS[0:3])
h = P.periksa(jawab(kutip_lintas, GANTI), NASAH_BARIS)
lolos_s1 = bool(h.ok and h.editan and h.editan[0].keadaan == 'cocok'
                and len(h.editan[0].indeks or []) >= 3)
hasil.append(('S1 lintas 3 baris', lolos_s1,
              f'ok={h.ok} editan={len(h.editan)} '
              f'keadaan={getattr(h.editan[0], "keadaan", None)} '
              f'idx={getattr(h.editan[0], "indeks", None)} '
              f'{(h.pesan or "")[:60]}'))

# S2 — regresi jalur lama (kutip 1 kalimat di paragraf utuh)
kutip_par = 'Latar belakang penelitian ini adalah meningkatnya pengguna media sosial'
h = P.periksa(jawab(kutip_par, GANTI), NASAH_PAR)
lolos_s2 = bool(h.ok and h.editan)
hasil.append(('S2 regresi paragraf utuh', lolos_s2,
              f'ok={h.ok} editan={len(h.editan)} {(h.pesan or "")[:60]}'))

# R1 — kutip karangan total
h = P.periksa(jawab('Fenomena gunung meletus di tengah kota menjadi dasar '
                    'penelitian penulis pada tahun dua ribu dua puluh lima ini.',
                    GANTI), NASAH_BARIS)
rusak_r1 = bool(not h.ok and any(d.get('sebab') == 'tidak_ketemu'
                                 for d in (h.ditolak or [])))
hasil.append(('R1 kutip karangan → tolak', rusak_r1,
              f'ok={h.ok} ditolak={h.ditolak} {(h.pesan or "")[:60]}'))

# R2 — kutip ambigu (muncul 2×)
h = P.periksa(jawab('Saya setuju dengan penelitian ini.', GANTI), NASAH_BARIS)
rusak_r2 = bool(not h.ok and any(d.get('sebab') == 'kembar'
                                 for d in (h.ditolak or [])))
hasil.append(('R2 kutip kembar → tolak', rusak_r2,
              f'ok={h.ok} ditolak={h.ditolak} {(h.pesan or "")[:60]}'))

# R3 — kutip asli dicampur kalimat karangan → wajib tak_ketemu
h = P.periksa(jawab(kutip_lintas + ' dan hal itu terbukti dari data lapangan '
                                   'yang sangat fantastis luar biasa sekali.',
                    GANTI), NASAH_BARIS)
rusak_r3 = bool(not h.ok)
hasil.append(('R3 kutip+karangan → tolak', rusak_r3,
              f'ok={h.ok} ditolak={h.ditolak} {(h.pesan or "")[:60]}'))

print('══ UJI PIPA LINTAS POTONGAN — 2 ARAH ══')
semua = True
for nama, lulus, detil in hasil:
    semua = semua and lulus
    print(f"  {'✅' if lulus else '❌'} {nama}: {detil}")
print('KESIMPULAN:', 'SEMUA LULUS' if semua else 'ADA GAGAL')
sys.exit(0 if semua else 1)
