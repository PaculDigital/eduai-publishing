"""UJI VERSI FINAL — peta bab: KODE saring & buang duplikat → JEV menghakimi.

PEMBAGIAN TUGAS (dokumentasi resmi + fact 254):
  KODE (yang KODE bisa putuskan sendiri — JANGAN tanya Jev):
    1. saring baris kandidat (pendek + pola 'BAB <romawi>', BUANG daftar isi)
    2. buang DUPLIKAT: nomor romawi dituntut NAIK (I→II→III→IV→V). Nomor yang
       mundur / sama = daftar isi / ringkasan → DIBUANG kode. (kode tahu urutan,
       Jev tidak — setiap pertanyaan Jev independen, tak bisa membandingkan)
    3. normalisasi huruf (BAB/bab) = kode
  JEV (judgment yang kode tak bisa):
    4. apakah baris ini awal bab yang menaungi isi panjang itu?
  KODE:
    5. rakit peta: mulai/akhir/yakin/asal + penanda

Ukur kecocokan vs kunci uji (5 bab asli) + banding peta lama.
"""
import sys, re, time, json
sys.path.insert(0, '/app')

from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR
from app.models import FileBerkas
from app import state, satpam

PENANDA_BAB = re.compile(r'^\s*BAB\s+([IVX]+)\b', re.I)
ANGKA_ROMAWI = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7,
                'VIII': 8, 'IX': 9, 'X': 10, 'XI': 11, 'XII': 12}


def teks_naskah(db, fid):
    fb = db.get(FileBerkas, fid)
    p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
    return (_teks_dari_berkas(p, fb.nama or '') or ''), (fb.nama or '')


def daftar_isi(s):
    return bool(re.search(r'\.{2,}\s*\d*\s*$', s)) or bool(re.search(r'[\u2026]{2,}', s))


def saring_kandidat(baris):
    """KODE langkah 1: baris pendek, pola BAB romawi, bukan daftar isi."""
    keluar = []
    for i, b in enumerate(baris):
        s = ' '.join(b.split())
        if not s or len(s) > 90 or daftar_isi(s):
            continue
        m = PENANDA_BAB.match(s)
        if m and m.group(1).upper() in ANGKA_ROMAWI:
            keluar.append((i, s, ANGKA_ROMAWI[m.group(1).upper()]))
    return keluar


def buang_duplikat_kode(kand):
    """KODE langkah 2: tuntut nomor NAIK. Mundur/sama ⇒ duplikat ⇒ buang.

    Alasan (dokumentasi): tiap pertanyaan Jev INDEPENDEN — Jev tak bisa
    membandingkan baris ke-1 & ke-2. URUTAN = pengetahuan KODE ⇒ putuskan di kode.
    """
    hasil, terakhir = [], 0
    buang = []
    for i, s, nom in kand:
        if nom > terakhir:
            hasil.append((i, s, nom))
            terakhir = nom
        else:
            buang.append((i, s, nom))
    return hasil, buang


def main():
    ids = [int(a) for a in sys.argv[1:]] or [75, 78, 81]
    db = SessionLocal()
    try:
        for fid in ids:
            teks, nama = teks_naskah(db, fid)
            baris = teks.split('\n')
            print('═' * 72)
            print(f'📄 fid={fid} {nama} · {len(teks):,} kar')

            kand = saring_kandidat(baris)
            lolos, dibuang = buang_duplikat_kode(kand)
            print(f'\nKODE: {len(kand)} kandidat → {len(lolos)} lolos, '
                  f'{len(dibuang)} duplikat dibuang')
            for i, s, n in dibuang:
                print(f'   🗑️ buang baris {i:6d} (romawi {n}) | {s[:40]}')

            if not lolos:
                print('   (tidak ada kandidat lolos)'); continue

            # ── JEV: fakta + pertanyaan sempit (1 panggilan)
            paket, tanya = {}, {}
            for n, (i, s, nom) in enumerate(lolos):
                z = len(baris)
                for j in range(i + 1, len(baris)):
                    t = ' '.join(baris[j].split())
                    if t and PENANDA_BAB.match(t) and not daftar_isi(t):
                        z = j
                        break
                isi = '\n'.join(baris[i + 1:z])
                sesudah = [' '.join(baris[j].split())[:90]
                           for j in range(i + 1, min(i + 5, len(baris)))
                           if baris[j].strip()][:3]
                kunci = f'kandidat_{n}'
                paket[kunci] = {
                    'baris_teks': s,
                    'nomor_romawi': nom[0] if False else {v: k for k, v in ANGKA_ROMAWI.items()}[nom],
                    'panjang_isi_setelahnya_karakter': len(isi.strip()),
                    'jumlah_baris_isi_setelahnya': len([1 for b in baris[i+1:z] if b.strip()]),
                    'tiga_baris_pertama_setelahnya': sesudah,
                }
                tanya[kunci] = {'type': 'noul', 'instructions': (
                    f'Lihat `{kunci}`. Baris ini berbunyi `{kunci}.baris_teks` '
                    f'(judul bab bernomor romawi `{kunci}.nomor_romawi`). '
                    f'Setelahnya ada isi `{kunci}.panjang_isi_setelahnya_karakter` '
                    f'karakter dalam `{kunci}.jumlah_baris_isi_setelahnya` baris. '
                    f'Apakah baris ini AWAL BAB sebenarnya yang menaungi isi panjang '
                    f'itu — bukan judul biasa, bukan rujukan, bukan tabel?')}

            t0 = time.time()
            jawab = satpam.tanya_bebas_mutu(
                json.dumps(paket, ensure_ascii=False)[:60000], tanya)
            dtk = time.time() - t0
            if not jawab:
                print('   ❌ Jev tidak menjawab'); continue

            peta = []
            for n, (i, s, nom) in enumerate(lolos):
                b = jawab.get(f'kandidat_{n}') or {}
                p = b.get('noul')
                peta.append({'baris': i, 'teks': s, 'romawi': nom,
                             'p': None if p is None else round(p, 3),
                             'yakin': None if p is None else round(abs(2*p-1), 3)})
            print(f'\nJEV ({dtk:.1f} dtk · 1 panggilan):')
            for f in peta:
                tanda = '✅' if (f['p'] is not None and f['p'] >= 0.6) else '⚠️ '
                print(f"   {tanda} baris {f['baris']:6d} p={f['p']} "
                      f"yakin={f['yakin']} | {f['teks'][:36]}")

            # ── peta lama sebagai pembanding
            pl = state.petakan(state.buang_daftar_isi(teks)) or []
            print(f'\nPETA LAMA: {len(pl)} bagian →', 
                  [str(x.get('section_id','')) for x in pl[:10]])
            print(f'PETA JEV : {len(peta)} bab →',
                  [f"{f['romawi']}@{f['baris']}" for f in peta])
    finally:
        db.close()


if __name__ == '__main__':
    main()
