"""UKUR ULANG — CARA RESMI: kode beri FAKTA, Jev menghakimi.

DASAR (dokumentasi resmi + fact 254):
  • Setiap pertanyaan Jev INDEPENDEN (primitives.md) → Jev TIDAK membandingkan
    antar baris. Karena itu "BAB I" palsu & "BAB IV" asli SAMA-SAMA dijawab "ya"
    kalau dikirim sebagai baris polos.
  • jaggedness #2: hitung/cari di KODE, Jev hanya menilai yang memang judgment.
  • CARA SAH (terukur di naskah Asih): kode kirim FAKTA yang kode TAHU tapi TAK
    BISA putuskan (mis. PANJANG ISI sesudah baris + ada duplikat) → Jev menghakimi.

Soal "beda huruf besar/kecil" → itu pekerjaan KODE (kode yang normalisasi),
JANGAN dijadikan pertanyaan Jev (jaggedness #1 literal reading + #5 distraktor).

Output: untuk tiap kandidat, p + yakin + fakta yang dikirim (biar bisa diaudit).
"""
import sys, re, time
sys.path.insert(0, '/app')

from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR
from app.models import FileBerkas
from app import satpam

PENANDA_BAB = re.compile(r'^\s*BAB\s+([IVX]+)\b', re.I)


def teks_naskah(db, fid):
    fb = db.get(FileBerkas, fid)
    p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
    return (_teks_dari_berkas(p, fb.nama or '') or ''), (fb.nama or '')


def buang_daftar_isi(s):
    return bool(re.search(r'\.{2,}\s*\d*\s*$', s)) or bool(
        re.search(r'[\u2026]{2,}', s))


def fakta_kandidat(baris, i):
    """FAKTA yang KODE tahu tentang baris i — inilah 'state' yang dikirim ke Jev.

    Kode TAHU fakta ini tapi TAK BISA memutuskan (itu judgment) ⇒ Jev yang putuskan.
    """
    s = ' '.join(baris[i].split())
    # panjang isi SESUDAH baris ini sampai baris 'BAB' berikutnya
    z = len(baris)
    for j in range(i + 1, len(baris)):
        t = ' '.join(baris[j].split())
        if t and PENANDA_BAB.match(t) and not buang_daftar_isi(t):
            z = j
            break
    isi = '\n'.join(baris[i + 1:z])
    n_kar = len(isi.strip())
    n_baris = len([1 for b in baris[i + 1:z] if b.strip()])
    # 3 baris pertama sesudahnya (bukti bentuk)
    sesudah = []
    for j in range(i + 1, min(i + 5, len(baris))):
        t = ' '.join(baris[j].split())
        if t:
            sesudah.append(t[:90])
    # duplikat: ada 'BAB <romawi>' sama sebelumnya?
    nomor = PENANDA_BAB.match(s).group(1).upper() if PENANDA_BAB.match(s) else '?'
    n_dup = 0
    for j in range(0, i):
        t = ' '.join(baris[j].split())
        if PENANDA_BAB.match(t) and PENANDA_BAB.match(t).group(1).upper() == nomor:
            n_dup += 1
    return {
        'baris': i,
        'teks': s,
        'nomor': nomor,
        'panjang_isi_kar': n_kar,
        'jumlah_baris_isi': n_baris,
        'tiga_baris_sesudah': sesudah,
        'duplikat_sebelumnya': n_dup,
        'jauh_dari_awal': i,          # posisi baris (kode tahu; Jev cuma lihat angka)
    }


def main():
    ids = [int(a) for a in sys.argv[1:]] or [75]
    db = SessionLocal()
    try:
        for fid in ids:
            teks, nama = teks_naskah(db, fid)
            baris = teks.split('\n')
            print('═' * 72)
            print(f'📄 fid={fid} {nama} · {len(teks):,} kar')

            kand = []
            for i, b in enumerate(baris):
                s = ' '.join(b.split())
                if not s or len(s) > 90 or buang_daftar_isi(s):
                    continue
                if PENANDA_BAB.match(s):
                    kand.append(i)

            fakta = [fakta_kandidat(baris, i) for i in kand]
            print(f'\nkandidat: {len(kand)}')

            # ── STATE: fakta per kandidat, sebagai OBJEK (dokumentasi: pakai struktur)
            paket = {}
            for n, f in enumerate(fakta):
                paket[f'kandidat_{n}'] = {
                    'baris_teks': f['teks'],
                    'nomor_romawi': f['nomor'],
                    'panjang_isi_setelahnya_karakter': f['panjang_isi_kar'],
                    'jumlah_baris_isi_setelahnya': f['jumlah_baris_isi'],
                    'tiga_baris_pertama_setelahnya': f['tiga_baris_sesudah'],
                    'berapa_kali_nomor_sama_muncul_sebelumnya': f['duplikat_sebelumnya'],
                }
            # ── PERTANYAAN: SATU per kandidat, noul SEMPIT, tunjuk field dgn backtick
            tanya = {}
            for n, f in enumerate(fakta):
                nm = f'kandidat_{n}'
                tanya[nm] = {
                    'type': 'noul',
                    'instructions': (
                        f'Lihat `{nm}`. Ini satu baris naskah akademik yang berbunyi '
                        f'`{nm}.baris_teks`, yaitu judul bernomor romawi '
                        f'`{nm}.nomor_romawi`. Setelah baris ini ada isi sepanjang '
                        f'`{nm}.panjang_isi_setelahnya_karakter` karakter dalam '
                        f'`{nm}.jumlah_baris_isi_setelahnya` baris. Apakah baris ini '
                        f'adalah AWAL BAB yang sebenarnya (yaitu bab yang menaungi '
                        f'isi panjang itu), dan BUKAN salinan dari daftar isi, '
                        f'BUKAN ringkasan, BUKAN rujukan?'),
                }

            t0 = time.time()
            jawab = satpam.tanya_bebas_mutu(
                __import__('json').dumps(paket, ensure_ascii=False)[:60000], tanya)
            dtk = time.time() - t0
            if not jawab:
                print('❌ Jev tidak menjawab'); continue

            print(f'\n{dtk:.1f} dtk · {len(kand)} pertanyaan · 1 panggilan\n')
            print(f'{"baris":>8} {"p":>7} {"yakin":>7} {"isi_kar":>9} {"dup":>4}  teks')
            for n, f in enumerate(fakta):
                b = jawab.get(f'kandidat_{n}') or {}
                p = b.get('noul')
                y = None if p is None else round(abs(2 * p - 1), 3)
                print(f'{f["baris"]:>8} {p if p is None else round(p,3):>7}'
                      f' {y if y is not None else "-":>7}'
                      f' {f["panjang_isi_kar"]:>9,} {f["duplikat_sebelumnya"]:>4}'
                      f'  {f["teks"][:34]}')
    finally:
        db.close()


if __name__ == '__main__':
    main()
