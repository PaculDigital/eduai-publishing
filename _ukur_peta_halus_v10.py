"""UKUR v10 — POLA RESMI: JENDELA BARIS BER-ID (baris + tetangganya).

MENGAPA v10 (akar v9, TERUKUR): Wulan kirim FAKTA HITUNGAN (`isi_sesudah`) yang
SALAH saat sub-bab berdempetan ("1.3. Tujuan Penelitian" langsung diikuti baris
pendek → isi dihitung 0) → Jev wajar ragu (p 0,58-0,63).

CARA RESMI (cookbook-structure-recovery): Jev diberi BLOK KEADAAN CUKUP =
baris ber-ID + BARIS KELILINGNYA. Jev menilai dari KEADAAN, bukan dari
hitungan kode yang bisa salah.

JENDELA per kandidat:
    L000618| melalui Relationship Marketing?
  > L000620| 1.3. Tujuan Penelitian          ← yang ditanya
    L000622| 1. Untuk menguji dan menganalisis Pengaruh D

KALIMAT (fakta positif, TANPA larangan):
    "Baris `c_i.tengah` diapit baris lain. Apakah baris tengah ini awal sub-bab?"

UJI: BAB I Tesis 78 · KUNCI = 358(1.1) 606(1.2) 620(1.3) 638(1.4)
"""
import sys, re, time, json
sys.path.insert(0, '/app')

from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR
from app.models import FileBerkas
from app import satpam

PEMBUANG = re.compile(
    r'^\s*(?:\[\[.*?\]\]|Sumber\s*:|DAFTAR\s+(?:PUSTAKA|ISI|TABEL|GAMBAR|LAMPIRAN)'
    r'|LAMPIRAN\b|Lampiran\s+\d|Keterangan\s*:)\s*', re.I)
TITIK_ISI = re.compile(r'\.{4,}|[\u2026]{2,}')
AMBANG = 0.80
KUNCI = {358: '1.1.', 606: '1.2.', 620: '1.3.', 638: '1.4.'}


def teks_naskah(db, fid):
    fb = db.get(FileBerkas, fid)
    p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
    return (_teks_dari_berkas(p, fb.nama or '') or ''), (fb.nama or '')


def pasti_bukan_judul(s):
    if not s.strip():
        return True
    if PEMBUANG.match(s) or TITIK_ISI.search(s):
        return True
    if re.match(r'^Tabel\s+\d|^Gambar\s+\d', s, re.I):
        return True
    if re.fullmatch(r'[\d\.,%\s\-–—]+', s):
        return True
    if re.fullmatch(r'[nN]\s*=\s*[\d\.,\s≈]+', s):
        return True
    return False


def main():
    ids = [int(a) for a in sys.argv[1:]] or [78]
    db = SessionLocal()
    try:
        for fid in ids:
            teks, nama = teks_naskah(db, fid)
            baris = teks.split('\n')
            print('═' * 74)
            print(f'📄 fid={fid} {nama[:46]}')
            print(f'KUNCI BAB I: {KUNCI}')

            # kandidat = baris pendek dalam BAB I (tanpa hitungan isi!)
            kand = []
            for i, b in enumerate(baris):
                if not (354 <= i <= 665):
                    continue
                s = ' '.join(b.split())
                if pasti_bukan_judul(s) or len(s) > 70:
                    continue
                kand.append((i, s))
            print(f'\nKANDIDAT: {len(kand)} baris pendek (TANPA hitungan isi)')

            hasil = {}
            for gel in range(0, len(kand), 8):
                pakai = kand[gel:gel+8]
                paket, tanya = {}, {}
                for n, (i, s) in enumerate(pakai):
                    nm = f'c{n}'
                    # ── JENDELA: 1 baris atas + tengah + 1 baris bawah (ber-ID)
                    atas = i - 1
                    bawah = i + 1
                    ta = f'L{atas:06d}| ' + ' '.join(baris[atas].split())[:80] if atas >= 0 else '(awal naskah)'
                    tb = f'L{bawah:06d}| ' + ' '.join(baris[bawah].split())[:80] if bawah < len(baris) else '(akhir naskah)'
                    paket[nm] = {
                        'baris_atas': ta,
                        'tengah': f'L{i:06d}| {s}',
                        'baris_bawah': tb,
                    }
                    tanya[nm] = {'type': 'noul', 'instructions': (
                        f'Baris `{nm}.tengah` diapit dua baris lain. '
                        f'Apakah baris tengah ini awal sub-bab?')}
                t0 = time.time()
                jw = satpam.tanya_bebas_mutu(
                    json.dumps(paket, ensure_ascii=False)[:60000], tanya) or {}
                dtk = time.time() - t0
                print(f'\nJEV gel.{gel//8+1} ({dtk:.1f} dtk):')
                for n, (i, s) in enumerate(pakai):
                    p = (jw.get(f'c{n}') or {}).get('noul')
                    ok = p is not None and p >= AMBANG
                    hasil[i] = p
                    tanda = ''
                    if i in KUNCI:
                        tanda = ' ✅TEPAT' if ok else ' ❌TERLEWAT'
                    t = '✅' if ok else ('⚠️' if p is not None and p >= 0.5 else '❌')
                    print(f'   {t} L{i:06d} p={None if p is None else round(p,3)}'
                          f' | {s[:42]}{tanda}')

            pilih = {i for i, p in hasil.items() if p is not None and p >= AMBANG}
            print(f'\n   ⇒ Jev pilih: {len(pilih)}')
            print(f'   ⇒ KUNCI ketemu: {len(pilih & set(KUNCI))}/{len(KUNCI)}')
            lewat = set(KUNCI) - pilih
            if lewat:
                print(f'   ⇒ TERLEWAT: {[(i, KUNCI[i]) for i in sorted(lewat)]}')
                for i in sorted(lewat):
                    print(f'      L{i:06d} p={hasil.get(i)}')
    finally:
        db.close()


if __name__ == '__main__':
    main()
