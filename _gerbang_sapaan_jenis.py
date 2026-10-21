"""GERBANG SAPAAN — 20 Okt 2026. Rp 0 (tanpa AI).

🔴 AKAR YANG DITUTUP (terukur di buku pendidikan anak 3 bab):
   Bab 1 memuat **14× "Anda"** padahal jenis='pendidikan' (sapaan "kamu").
   Bab 2 & 3 = 0×. Jadi bukan model nakal — aturannya TIDAK PERNAH dikirim.

   Terbukti dari kode:
     • `tone_menulis.py` punya kunci `"sapaan": "kamu"` untuk anak & pendidikan
     • `_t['sapaan']` TIDAK DIPAKAI di satu pun prompt (grep kosong)
     • `personal` paket `pendidikan` hanya "panggil kamu langsung" — tanpa
       LARANGAN sapaan lain, padahal paket `anak` menyebut "kamu" 3×.
   ⇒ Sapaan = harapan, bukan PERINTAH. Model bebas memakai "Anda".

YANG DIUJI (semua dari PROMPT SUNGGUHAN, bukan teks kode):
  [1] Tiap prompt (intro, penutup, sub-bab, editor) MENYEBUT sapaan paketnya
  [2] Sapaan "Anda" TIDAK disuruh untuk jenis anak/pendidikan
  [3] Larangan sapaan lain ADA (bukan cuma imbauan)
  [4] jenis='umum' tetap "Anda" (tidak ikut berubah)
"""
import sys

LULUS = 0
GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama}   {bukti}')


def main():
    import buku_umum_pipeline as P
    import tone_menulis as TM

    OUT = {1: {'title': 'Bab Satu', 'subs': [('1.1', 'Sub A', 'poin a')]}}

    def prompt_semua(jenis):
        """Semua prompt yang menyentuh TONE untuk satu jenis."""
        return {
            'intro': P.architect_prompt(1, 'Bab Satu', None, None, None,
                                        'ringkasan', is_intro=True,
                                        jenis=jenis, outline=OUT),
            'penutup': P.architect_prompt(1, 'Bab Satu', None, None, None,
                                          'ringkasan', is_closing=True,
                                          jenis=jenis, outline=OUT),
            'sub_bab': P.architect_prompt(1, 'Bab Satu', '1.1', 'Sub A',
                                          'poin a', 'ringkasan',
                                          jenis=jenis, outline=OUT),
            'editor': P.editor_prompt('Sub A', 'draf teks', 'kritik',
                                      'saran', jenis=jenis),
        }

    print('\n[1] TIAP PROMPT MENYEBUT SAPAAN PAKETNYA')
    for jenis in ('anak', 'pendidikan', 'umum'):
        sapaan = TM.tone(jenis)['sapaan']
        for nama, p in prompt_semua(jenis).items():
            #  Harus ada PERINTAH sapaan, bukan sekadar kata nyasar.
            cek(f'{jenis}/{nama}: menyebut sapaan "{sapaan}" sebagai perintah',
                f'"{sapaan}"' in p and 'SAPA' in p.upper(),
                f'potongan: {p[:80]!r}')

    print('\n[2] SAPAAN "Anda" TIDAK DISURUH UNTUK anak/pendidikan')
    for jenis in ('anak', 'pendidikan'):
        for nama, p in prompt_semua(jenis).items():
            kalimat_anda = [k for k in p.split('.') if 'anda' in k.lower()]
            salah = [k for k in kalimat_anda
                     if 'dilarang' not in k.lower()
                     and 'jangan' not in k.lower()]
            cek(f'{jenis}/{nama}: tidak MENYURUH memakai "Anda"',
                not salah, f'hanya boleh muncul di larangan: {salah[:1]}')

    print('\n[3] BUKU BUKAN DEWASA TIDAK MENERIMA ATURAN DEWASA')
    #  ⚠️ Gerbang versi pertama TIDAK bergigi: suntikan "pendidikan masuk
    #     cabang dewasa" LOLOS karena yang diperiksa hanya kata larangan.
    #     Yang benar: periksa ATURAN yang benar-benar dikirim ke editor.
    for jenis in ('anak', 'pendidikan'):
        p = P.editor_prompt('Sub A', 'draf', 'kritik', 'saran', jenis=jenis)
        cek(f'{jenis}: TIDAK menerima "Personal >= 20%" gaya dewasa',
            'Personal >= 20%' not in p, f'{p[:120]!r}')
        cek(f'{jenis}: TIDAK menerima "0 pertanyaan" gaya dewasa',
            '0 pertanyaan' not in p, f'{p[:120]!r}')
        cek(f'{jenis}: ada larangan sapaan lain',
            'DILARANG memakai' in p and 'Anda' in p, f'{p[:120]!r}')

    print('\n[3b] PROMPT PENULIS (intro/penutup/sub) TIDAK MENYURUH DEWASA')
    for jenis in ('anak', 'pendidikan'):
        for nama, p in prompt_semua(jenis).items():
            cek(f'{jenis}/{nama}: tanpa aturan "Personal >= 20%"',
                'Personal >= 20%' not in p, f'{p[:100]!r}')

    print('\n[4] jenis="umum" TETAP "Anda" (tidak ikut berubah)')
    cek('umum menyapa "Anda"', TM.tone('umum')['sapaan'] == 'Anda',
        TM.tone('umum')['sapaan'])

    print(f'\n{"=" * 62}\nSAPAAN: {LULUS} LULUS / {GAGAL} GAGAL\n{"=" * 62}')
    return 0 if GAGAL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
