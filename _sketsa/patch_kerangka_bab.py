"""TAHAP 3 — sambungkan kerangka.py ke 5 BAB + mesin TAHAP 3 (potong token)."""
import pathlib

P = pathlib.Path('/opt/data/services/eduai-publishing/app/kerangka.py')
s = P.read_text()

# ── 1. Buang KERANGKA_BAKU lama, pakai app.kerangka_bab ──
awal = s.index('#  ── Kerangka baku per bab (dipakai kalau AI tidak tersedia) ──')
akhir = s.index('def tolak_buat_utuh(')
s = s[:awal] + s[akhir:]

# ── 2. Import kerangka_bab (aman: di dalam fungsi biar tidak melingkar) ──
s = s.replace("""SUBBAB_PER_BAB = 5
POIN_MIN = 3
POIN_MAKS = 5""",
"""SUBBAB_PER_BAB = 5          # pola umum: 5 sub-bab (putusan Bos Q1)
POIN_MIN = 3
POIN_MAKS = 5""")

# ── 3. susun_rencana: pakai kerangka_bab + dukung semua bab ──
lama = """    #  ── 2. KERANGKA BAKU ──
    kerangka = [{'kode': k, 'judul': j, 'poin': p}
                for (k, j, p) in KERANGKA_BAKU.get(bab, [])]"""
baru = """    #  ── 2. KERANGKA BAKU (disesuaikan per bab — arahan Bos 26Sep26) ──
    from . import kerangka_bab as _kb
    _b = _kb.ambil(bab)
    kerangka = [{'kode': k, 'judul': j, 'poin': p}
                for (k, j, p) in (_b.get('sub_bab') or [])]
    nama_bab = _b.get('nama') or ''
    butuh = _b.get('butuh') or {'tabel': [], 'grafik': []}"""
assert lama in s
s = s.replace(lama, baru, 1)

# ── 4. pesan "bab belum didukung" + pakai daftar bab dinamis ──
lama = """    if not kerangka:
        return {
            'ok': False,
            'kode': 'bab_belum_didukung',
            'pesan': (f'Kerangka untuk BAB {bab} belum dibuka. Putusan: mulai '
                      'BAB I dulu, supaya mahasiswa paham alur sebelum lanjut.'),
            'bab_tersedia': list(KERANGKA_BAKU.keys()),
        }"""
baru = """    if not kerangka:
        from . import kerangka_bab as _kb2
        tersedia = [f'BAB {x["bab"]} ({x["nama"]})'
                    for x in _kb2.daftar_bab()]
        return {
            'ok': False,
            'kode': 'bab_belum_didukung',
            'pesan': (f'Kerangka BAB {bab} tidak tersedia. Yang tersedia: '
                      + ', '.join(tersedia) + '.'),
            'bab_tersedia': _kb2.BAB_KERANGKA,
        }"""
assert lama in s
s = s.replace(lama, baru, 1)

# ── 5. tambahkan nama_bab + butuh ke keluaran ──
s = s.replace("""        'kerangka': kerangka,
        'panjang': {'sub_bab': len(kerangka), 'poin_per_sub': f'{POIN_MIN}-{POIN_MAKS}'},""",
"""        'kerangka': kerangka,
        'nama_bab': nama_bab,
        'butuh': butuh,
        'panjang': {'sub_bab': len(kerangka), 'poin_per_sub': f'{POIN_MIN}-{POIN_MAKS}'},""", 1)

# ── 6. TAHAP 3: bangun_isi (kerangka + tabel + grafik + sitasi) ──
TAHAP3 = '''

# ══════════════════════════════════════════════════════════════════════════
#  TAHAP 3 — KERJAKAN (potong Token Revisi DI LUAR fungsi ini, pemanggil
#  yang memotong setelah user menekan [Setuju & Kerjakan] — pagar P1)
# ══════════════════════════════════════════════════════════════════════════
def bangun_isi(judul: str, bab: str = '1', jenis_dok: str = '',
               jenis_penelitian: str = '', tema: str = '',
               naskah: str = '', maks_artikel: int = 20) -> dict:
    """Susun BAHAN kerangka: sitasi + kerangka + rencana tabel & grafik.

    ⚠️ Fungsi ini TIDAK memotong token dan TIDAK menulis .docx.
       Potong token dilakukan API (setelah persetujuan user).
       Penulisan .docx dilakukan jalur presisi (`app/tulis_docx.py`).

    Keluaran dipakai untuk:
      · prompt AI (kalau AI tersedia) → kerangka lebih hidup
      · cadangan: kerangka baku + poin + sitasi siap tulis
    """
    from . import kerangka_bab as _kb

    tema_kerja = (tema or judul or '').strip()
    bab = str(bab or '1')
    _b = _kb.ambil(bab)
    if not _b:
        return {'ok': False, 'kode': 'bab_belum_didukung',
                'pesan': f'BAB {bab} tidak punya kerangka baku.'}

    #  ── 1. SITASI NYATA (audit DOI) ──
    artikel, info = [], {}
    try:
        from . import pustaka as _pustaka
        h = _pustaka.cari_semua(tema_kerja)
        artikel = h.get('artikel') or []
        info = {'per_sumber': h.get('jumlah_per_sumber') or {},
                'total_unik': h.get('total_unik') or 0,
                'terverifikasi': h.get('terverifikasi') or 0}
    except Exception as e:                                    # noqa: BLE001
        log.warning('[kerangka] TAHAP 3 pencarian gagal: %s', e)

    #  ── 2. APA 7 — HANYA yang terverifikasi (pagar P3) ──
    daftar_pustaka = ''
    try:
        from . import pustaka as _p2
        daftar_pustaka = _p2.daftar_pustaka_apa7(artikel)
    except Exception:                                         # noqa: BLE001
        daftar_pustaka = ''

    #  ── 3. RENCANA TABEL & GRAFIK (sesuai bab — arahan Bos) ──
    tabel = [{'judul': t, 'kolom': [], 'baris': []}
             for t in (_b.get('butuh') or {}).get('tabel', [])]
    grafik = [{'judul': g, 'jenis': _jenis_grafik(bab), 'data': []}
              for g in (_b.get('butuh') or {}).get('grafik', [])]

    #  ── 4. SARING artikel yang RELEVAN ke sub-bab (kalau naskah ada) ──
    relevan = _pilih_relevan(artikel, naskah, judul)

    return {
        'ok': True,
        'bab': bab, 'nama_bab': _b.get('nama') or '',
        'judul': judul, 'jenis_dokumen': jenis_dok,
        'jenis_penelitian': jenis_penelitian,
        'kerangka': [{'kode': k, 'judul': j, 'poin': p}
                     for (k, j, p) in (_b.get('sub_bab') or [])],
        'tabel': tabel,
        'grafik': grafik,
        'artikel': artikel[:maks_artikel],
        'artikel_relevan': relevan[:maks_artikel],
        'daftar_pustaka': daftar_pustaka,
        'info_cari': info,
        'pagar': {
            'token_dipotong_di_api': True,
            'sitasi_terverifikasi': info.get('terverifikasi', 0),
            'hanya_terverifikasi_masuk_daftar_pustaka': True,
        },
    }


def _jenis_grafik(bab: str) -> str:
    """Jenis grafik sesuai ciri bab (arahan Bos: 'termasuk grafik & tabel')."""
    return {'2': 'diagram_panah', '4': 'batang'}.get(str(bab), 'batang')


def _pilih_relevan(artikel: list[dict], naskah: str, judul: str) -> list[dict]:
    """Pilih artikel yang paling nyambung dengan NASKAH user (kalau ada).

    Kalau naskah kosong → kembalikan semua (tidak memotong pilihan user).
    """
    if not naskah:
        return list(artikel)
    teks = (naskah or '').lower()
    keluar = []
    for r in artikel:
        kata = [w for w in (r.get('title') or '').lower().split()
                if len(w) > 5]
        kena = sum(1 for w in kata if w in teks)
        if kena:
            keluar.append({**r, 'kena_naskah': kena})
    keluar.sort(key=lambda x: (-(x.get('kena_naskah') or 0),
                               -(x.get('cited_by_count') or 0)))
    return keluar or list(artikel)
'''
s = s.rstrip() + '\n' + TAHAP3
P.write_text(s)
print('✅ kerangka.py: 5 BAB + TAHAP 3 (bangun_isi) + tabel/grafik per bab')
