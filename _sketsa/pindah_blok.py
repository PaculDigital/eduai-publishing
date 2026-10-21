import pathlib
p = pathlib.Path('/opt/data/services/eduai-publishing/app/ai.py')
s = p.read_text()

awal = s.index('    # ── KONTEKS TETANGGA (ACC Bos 24Sep26 — "Opsi 1") ────────────────────')
akhir = s.index('    if len(komentar) > AI_MAX_KOMENTAR:')
blok = s[awal:akhir]
s = s[:awal] + s[akhir:]
print(f'blok konteks dipotong: {len(blok)} kar')

titik = s.index('        user_msg = (')
s = s[:titik] + blok + '\n' + s[titik:]
p.write_text(s)
print('blok konteks dipindah SEBELUM user_msg')
