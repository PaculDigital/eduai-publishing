"""PERBAIKAN: periksa pipa DI DALAM loop (per bagian), bukan atas gabungan.

🔴 AKAR (terbukti 25Sep26):
   `_revisi_kerja` memeriksa pipa SEKALI di luar loop dengan `konten` GABUNGAN
   (baris ~2060). Untuk naskah 2 bagian:
       BAGIAN 1 → editan=1 (revisi nyata)
       BAGIAN 2 → editan=0 ("tidak ada yang perlu diubah")  ← SAH
   Gabungan keduanya → `periksa()` melihat KUTIP-ASLI bagian 1 TIDAK ada di
   awal gabungan... lebih tepatnya: cakupan gabungan tak punya editan utuh →
   `if not editan and not cakupan:` → 503  ← SALAH MENOLAK hasil SAH.

🛠️ PERBAIKAN: periksa pipa per bagian DI DALAM loop (setelah C9).
   - bagian yg TIDAK ada editan & bukan "tanpa perubahan" → bagian itu
     memakai jawaban apa adanya (tetap aman: tidak ada yg ditempelkan).
   - SIMPAN hasil per bagian di `pipa_per_bagian` supaya pemeriksa di luar
     loop bisa memutuskan dgn benar:
        lolos bila ≥1 bagian punya editan ATAU semua bagian "tanpa perubahan"
"""
import ast
import pathlib

SRC = pathlib.Path('app/ai.py')
teks = SRC.read_text()
baris = teks.split('\n')

#  ── 1) Sisipkan pemeriksa pipa PER BAGIAN setelah C9 (`hasil_bagian.append`) ──
i_app = next(i for i, b in enumerate(baris)
             if b.startswith(' ' * 8)
             and b.strip() == 'hasil_bagian.append(konten)')
print(f'hasil_bagian.append → baris {i_app + 1}')

SISIP = [
    '            #  ══ KONTRAK PIPA PER BAGIAN (25Sep26) ══════════════════',
    '            #  Pipa DIPERIKSA DI SINI (per bagian yang benar-benar',
    '            #  dikirim), BUKAN atas gabungan. Alasan (terbukti 2 bagian):',
    '            #     bagian 1 → editan=1 (revisi nyata)',
    '            #     bagian 2 → editan=0 ("tidak ada yang perlu diubah")',
    '            #  Kalau diperiksa atas GABUNGAN, hasil sah 503 ditolak.',
    '            try:',
    '                _pp = _pipa_periksa_bagian(konten, naskah_dikirim)',
    '            except Exception as _epp:                          # noqa: BLE001',
    '                _pp = None',
    '                log.warning("[ai] periksa pipa bagian gagal: %s", _epp)',
    '            if _pp is not None:',
    '                pipa_per_bagian.append((idx, _pp))',
    '                if not _pp.ok:',
    '                    log.error("[ai] PIPA menolak bagian %d/%d: %s",',
    '                              idx, jml_bagian, _pp.pesan[:160])',
    '                    for ip in info_potong:',
    '                        _kembalikan_kuota(db, u, ip)',
    '                    raise HTTPException(503, detail={',
    '                        "ok": False, "pesan": _pp.pesan})',
]
baris[i_app:i_app] = SISIP
print(f'+ {len(SISIP)} baris pemeriksa pipa per bagian')

teks2 = '\n'.join(baris)

#  ── 2) Inisialisasi `pipa_per_bagian` di badan loop (dekat naskah_dikirim) ──
i_nd = next(i for i, b in enumerate(teks2.split('\n'))
            if b.strip() == 'naskah_dikirim = potongan')
b2 = teks2.split('\n')
b2[i_nd + 1:i_nd + 1] = [
    '        pipa_per_bagian = []      # hasil periksa pipa PER BAGIAN',
]
teks2 = '\n'.join(b2)
print('+ inisialisasi pipa_per_bagian')

#  ── 3) Import & alias `_pipa_periksa_bagian` (dekat import lain) ──
ANCHOR = 'from .pipa import periksa as _pipa_periksa'
if ANCHOR in teks2:
    teks2 = teks2.replace(
        ANCHOR,
        ANCHOR + '\n        from .pipa import periksa as _pipa_periksa_bagian',
        1)
    print('+ alias _pipa_periksa_bagian')
else:
    #  belum ada di blok itu → taruh di blok `try` pemeriksa luar
    LAMA = '        from .pipa import periksa as _pipa_periksa\n'
    assert LAMA in teks2, 'import pipa tidak ditemukan'
    teks2 = teks2.replace(
        LAMA,
        LAMA + '        from .pipa import periksa as _pipa_periksa_bagian\n', 1)
    print('+ alias (anchor kedua)')

#  ── 4) Ganti pemeriksa LUAR agar memakai `pipa_per_bagian` ──
LAMA_LUAR = """        if not _cek_pipa.editan and not _cek_pipa.cakupan:"""
BARU_LUAR = """        _ada_editan = any(p.editan for _, p in (pipa_per_bagian or []))
        _semua_tanpa = (bool(pipa_per_bagian)
                        and all(not p.editan and p.cakupan
                                for _, p in pipa_per_bagian))
        if not _ada_editan and not _semua_tanpa and not _cek_pipa.editan \\
                and not _cek_pipa.cakupan:"""
assert LAMA_LUAR in teks2, 'anchor pemeriksa luar tidak ditemukan'
teks2 = teks2.replace(LAMA_LUAR, BARU_LUAR, 1)
print('✅ pemeriksa luar memakai hasil per bagian')

ast.parse(teks2)
print('✅ sintaks OK')
SRC.write_text(teks2)
print(f'💾 {len(teks2.split(chr(10)))} baris')
