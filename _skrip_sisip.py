"""Tulis fungsi _posisi_dari_jev ke konversi.py."""
import re

p = 'app/konversi.py'
s = open(p, encoding='utf-8').read()

FUNGSI = '''

#  PERTANYAAN ke Jev: KENALI bentuk naskah → balik daftar bab.
#  ⚠️ Skema Jev WAJIB: `choice` → criteria OBJEK; `noul` tanpa criteria.
_PERTANYAAN_KENALI = {
    'ada_bab': {
        'instructions': ('Apakah naskah ini punya bab akademik bernomor '
                         '(BAB I, BAB II, … atau Bab 1, Bab 2, …)? Abaikan '
                         'daftar isi dan blok "Sistematika Penulisan".'),
        'type': 'noul',
    },
    'jumlah_bab': {
        'instructions': ('Ada berapa bab akademik yang BENAR-BENAR berisi '
                         'di naskah ini? Jangan hitung daftar isi, daftar '
                         'tabel/gambar, halaman judul, abstrak, atau blok '
                         '"Sistematika Penulisan" yang hanya 1 paragraf '
                         'per bab.'),
        'type': 'choice',
        'criteria': {'0': 'tidak ada', '1': 'satu', '2': 'dua', '3': 'tiga',
                     '4': 'empat', '5': 'lima', '6': 'enam', '7': 'tujuh',
                     '8': 'lebih dari tujuh'},
    },
    'judul_bab': {
        'instructions': ('Sebutkan judul tiap bab yang berisi, dipisah tanda '
                         'titik-koma. Contoh bentuk: "BAB I; BAB II; BAB III". '
                         'Hanya bab yang berisi, bukan daftar isi.'),
        'type': 'noul',
    },
}


def _posisi_dari_jev(teks: str) -> list:
    """Minta JEV mengenali bentuk naskah → balik [(idx_baris, nama_bab)].

    PRINSIP INDUK BOS: "Jev selalu terdepan sebelum mesin dan Ai". Mesin TIDAK
    menebak bentuk naskah — Jev yang mengenali, mesin memotong ikut peta Jev.

    Cara kerja: Jev memberi JUMLAH bab + JUDUL tiap bab (teks). Mesin lalu
    mencari judul itu di naskah (pencocokan HARFIAH, bukan tebakan pola) →
    dapat posisi baris. Kalau Jev mati/ragu → balik [] (pemanggil pakai
    cadangan mesin; Jev TIDAK PERNAH jadi penghalang).
    """
    try:
        from . import satpam
    except Exception:                                          # noqa: BLE001
        return []
    if not getattr(satpam, 'AKTIF', False) or not teks:
        return []

    #  Bahan: potongan awal naskah (cukup untuk mengenali daftar isi & bab).
    bahan = teks[:20000] if len(teks) > 20000 else teks
    try:
        jawab = satpam.tanya_bebas(bahan, [], _PERTANYAAN_KENALI)
    except Exception as e:                                     # noqa: BLE001
        log.warning('[konversi] Jev kenali bentuk gagal: %s', e)
        return []
    if not jawab:
        return []

    ada = (jawab.get('ada_bab') or {}).get('noul')
    jml_choice = (jawab.get('jumlah_bab') or {}).get('choice')
    try:
        jml = int(jml_choice) if str(jml_choice).isdigit() else 0
    except (TypeError, ValueError):
        jml = 0
    judul_tev = (jawab.get('judul_bab') or {}).get('text') or ''
    if ada is not None and float(ada) < 0.5:
        return []
    if jml < 2:
        return []

    #  ── MESIN memotong ikut peta Jev: cari judul bab HARFIAH di naskah ──
    import re
    baris = teks.split('\\n')
    #  Kandidat judul: dari Jev ('BAB I; BAB II; …') ATAU pola romawi (cadangan).
    kandidat = [s.strip() for s in re.split(r'[;\\n]', judul_tev) if s.strip()]
    posisi = []
    for i, b in enumerate(baris):
        bersih = b.strip()
        if not bersih or len(bersih) > 120:
            continue
        for k in kandidat:
            if bersih.upper().startswith(k.upper()[:12]):
                posisi.append((i, bersih[:80]))
                break
        else:
            continue
        if len(posisi) >= jml:
            break
    return posisi
'''

#  Sisipkan SEBELUM def _potong_per_bagian
anchor = '\ndef _potong_per_bagian(teks: str) -> str:'
assert anchor in s, 'anchor _potong_per_bagian tidak ketemu'
s = s.replace(anchor, FUNGSI + anchor, 1)
open(p, 'w', encoding='utf-8').write(s)
print('OK: _posisi_dari_jev + _PERTANYAAN_KENALI disisipkan')
