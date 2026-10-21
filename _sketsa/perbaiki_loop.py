"""PERBAIKAN: indentasi ulang `_revisi_kerja` — loop per-bagian DIHIDUPKAN.

🔴 AKAR BUG (ditemukan 25Sep26, terbukti AST):
   `for idx, potongan in enumerate(bagian_naskah, start=1):` (baris 1763)
   isinya CUMA menghitung `kepala`. Seluruh pemrosesan AI ada DI LUAR loop
   (indentasi 8 spasi, sejajar `for`) → hanya bagian TERAKHIR diproses,
   `hasil_bagian` berisi 1 isi → C9/C10 menangkap → 503
   "hasil revisi kosong" untuk SETIAP naskah >55.000 kar.

   Bukti nyata: 4 percobaan E2E (proses 103,104,105,106) semuanya
   `token_in=0` = AI hanya dipanggil 1× untuk potongan terakhir.

CARA PERBAIKAN (bukan tambalan):
   • Semua pernyataan dari baris "KONTEKS TETANGGA" (1768) s/d
     "hasil_bagian.append(konten)" (1882) DINAIIKKAN indentasinya +4 spasi
     → masuk ke dalam loop.
   • Blok "KONTEKS TETANGGA" pindah KE DALAM loop (memang tempatnya: tiap
     bagian punya konteks sendiri).
   • TIDAK mengubah logika apa pun — hanya indentasi + urutan yang benar.

Aturan Bos: sebelum ubah berkas → BACKUP (sudah: ai.py.sebelum-loop).
"""
import pathlib
import re

P = pathlib.Path('/opt/data/services/eduai-publishing/app/ai.py')
s = P.read_text()

#  ── Batas blok yang harus masuk ke dalam loop ──
AWAL = '    # ── KONTEKS TETANGGA (ACC Bos 24Sep26 — "Opsi 1") ────────────────────'
AKHIR = '        hasil_bagian.append(konten)\n'

i_awal = s.index(AWAL)
i_akhir = s.index(AKHIR) + len(AKHIR)
blok = s[i_awal:i_akhir]
print(f'blok yang dinaikkan: {len(blok):,} kar, '
      f'{blok.count(chr(10))} baris')

#  ── Verifikasi: blok ini HARUS berakhir dengan hasil_bagian.append ──
assert blok.rstrip().endswith('hasil_bagian.append(konten)'), 'batas salah!'

#  ── Naikkan indentasi +4 untuk SEMUA baris (kecuali baris kosong) ──
def naikkan(baris):
    if not baris.strip():
        return baris
    return '    ' + baris

blok_baru = '\n'.join(
    naikkan(b) if b.strip() else b for b in blok.split('\n'))

#  ── Baris sesudahnya: `# 4c) HITUNG TOKEN REVISI` harus tetap 4 spasi ──
s_baru = s[:i_awal] + blok_baru + s[i_akhir:]

#  ── `kepala` sudah di dalam loop (baris 1764) → cek hasilnya ──
P.write_text(s_baru)
print(f'berkas ditulis: {len(s_baru):,} byte (dari {len(s):,})')

#  ── Verifikasi HASIL: loop sekarang berisi banyak pernyataan ──
import ast
t = ast.parse(s_baru)
for n in ast.walk(t):
    if isinstance(n, ast.AsyncFunctionDef) and n.name == '_revisi_kerja':
        for b in n.body:
            if isinstance(b, ast.For) and 'bagian_naskah' in ast.unparse(b.iter):
                isi = ast.unparse(b)
                print(f'✅ FOR baris {b.lineno}: {len(b.body)} pernyataan '
                      f'(dulu 1)')
                print(f'   panggil AI di dalam loop? '
                      f'{"YA" if "_revisi_dengan_failover" in isi else "TIDAK"}')
                print(f'   hasil_bagian.append di dalam loop? '
                      f'{"YA" if "hasil_bagian.append" in isi else "TIDAK"}')
