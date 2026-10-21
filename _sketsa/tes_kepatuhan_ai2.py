"""TES KEPATUHAN AI — putaran 2: komentar COCOK dengan potongan.

KENAPA ulang: putaran 1 memakai komentar "rumusan masalah" padahal potongan
    bagian-1 hanya sampai Kata Pengantar → AI benar menolak (CACAT UJI).

Putaran ini: komentar menunjuk ke isi yang MEMANG ADA di potongan,
    supaya format [KUTIP-ASLI]/[GANTI-JADI] benar-benar diuji.
"""
import asyncio
import pathlib
import re
import sys

sys.path.insert(0, '/app')
from app.ai import (_revisi_dengan_failover, _teks_dari_docx,      # noqa: E402
                    potong_cerdas)

DOCX = pathlib.Path('/app/_naskah_bos_uji.docx')
t = _teks_dari_docx(DOCX)
bagian = potong_cerdas(t)
potongan = bagian[0][:8000]

#  Cari paragraf yang BENAR-BENAR ada di potongan (kalimat isi, bukan judul)
paras = [p.strip() for p in re.split(r'\n{2,}', potongan) if len(p.strip()) > 120]
print(f'potongan {len(potongan):,} kar · paragraf isi: {len(paras)}')
target = paras[0] if paras else potongan[:500]
print(f'paragraf contoh (dipakai sebagai sasaran komentar):')
print(f'   {target[:200]}…')

KOMENTAR = ('Paragraf ini perlu ditajamkan: kalimatnya terlalu panjang dan '
            'kurang memberi penekanan pada tujuan penelitian.')

PESAN = (
    f'NASKAH:\n{potongan}\n\n'
    f'CATATAN PEMBIMBING:\n- {KOMENTAR}\n\n'
    'BALAS DENGAN FORMAT TEPAT SEPERTI INI (tidak boleh bentuk lain):\n'
    '[PROFIL] Paradigma=…; Desain=…\n'
    '[K1-KUTIP-ASLI] <salin PERSIS satu kalimat dari naskah yang kamu ganti>\n'
    '[K1-GANTI-JADI] <teks penggantinya>\n\n'
    'ATURAN KERAS:\n'
    '1. DILARANG menyalin seluruh naskah ke jawaban.\n'
    '2. KUTIP-ASLI harus PERSIS sama dengan naskah (huruf demi huruf).\n'
    '3. Kalau memang tidak ada yang perlu diubah, tulis tepat: '
    'TIDAK ADA PERUBAHAN\n'
    '4. Tidak ada penjelasan lain di luar format di atas.')

print()
print('memanggil AI…')
konten, model, info = asyncio.run(
    _revisi_dengan_failover(PESAN, 1, naskah_banding=potongan))

print()
print('═' * 74)
print('HASIL')
print('═' * 74)
print(f'model  : {model}')
print(f'token  : in={info.get("token_in"):,} out={info.get("token_out"):,}')
print(f'panjang: {len(konten):,} kar')
print(f'penanda: KUTIP-ASLI={len(re.findall("KUTIP-ASLI", konten, re.I))} · '
      f'GANTI-JADI={len(re.findall("GANTI-JADI", konten, re.I))}')

#  Apakah kutipannya BENAR-BENAR ada di naskah?
kutip = re.search(r'\[K1-KUTIP-ASLI\]\s*(.+?)(?=\[|$)', konten, re.S | re.I)
ganti = re.search(r'\[K1-GANTI-JADI\]\s*(.+?)(?=\[|$)', konten, re.S | re.I)
if kutip:
    k = kutip.group(1).strip()[:250]
    print()
    print(f'KUTIP-ASLI  : {k[:200]!r}')
    ada = k[:60] in t
    print(f'ada di naskah? {ada}  ← {"✅ cocok" if ada else "❌ TIDAK COCOK"}')
if ganti:
    print(f'GANTI-JADI  : {ganti.group(1).strip()[:250]!r}')
print()
print('--- jawaban penuh (1.200 kar) ---')
print(konten[:1200])
