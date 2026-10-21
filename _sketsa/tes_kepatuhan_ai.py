"""TES KEPATUHAN AI — apakah AI mau membalas bentuk [KUTIP-ASLI]/[GANTI-JADI]?

TUJUAN: sebelum menulis kode pipa, BUKTIKAN dulu AI patuh atau tidak.
    Kalau tidak patuh, rancangan harus diubah (jangan koding sia-sia).

Diuji 3 gaya permintaan (makin tegas):
  A. santai   — "tolong sebutkan kalimat asli dan penggantinya"
  B. tegas    — format penanda tegas + larangan
  C. naskah utuh (pembanding) — apakah AI mau salin utuh? (biaya token)
"""
import asyncio
import json
import pathlib
import re
import sys

sys.path.insert(0, '/app')
from app.ai import (_revisi_dengan_failover, _teks_dari_docx,      # noqa: E402
                    potong_cerdas)

DOCX = pathlib.Path('/app/_naskah_bos_uji.docx')
KOMENTAR = ('Paragraf rumusan masalah belum menyebut kesenjangan penelitian. '
            'Mohon perbaiki.')

t = _teks_dari_docx(DOCX)
bagian = potong_cerdas(t)
potongan = bagian[0]
print(f'naskah {len(t):,} kar → {len(bagian)} bagian · potongan 1 = '
      f'{len(potongan):,} kar')

GAYA = {
  'A. SANTAI': (
    f'NASKAH:\n{potongan[:6000]}\n\n'
    f'CATATAN PEMBIMBING:\n- {KOMENTAR}\n\n'
    'Sebutkan kalimat asli yang perlu diubah, lalu tuliskan kalimat '
    'penggantinya. Jangan salin seluruh naskah.'),
  'B. TEGAS': (
    f'NASKAH:\n{potongan[:6000]}\n\n'
    f'CATATAN PEMBIMBING:\n- {KOMENTAR}\n\n'
    'BALAS DENGAN FORMAT TEPAT SEPERTI INI (tidak boleh bentuk lain):\n'
    '[K1-KUTIP-ASLI] <salin PERSIS satu kalimat dari naskah yang diganti>\n'
    '[K1-GANTI-JADI] <teks penggantinya>\n\n'
    'ATURAN KERAS:\n'
    '- DILARANG menyalin seluruh naskah ke jawaban.\n'
    '- KUTIP-ASLI harus PERSIS sama dengan yang ada di naskah '
    '(huruf demi huruf).\n'
    '- Kalau tidak ada yang perlu diubah, tulis: TIDAK ADA PERUBAHAN\n'
    '- Tidak ada penjelasan lain di luar format.'),
  'C. NASKAH UTUH': (
    f'NASKAH:\n{potongan[:6000]}\n\n'
    f'CATATAN PEMBIMBING:\n- {KOMENTAR}\n\n'
    'Perbaiki lalu kembalikan SELURUH naskah lengkap hasil perbaikan.'),
}


def kukur(teks: str) -> dict:
    """Ukur kepatuhan jawaban."""
    d = {
        'panjang': len(teks),
        'penanda_kutip': len(re.findall(r'KUTIP-ASLI', teks, re.I)),
        'penanda_ganti': len(re.findall(r'GANTI-JADI', teks, re.I)),
        'penanda_lain': len(re.findall(r'\[K\d', teks)),
        'menolak': bool(re.search(r'TIDAK ADA PERUBAHAN', teks, re.I)),
        'menyalin_utuh': len(teks) > len(potongan) * 0.8,
    }
    return d


for nama, pesan in GAYA.items():
    print()
    print('═' * 74)
    print(nama)
    print('═' * 74)
    try:
        konten, model, info = asyncio.run(
            _revisi_dengan_failover(pesan, 1, naskah_banding=potongan[:6000]))
    except Exception as e:                                          # noqa: BLE001
        print(f'  ❌ GAGAL: {type(e).__name__}: {str(e)[:200]}')
        continue
    d = kukur(konten)
    print(f'  model   : {model}')
    print(f'  token   : in={info.get("token_in"):,} out={info.get("token_out"):,}')
    print(f'  panjang : {d["panjang"]:,} kar')
    print(f'  penanda : KUTIP-ASLI={d["penanda_kutip"]} '
          f'GANTI-JADI={d["penanda_ganti"]} penanda-lain={d["penanda_lain"]}')
    print(f'  menolak : {d["menolak"]} · menyalin utuh: {d["menyalin_utuh"]}')
    print()
    print('  --- 700 kar pertama jawaban ---')
    print('  ' + konten[:700].replace('\n', '\n  '))
    pathlib.Path(f'/tmp/tes_ai_{nama[0]}.txt').write_text(konten)
