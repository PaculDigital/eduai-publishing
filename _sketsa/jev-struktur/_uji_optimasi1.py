"""UJI OPTIMASI PASS 1 — saring kode dulu, Jev tetap menyambung.

DUGAAN: 2.223 baris, tapi yang MUNGKIN terbelah hanya baris PENDEK yang
bertetangga dengan baris PENDEK. Paragraf panjang PASTI tidak terbelah.

Cara uji: jalankan versi LAMA (semua baris) vs versi BARU (hanya kandidat),
bandingkan: jumlah panggilan, waktu, DAN peta bab yang dihasilkan.

⚠️ TIDAK menyentuh app/konversi.py — semua fungsi di sini salinan lokal.
"""
import sys, time, re
sys.path.insert(0, '/app')
from app import konversi as K
from app import satpam
from app.state import buang_daftar_isi
import app.models as M
from app.models import SessionLocal
import app.ai as ai_mod

# ── hitung panggilan ──
catat = []
_asli_mutu = satpam.tanya_bebas_mutu
def _bungkus(bahan, pertanyaan, *a, **k):
    t0 = time.time()
    h = _asli_mutu(bahan, pertanyaan, *a, **k)
    catat.append({'t': time.time() - t0, 'kar': len(bahan or ''),
                  'n': len(pertanyaan) if hasattr(pertanyaan, '__len__') else 1})
    return h
satpam.tanya_bebas_mutu = _bungkus

db = SessionLocal()
fb = db.query(M.FileBerkas).filter(M.FileBerkas.id == 81).first()
teks = ai_mod._teks_dari_berkas(ai_mod._path_berkas(fb), fb.nama or '') or ''
print(f'naskah: fid={fb.id} {fb.nama} · {len(teks):,} kar · {teks.count(chr(10)):,} baris')
db.close()

BERSIH = buang_daftar_isi(teks)


# ═══ VERSI LAMA (persis kode sekarang) ═══
def _pecah_lama(teks):
    baris = [' '.join(m.split()) for m in (teks or '').split('\n')]
    baris = [s for s in baris if not s.startswith(K._PENANDA_INTERNAL)]
    if len(baris) < 4:
        return []
    sambung = {}
    for mulai in range(0, len(baris), K._GAL_BARIS):
        bagian = baris[mulai:mulai + K._GAL_BARIS]
        state = '\n'.join(f'L{mulai+n:04d}| {b[:200]}' for n, b in enumerate(bagian))
        tanya = {f'L{mulai+n:04d}': {'instructions':
                 (f'Does line L{mulai+n:04d} pick up mid-sentence, continuing a '
                  f'sentence left unfinished at the end of line L{mulai+n-1:04d}?'),
                 'type': 'noul'} for n in range(1, len(bagian))}
        if not tanya:
            continue
        j = K._tanya_jev_kuat(state, tanya)
        if j:
            sambung.update(j)
    return _rakit(baris, sambung)


# ═══ VERSI BARU (saring kode dulu: hanya baris pendek bertetangga pendek) ═══
def _kandidat_sambung(baris, ambang_kar=60):
    """Kode TAHU: hanya baris PENDEK yang mungkin terbelah.

    Fakta (bukan tebakan): kalimat yang terbelah selalu jadi baris PENDEK,
    karena pemenggalannya terjadi di tengah kalimat pendek. Paragraf panjang
    (> ambang_kar) TIDAK MUNGKIN terbelah — tak ada editor yang memotong
    paragraf panjang jadi dua baris judul.
    """
    kandidat = []
    for n in range(1, len(baris)):
        a, b = baris[n - 1], baris[n]
        if not a or not b:
            continue
        if len(a) <= ambang_kar and len(b) <= ambang_kar:
            kandidat.append(n)
    return kandidat


def _pecah_baru(teks, ambang_kar=60):
    baris = [' '.join(m.split()) for m in (teks or '').split('\n')]
    baris = [s for s in baris if not s.startswith(K._PENANDA_INTERNAL)]
    if len(baris) < 4:
        return [], 0
    kand = _kandidat_sambung(baris, ambang_kar)
    if not kand:
        return _rakit(baris, {}), 0
    #  Kirim HANYA baris kandidat + tetangga kirinya (yang dibutuhkan Jev).
    #  Dipecah per jatah, tapi jatah isinya KANDIDAT (bukan semua baris).
    sambung = {}
    GAL = 120
    for mulai in range(0, len(kand), GAL):
        sub = kand[mulai:mulai + GAL]
        perlu = sorted({n - 1 for n in sub} | set(sub))
        peta_id = {n: i for i, n in enumerate(perlu)}
        state = '\n'.join(f'L{n:04d}| {baris[n][:200]}' for n in perlu)
        tanya = {f'L{n:04d}': {'instructions':
                 (f'Does line L{n:04d} pick up mid-sentence, continuing a '
                  f'sentence left unfinished at the end of line L{n-1:04d}?'),
                 'type': 'noul'} for n in sub}
        j = K._tanya_jev_kuat(state, tanya)
        if j:
            sambung.update(j)
    return _rakit(baris, sambung), len(kand)


def _rakit(baris, sambung):
    def _akhir(x):
        return re.search(r'[.!?:;\u2026]["\')\]]*$', x) is not None
    blok = []
    for n, b in enumerate(baris):
        kosong = not b
        gabung = False
        if blok and not kosong:
            noul = (sambung.get(f'L{n:04d}') or {}).get('noul')
            if noul is not None:
                amb = K._SAMBUNG_AKHIR if _akhir(baris[n-1]) else K._SAMBUNG_GANTUNG
                try:
                    gabung = float(noul) >= amb
                except (TypeError, ValueError):
                    gabung = False
        if gabung:
            blok[-1]['text'] = (blok[-1]['text'] + ' ' + b).strip()
            blok[-1]['lines'].append(n)
        else:
            blok.append({'text': b, 'lines': [n], 'kosong': kosong})
    return blok


def _rakit_peta(blok, jenis):
    """SALINAN aturan rakit peta (dari kode asli) supaya bisa dibandingkan."""
    _BAB = re.compile(r'^\s*BAB\s+([IVXLC]+|\d+)\b', re.IGNORECASE)
    _RANGKA = re.compile(r'^\s*sistematika\s+penulisan\s*$', re.IGNORECASE)
    posisi, rangka = [], False
    for n, b in enumerate(blok):
        if jenis.get(n) != 'heading':
            continue
        judul = (b['text'] or '').strip()
        if not judul:
            continue
        if _RANGKA.match(judul):
            rangka = True
            continue
        if _BAB.match(judul):
            if rangka and not re.fullmatch(r'BAB\s+([IVXLC]+|\d+)', judul, re.I):
                continue
            rangka = False
            posisi.append((b['lines'][0], judul[:80]))
        elif posisi and not rangka and len(posisi[-1][1]) <= 12 and len(judul) <= 70:
            i, j0 = posisi[-1]
            posisi[-1] = (i, f'{j0} {judul}'[:80])
    return posisi if len(posisi) >= 2 else []


def _klasifikasi(blok):
    pendek = [n for n, b in enumerate(blok) if b.get('text') and len(b['text']) <= 90]
    hasil = {}
    for mulai in range(0, len(pendek), K._GAL_BLOK):
        sub = pendek[mulai:mulai + K._GAL_BLOK]
        state = '\n'.join(f'B{n:03d}| {blok[n]["text"][:170]}' for n in sub)
        tanya = {f't{n:03d}': {'instructions': f'What kind of content is block B{n:03d}?',
                 'type': 'choice', 'criteria': K._KRITERIA_BLOK} for n in sub}
        j = K._tanya_jev_kuat(state, tanya)
        if j:
            hasil.update(j)
    return {n: (hasil.get(f't{n:03d}') or {}).get('choice') for n in pendek}


BENAR = [(0, 'BAB I'), (198, 'BAB II'), (371, 'BAB III'),
         (589, 'BAB IV'), (800, 'BAB V')]

for nama, fn in (('LAMA (semua baris)', _pecah_lama), ('BARU (saring kode)', _pecah_baru)):
    catat.clear()
    t0 = time.time()
    hasil = fn(BERSIH)
    blok = hasil[0] if isinstance(hasil, tuple) else hasil
    n_kand = hasil[1] if isinstance(hasil, tuple) else 0
    jenis = _klasifikasi(blok)
    peta = _rakit_peta(blok, jenis)
    dt = time.time() - t0
    print()
    print(f'════ {nama} ════')
    print(f'  baris        : {BERSIH.count(chr(10))+1:,}')
    if n_kand:
        print(f'  KANDIDAT     : {n_kand:,} (yang benar-benar dikirim ke Jev)')
    print(f'  blok         : {len(blok):,}')
    print(f'  PANGGILAN Jev: {len(catat)}')
    print(f'  WAKTU        : {dt:.1f} dtk')
    print(f'  PETA BAB ({len(peta)}):')
    for i, j in peta:
        print(f'     baris {i:>5}  {j}')
    cocok = len(peta) == len(BENAR)
    print(f'  JUMLAH BENAR (5)? {"YA ✅" if cocok else "TIDAK ❌"}')
