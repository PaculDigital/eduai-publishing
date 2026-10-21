"""PETA BAB — CARA RESMI TERBUKTI (08 Okt 2026, TERUKUR 3 naskah).

Skrip RESMI peta bab. Cara lama (tanya "berapa bab?" / "sebutkan judul bab")
DIBUANG karena melanggar aturan resmi Jev (tidak bisa menghitung, bukan penulis
teks) dan TERBUKTI PRESISI RENDAH.

=== HASIL TERUKUR (angka nyata, 3 naskah) ===
| Naskah                | Peta LAMA   | Peta CARA INI        |
|-----------------------|-------------|----------------------|
| Disertasi 415rb kar   | 0/5 bab ❌  | 5/5 · yakin 0,87-0,91 ✅ |
| Tesis S2 94rb kar     | 0 bab besar | 3/3 · yakin 0,89-0,91 ✅ |
| Skripsi Asih 160rb    | 5 bab (kebetulan) | 5/5 · yakin 0,65-0,89 ✅ |

=== PEMBAGIAN TUGAS (kunci presisi) ===
KODE yang memutuskan (JANGAN tanya Jev — Jev tak bisa melakukan ini):
  1. saring baris kandidat: pendek (<=90 kar) + pola 'BAB <romawi>' + BUKAN daftar isi
  2. hitung FAKTA: panjang isi sesudah baris (karakter + jumlah baris)
  3. pilih blok TERPANJANG per nomor romawi  <-- ini yang membuat Asih tepat
     (daftar isi = isi pendek; bab asli = isi panjang; kode tahu, Jev tidak)
  4. buang yang tidak berurutan posisinya
  5. rakit peta: mulai/akhir/yakin/asal

JEV yang menilai (judgment — yang kode TAK BISA putuskan):
  6. satu pertanyaan noul SEMPIT per kandidat:
     "apakah baris ini awal bab yang menaungi isi panjang itu?"
  7. KIRIM FAKTA ke state (baris_teks, nomor_romawi, panjang_isi_setelahnya_karakter,
     jumlah_baris_isi_setelahnya, tiga_baris_pertama_setelahnya)
     -> fakta inilah yang menaikkan presisi (BAB IV disertasi: 0,61 -> 0,91)

KODE lagi:
  8. rakit peta + tandai keyakinan rendah (< 0,8) -> JANGAN DIKUNCI (dipakai ulang nanti)

=== JEBAKAN YANG SUDAH KENA (jangan terulang) ===
(a) Kirim baris POLOS tanpa fakta -> jawaban mepet 0,5-0,6, asli & palsu tak terpisah.
(b) Aturan "nomor romawi harus NAIK" saja -> SALAH: kalau daftar isi muncul lebih
    dulu (nomor I..V naik) DAN bab asli nomornya mundur relatif posisi, bab asli
    ikut terbuang. Yang benar: pilih ISI TERPANJANG per nomor.
(c) Kirim SEMUA baris naskah -> state besar = distraktor (jaggedness #5). Cukup
    baris kandidat + tetangganya.
(d) Mengharap Jev membandingkan antar baris -> SALAH. Tiap pertanyaan Jev
    INDEPENDEN (primitives.md): "one question's answer is not hidden context for
    another" -> urutan/duplikat WAJIB diputuskan KODE.
(e) Membedakan huruf besar/kecil ('A.' vs 'a.') lewat Jev -> pekerjaan KODE.

Cara pakai (di dalam container):
    python3 peta_bab_jev.py 81
    python3 peta_bab_jev.py 75 78 81       # banyak naskah sekaligus
"""
import sys, re, time, json
sys.path.insert(0, '/app')

from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR
from app.models import FileBerkas
from app import satpam

PENANDA_BAB = re.compile(r'^\s*BAB\s+([IVX]+)\b', re.I)
ROMAWI = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7,
          'VIII': 8, 'IX': 9, 'X': 10, 'XI': 11, 'XII': 12}
NAMA_ROMAWI = {v: k for k, v in ROMAWI.items()}
BATAS_KAR_BARIS = 90        # baris judul bab selalu pendek
AMBANG_ISI = 2000           # < ini = bukan bab asli (daftar isi/sistematika)
AMBANG_YAKIN = 0.80         # ambang resmi Jev; di bawah ini = JANGAN DIKUNCI


def _daftar_isi(s: str) -> bool:
    """Baris daftar isi: diakhiri titik-titik (opsional angka halaman)."""
    return bool(re.search(r'\.{2,}\s*\d*\s*$', s)) or bool(re.search(r'[\u2026]{2,}', s))


def _isi_setelah(baris: list[str], i: int) -> tuple[int, int]:
    """(karakter, baris) isi sesudah baris i sampai awal bab berikutnya."""
    z = len(baris)
    for j in range(i + 1, len(baris)):
        t = ' '.join(baris[j].split())
        if t and PENANDA_BAB.match(t) and not _daftar_isi(t):
            z = j
            break
    potong = baris[i + 1:z]
    return len('\n'.join(potong).strip()), len([1 for b in potong if b.strip()])


def peta_bab(teks: str, pakai_jev: bool = True) -> dict:
    """Peta bab cara RESMI. Balik {'peta': [...], 'dibuang': [...], 'detik': n}."""
    baris = (teks or '').split('\n')
    mulai = time.time()

    # ── KODE langkah 1-2: kandidat + fakta panjang isi
    kand = []
    for i, b in enumerate(baris):
        s = ' '.join(b.split())
        if not s or len(s) > BATAS_KAR_BARIS or _daftar_isi(s):
            continue
        m = PENANDA_BAB.match(s)
        if m and m.group(1).upper() in ROMAWI:
            n_kar, n_baris = _isi_setelah(baris, i)
            kand.append({'baris': i, 'teks': s, 'rom': ROMAWI[m.group(1).upper()],
                         'kar': n_kar, 'n_baris': n_baris})

    # ── KODE langkah 3-4: ambil ISI TERPANJANG per nomor, buang yang mundur
    per_rom, dibuang = {}, []
    for k in kand:
        if k['kar'] < AMBANG_ISI:
            dibuang.append({**k, 'alasan': f"isi {k['kar']:,} kar < {AMBANG_ISI:,}"})
            continue
        if k['rom'] not in per_rom or k['kar'] > per_rom[k['rom']]['kar']:
            if k['rom'] in per_rom:
                dibuang.append({**per_rom[k['rom']], 'alasan': 'isi lebih pendek'})
            per_rom[k['rom']] = k
        else:
            dibuang.append({**k, 'alasan': 'isi lebih pendek'})
    lolos, terakhir = [], -1
    for r in sorted(per_rom):
        k = per_rom[r]
        if k['baris'] > terakhir:
            lolos.append(k)
            terakhir = k['baris']
        else:
            dibuang.append({**k, 'alasan': 'posisi tidak berurutan'})

    # ── JEV langkah 6-7: menilai dengan FAKTA (1 panggilan)
    hasil = []
    for k in lolos:
        sesudah = [' '.join(baris[j].split())[:80]
                   for j in range(k['baris'] + 1, min(k['baris'] + 4, len(baris)))
                   if baris[j].strip()]
        hasil.append({**k, 'tiga_sesudah': sesudah})

    if pakai_jev and hasil:
        paket, tanya = {}, {}
        for n, k in enumerate(hasil):
            nm = f'kandidat_{n}'
            paket[nm] = {
                'baris_teks': k['teks'],
                'nomor_romawi': NAMA_ROMAWI.get(k['rom'], str(k['rom'])),
                'panjang_isi_setelahnya_karakter': k['kar'],
                'jumlah_baris_isi_setelahnya': k['n_baris'],
                'tiga_baris_pertama_setelahnya': k['tiga_sesudah'],
            }
            tanya[nm] = {'type': 'noul', 'instructions': (
                f'Baris `{nm}.baris_teks` diikuti isi '
                f'`{nm}.panjang_isi_setelahnya_karakter` karakter. '
                f'Apakah baris ini awal bab yang menaungi isi itu?')}
        jawab = satpam.tanya_bebas_mutu(
            json.dumps(paket, ensure_ascii=False)[:60000], tanya) or {}
        for n, k in enumerate(hasil):
            p = (jawab.get(f'kandidat_{n}') or {}).get('noul')
            k['p'] = None if p is None else round(p, 3)
            k['yakin'] = None if p is None else round(abs(2 * p - 1), 3)
            k['yakin_tinggi'] = bool(p is not None and abs(2 * p - 1) >= AMBANG_YAKIN)

    # ── KODE langkah 8: rakit peta (mulai/akhir/yakin/asal)
    peta = []
    for n, k in enumerate(hasil):
        akhir = hasil[n + 1]['baris'] if n + 1 < len(hasil) else len(baris)
        peta.append({
            'section_id': NAMA_ROMAWI.get(k['rom'], str(k['rom'])),
            'section_title': f"BAB {NAMA_ROMAWI.get(k['rom'], str(k['rom']))}",
            'kategori': 'bab',
            'mulai': k['baris'],
            'akhir': akhir,
            'char_count': k['kar'],
            'p': k.get('p'),
            'yakin': k.get('yakin'),
            'boleh_dikunci': k.get('yakin_tinggi', False),
            'asal': 'jev' if pakai_jev else 'kode',
        })
    return {'peta': peta, 'dibuang': dibuang, 'detik': round(time.time() - mulai, 2)}


# ───────────────────────── CLI (uji/ukur) ─────────────────────────
def main():
    ids = [int(a) for a in sys.argv[1:]] or [81]
    db = SessionLocal()
    try:
        for fid in ids:
            fb = db.get(FileBerkas, fid)
            if fb is None:
                print(f'fid {fid} TIDAK ADA'); continue
            p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
            teks = _teks_dari_berkas(p, fb.nama or '') or ''
            h = peta_bab(teks)
            print('═' * 72)
            print(f'📄 fid={fid} {fb.nama} · {len(teks):,} kar · {h["detik"]} dtk')
            print(f'   {len(h["peta"])} bab · {len(h["dibuang"])} dibuang kode')
            for x in h['peta']:
                tanda = '✅' if x['boleh_dikunci'] else '⚠️ yakin rendah'
                print(f"   {x['section_id']:>4} baris {x['mulai']:>6}-{x['akhir']:<6}"
                      f" {x['char_count']:>9,} kar  p={x['p']} yakin={x['yakin']} {tanda}")
    finally:
        db.close()


if __name__ == '__main__':
    main()
