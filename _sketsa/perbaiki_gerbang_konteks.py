"""PERBAIKAN AKAR: pindahkan PEMROSESAN AI keluar dari `if konteks tetangga`.

🔴 AKAR (terbukti 25Sep26):
   Badan loop `for idx, potongan in enumerate(bagian_naskah)` berisi:
       N=8   kepala = ...
       N=8   konteks_terpakai = ''
       N=8   if (jml_bagian == 1 and bab != BAB_SELURUH and '.' in bab ...):
       N=12      try: <bangun konteks tetangga>  ... except/finally
       N=12      user_msg = (...)                ⚠️ DALAM GERBANG
       N=12      if _lapor: ...                  ⚠️ DALAM GERBANG
       N=12      try: await _revisi_dengan_failover(...)  ⚠️ DALAM GERBANG
       N=12      konten = bersihkan_jawaban_ai(...)       ⚠️ DALAM GERBANG
       N=12      if not konten: 503 (C9)                  ⚠️ DALAM GERBANG
       N=12      hasil_bagian.append(konten)              ⚠️ DALAM GERBANG

   ⇒ Saat `jml_bagian > 1`, gerbang `jml_bagian == 1` False → SELURUH
     pemrosesan AI DILEWATI → `hasil_bagian` kosong → C10 → 503.
   ⇒ SEMUA revisi naskah >55.000 kar (2+ bagian) SELALU gagal.

🛠️ PERBAIKAN: geser ke-4 blok itu KELUAR (kurangi 4 spasi: N=12 → N=8),
   sehingga berada di BADAN LOOP, BUKAN di dalam `if`.
   `user_msg` sudah memuat `konteks_terpakai` (yaitu '' bila gerbang tak jalan)
   → perilaku saat 1 bagian & sub-bab TIDAK berubah sama sekali.

📌 Setelah gerbang, WAJIB kembalikan `potongan` (bukan `isi_target`) supaya
   naskah yang divalidasi C9 = yang benar-benar dikirim ke AI.
"""
import ast
import pathlib
import shutil

SRC = pathlib.Path('app/ai.py')
CAD = pathlib.Path('_arsip/pre-pipa-20260925/ai.py.cadangan-fix')
shutil.copy2(SRC, CAD)
baris = SRC.read_text().split('\n')
print(f'ai.py {len(baris)} baris · cadangan → {CAD}')

#  ── Temukan ANCHOR (teks unik) ──
i_user = next(i for i, b in enumerate(baris)
              if b.startswith(' ' * 12) and b.strip() == 'user_msg = (')
i_app = next(i for i, b in enumerate(baris)
             if b.startswith(' ' * 12) and b.strip() == 'hasil_bagian.append(konten)')
i_if = next(i for i, b in enumerate(baris)
            if b.startswith(' ' * 8) and b.strip().startswith('if (')
            and 'jml_bagian == 1' in b)
print(f'if konteks   baris {i_if + 1}')
print(f'user_msg     baris {i_user + 1}')
print(f'hasil_bagian baris {i_app + 1}')

assert i_if < i_user < i_app, 'urutan anchor tidak masuk akal'

#  ── SISIPKAN penutup `if` + baris kosong SEBELUM user_msg ──
#     (agar `if konteks` tetap punya blok `try/except` yg sah)
sisip = ['        #  🛠️ 25Sep26 — batas gerbang konteks tetangga BERAKHIR di sini.',
         '        #     Di bawah ini PEMROSESAN AI berjalan untuk SETIAP bagian',
         '        #     (sebelumnya salah berada di dalam gerbang → naskah besar',
         '        #     selalu gagal karena `jml_bagian == 1` False).',
         '']

#  ── Geser: kurangi 4 spasi untuk baris N>=12 dalam rentang [i_user, i_app] ──
baru = baris[:i_user] + sisip
for i in range(i_user, i_app + 1):
    b = baris[i]
    if not b.strip():
        baru.append(b)
        continue
    n = len(b) - len(b.lstrip())
    baru.append(b[4:] if n >= 12 else b)
baru += baris[i_app + 1:]

teks2 = '\n'.join(baru)

#  ── VERIFIKASI ──
ast.parse(teks2)
print('\n✅ sintaks OK')

#  ── Pastikan `if konteks` masih punya blok (bukan if kosong) ──
pohon = ast.parse(teks2)
for n in ast.walk(pohon):
    if isinstance(n, ast.AsyncFunctionDef) and n.name == '_revisi_kerja':
        for x in n.body:
            if isinstance(x, ast.For) and 'bagian_naskah' in ast.unparse(x.iter):
                body = x.body
                print(f'badan loop sekarang: {len(body)} pernyataan')
                print(f'   1) {ast.unparse(body[0])[:60]}')
                print(f'   2) {ast.unparse(body[1])[:60]}')
                print(f'   3) {type(body[2]).__name__}: '
                      f'{ast.unparse(body[2])[:60]}')
                #  cari pernyataan yg memanggil AI — WAJIB di level badan loop
                lapis = [ast.unparse(y)[:50] for y in body
                         if 'failover' in ast.unparse(y)
                         or 'hasil_bagian.append' in ast.unparse(y)]
                print(f'   panggilan AI / append di badan loop: {len(lapis)}')
                for x2 in lapis:
                    print(f'      · {x2}')

SRC.write_text(teks2)
print(f'\n💾 tersimpan · {len(teks2.split(chr(10)))} baris')
