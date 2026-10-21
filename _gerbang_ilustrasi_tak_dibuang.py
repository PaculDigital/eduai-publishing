"""GERBANG ILUSTRASI TIDAK DIBUANG — 19 Okt 2026. Rp 0 (AI dipalsukan).

🔴 CACAT YANG DITUTUP (TERUKUR di buku nyata 2 bab):
  Bab 1 DILEWATI tanpa ilustrasi karena `brief_visual()` menyerah setelah 3
  percobaan QC. Bab 2 berhasil. Buku yang dijual kehilangan gambar di satu bab
  padahal brief yang ditolak biasanya cuma kurang satu kata kunci.

YANG DIUJI:
  [1] QC selalu gagal → brief CADANGAN tetap dipakai (dulu: kosong)
  [2] prompt_dari_bab() mengembalikan prompt (dulu galat)
  [3] Penanda `cadangan_dipakai` jujur = True
  [4] Brief melanggar BUDAYA → TETAP dibuang (pagar tidak boleh jebol)
  [5] Brief terlalu pendek → TETAP dibuang
  [6] QC lolos → perilaku lama tidak berubah (pakai brief itu, tanpa cadangan)
  [7] Bukti cacat lama: tanpa cadangan, hasilnya kosong

PAKAI: cd /opt/data && /opt/data/.venv/bin/python _gerbang_ilustrasi_tak_dibuang.py
"""
import sys

sys.path.insert(0, '/opt/data')

LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama}   {bukti}')


#  Brief yang (menurut QC) kurang HUBUNGAN, tapi isinya benda nyata & wajar.
BRIEF_KURANG_HUBUNGAN = (
    'Deretan ember kosong tersusun di halaman belakang rumah, langit kelabu '
    'menggantung di atasnya, tanah tampak kering dan retak memanjang.')

#  Brief melanggar budaya — TIDAK boleh dipakai walau apa pun.
BRIEF_TERLARANG = (
    'Susunan botol alkohol dan gelas anggur di atas meja kayu panjang, '
    'tampak seperti pesta yang berlangsung sampai malam hari.')


def llm_tetap(teks_selalu):
    """AI palsu: selalu mengembalikan teks yang sama."""
    def panggil(prompt, **kw):
        return teks_selalu
    return panggil


def main():
    import brief_visual as BV

    print('[1] QC SELALU GAGAL → BRIEF CADANGAN TETAP DIPAKAI')
    b = BV.brief_visual('Ringkasan bab tentang kekeringan dan hujan.',
                        panggil_llm=llm_tetap(BRIEF_KURANG_HUBUNGAN),
                        max_percobaan=3)
    cek('brief TIDAK kosong (dulu kosong)', bool(b['brief']), str(b)[:150])
    cek('brief = brief terbaik yang tersimpan',
        b['brief'].strip() == BRIEF_KURANG_HUBUNGAN.strip(), b['brief'][:80])

    print('\n[2] prompt_dari_bab() TETAP MENGHASILKAN PROMPT')
    h = BV.prompt_dari_bab(1, 'Ringkasan bab tentang kekeringan dan hujan.',
                           panggil_llm=llm_tetap(BRIEF_KURANG_HUBUNGAN))
    cek('prompt TIDAK kosong (dulu galat)', bool(h['prompt']), str(h['galat'])[:120])
    cek('galat = None', h['galat'] is None, str(h['galat'])[:80])

    print('\n[3] PENANDA JUJUR')
    cek('cadangan_dipakai = True', b.get('cadangan_dipakai') is True, str(b.get('cadangan_dipakai')))
    cek('generik = True (jujur tidak lolos QC)', b.get('generik') is True,
        str(b.get('generik')))

    print('\n[4] BRIEF MELANGGAR BUDAYA → TETAP DIBUANG')
    b2 = BV.brief_visual('Ringkasan bab tentang pesta dan perayaan.',
                         panggil_llm=llm_tetap(BRIEF_TERLARANG),
                         max_percobaan=2)
    cek('brief budaya TIDAK dipakai', b2['brief'] == '', b2['brief'][:80])
    cek('cadangan_dipakai = False', b2.get('cadangan_dipakai') is False,
        str(b2.get('cadangan_dipakai')))

    print('\n[5] BRIEF TERLALU PENDEK → TETAP DIBUANG')
    b3 = BV.brief_visual('Ringkasan bab apa saja.',
                         panggil_llm=llm_tetap('awan hujan air'),
                         max_percobaan=2)
    cek('brief pendek TIDAK dipakai', b3['brief'] == '', b3['brief'][:60])

    print('\n[6] QC LOLOS → PERILAKU LAMA TIDAK BERUBAH')
    bagus = ('A single rain cloud hanging above a row of empty buckets, water '
             'flowing from the cloud into the buckets, one bucket overflowing.')
    #  ⚠️ JEBAKAN UJI (19 Okt): `brief_visual()` punya DUA lapis QC —
    #     lapis 1 kata kunci, lapis 2 `apa_brief_khas()` yang MEMANGGIL AI
    #     untuk menilai "khas bab ini?". Kalau AI palsu selalu menjawab teks
    #     yang sama, lapis 2 menjawab "tidak berbentuk" ⇒ ditolak, dan uji
    #     salah menyimpulkan brief bagus ikut jadi cadangan.
    #  ⇒ AI palsu harus menjawab "YA" untuk pertanyaan lapis 2.
    def llm_pintar(prompt, **kw):
        #  Bentuk jawaban yang dibaca `_baca_vonis_khas()`: `KHAS: YA`
        #  (bukan sekadar "YA" — itu dianggap TIDAK, "ragu = TIDAK").
        #  Ciri dari prompt ASLI lapis 2: "Kamu pemeriksa kualitas ilustrasi buku"
        if 'pemeriksa kualitas' in prompt.lower():
            return 'KHAS: YA\nSEBAB: memuat awan, ember, dan air yang mengalir'
        return bagus

    b4 = BV.brief_visual('Ringkasan bab tentang siklus air dan hujan.',
                         panggil_llm=llm_pintar, max_percobaan=3,
                         mode='konseptual')
    cek('brief bagus dipakai apa adanya', b4['brief'].strip() == bagus.strip(),
        b4['brief'][:80])
    cek('cadangan_dipakai = False (bukan cadangan)',
        b4.get('cadangan_dipakai') is False, str(b4.get('cadangan_dipakai')))

    print('\n[7] BUKTI CACAT LAMA (tanpa cadangan → kosong)')
    #  Simulasi perilaku LAMA: paksa kandidat tidak tersimpan.
    asli = BV.apa_brief_terlarang_budaya
    BV.apa_brief_terlarang_budaya = lambda t: (True, ['paksa'])
    try:
        b5 = BV.brief_visual('Ringkasan bab tentang kekeringan dan hujan.',
                             panggil_llm=llm_tetap(BRIEF_KURANG_HUBUNGAN),
                             max_percobaan=2)
        cek('tanpa cadangan hasilnya KOSONG (cacat lama terbukti)',
            b5['brief'] == '', b5['brief'][:60])
    finally:
        BV.apa_brief_terlarang_budaya = asli

    print(f'\n{"=" * 64}\nILUSTRASI TIDAK DIBUANG: {LULUS} LULUS / {GAGAL} GAGAL\n{"=" * 64}')
    return 0 if GAGAL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
