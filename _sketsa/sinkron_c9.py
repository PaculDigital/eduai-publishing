import pathlib

TXT_FLAG = ('\n| **C9** | ✅ **DITUTUP 25Sep26** — BUG NYATA "SUKSES PALSU": hasil revisi '
    'KOSONG (0 kar) disimpan sebagai versi TERPAKAI -> naskah mahasiswa lenyap, tapi '
    'notifikasi bilang "berhasil". Akar: AI hanya MENYALIN naskah -> bersihkan_jawaban_ai() '
    'buang salinan -> 0 kar -> simpan_versi tetap simpan. 3 pagar (ACC Bos "1"): _valid() '
    'tolak salinan - _revisi_kerja() GAGAL + kembalikan kuota - token_revisi tanpa '
    'or len(info_potong). Uji _uji_c9_kosong.py 16/0 BERGIGI. Bukti: file 47 v59 = 0 kar '
    'terpakai=1. |\n')

TXT_SKILL = ('\n- **C9 OK 25Sep26** - SUKSES PALSU: hasil revisi **0 kar** disimpan sebagai '
    'versi `terpakai=1` -> naskah mahasiswa KOSONG padahal status "selesai". Akar: AI hanya '
    'menyalin naskah -> `bersihkan_jawaban_ai()` buang salinan -> `simpan_versi("")` tetap '
    'simpan. 3 pagar: `_valid()` tolak salinan (<40 kar) - `_revisi_kerja()` raise 503 + '
    'kembalikan kuota - `token_revisi` tanpa `or len(info_potong)`. Uji `_uji_c9_kosong.py` '
    '16/0 BERGIGI. **PELAJARAN:** asersi `str in KODE` TIDAK bergigi - pakai regex + cek '
    'URUTAN posisi + cari SEMUA kemunculan pola.\n')

for path, txt in (('FLAG_LANJUT_DISINI.md', TXT_FLAG),
                  ('/opt/data/skills/devops/eduai-publishing/SKILL.md', TXT_SKILL)):
    p = pathlib.Path(path)
    s = p.read_text()
    if 'C9' in s:
        print('sudah ada:', path)
        continue
    p.write_text(s.rstrip() + txt)
    print('DITAMBAH:', path)
