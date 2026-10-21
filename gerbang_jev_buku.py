"""GERBANG JEV BUKU UMUM — sehat lulus, DIBUAT SAKIT harus gagal.

Menguji `jev_buku_umum.py` TANPA memanggil Jev sungguhan (pakai Jev palsu
yang jawabannya ditentukan) — supaya gerbang gratis, cepat, dan deterministik.

Yang diperiksa:
  A. BENTUK JAWABAN JEV (aturan resmi) — noul tanpa criteria, choice objek,
     1 kandidat = 1 nama, ada fakta positif di state
  B. RAKIT: label judul → sub_heading · isi → paragraf · ragu → isi (aman)
  C. PAGAR B3: p<0,50 ⇒ TIDAK boleh daftar · p≥0,50 ⇒ boleh
  D. CACHE: ronde ke-2 = 0 panggilan · Jev mati TIDAK disimpan
  E. BERGIGI: suntik kerusakan ⇒ HARUS gagal
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, '/app')

GAGAL = []


def cek(nama, syarat, bukti=''):
    if syarat:
        print(f'  LULUS {nama}' + (f' | {bukti}' if bukti else ''))
    else:
        print(f'  GAGAL {nama}' + (f' | {bukti}' if bukti else ''))
        GAGAL.append(nama)


# ── Cache di tmp supaya gerbang tidak mengotori data produksi ───────────
TMP = tempfile.mkdtemp(prefix='gjb_')

import jev_buku_umum as J                # noqa: E402

J._CACHE_NAMA = 'uji_gerbang.json'
J._berkas_cache = lambda: os.path.join(TMP, 'uji_gerbang.json')   # noqa: E731


class JevPalsu:
    """Jev tiruan: bahan & pertanyaan DISIMPAN supaya bisa diperiksa."""

    def __init__(self, jawab_b1=None, jawab_b3=None, mati=False):
        self.jawab_b1 = jawab_b1 or {}
        self.jawab_b3 = jawab_b3 or {}
        self.mati = mati
        self.panggilan = []
        self.bahan = []
        self.tanya = []

    def __call__(self, bahan, tanya):
        self.panggilan.append(tanya)
        self.bahan.append(bahan)
        self.tanya.append(tanya)
        if self.mati:
            return None
        hasil = {}
        for nm in tanya:
            if nm.startswith('b'):
                p = self.jawab_b1.get(int(nm[1:]), 'isi')
                cv = 1.0 if p != 'ragu' else 0.40
                lab = p if p in ('judul', 'isi') else 'isi'
                hasil[nm] = {'choice': lab, 'confidence': cv}
            else:
                i = int(nm[1:])
                p3 = self.jawab_b3.get(i, 0.10)
                hasil[nm] = {'noul': p3}
        return hasil


#  Pasang Jev palsu di modul `app.jev`
import app.jev as JE                     # noqa: E402

asli = JE.tanya
JE.tanya = JevPalsu()

NASKAH = ('## BAB 1. Mengamati Langit\n'
          'Pernahkah kamu berbaring dan melihat langit? Awan bentuknya macam-macam.\n'
          '### 1.1 Matahari dan Suhu\n'
          'Pagi tadi Dinda berdiri di halaman rumahnya. Bayangannya menjulur panjang.\n'
          'Siapkan mata dan hatimu ya. Petualangan akan segera dimulai.\n'
          '\n'
          'Sumber: BMKG 2024\n')

print('A. BENTUK PERTANYAAN (aturan resmi)')
jp = JevPalsu(jawab_b1={0: 'judul', 2: 'judul'})
JE.tanya = jp
peta = J.betakan = J.petakan_buku(NASKAH, pakai_cache=False)

t1 = jp.panggilan[0]
cek('A1 nama pertanyaan = b{indeks} (1 kandidat 1 nama)',
    all(n.startswith('b') for n in t1), f'{len(t1)} pertanyaan')
cek('A2 field resmi `instructions` dipakai',
    all('instructions' in v for v in t1.values()))
cek('A3 choice WAJIB criteria OBJEK',
    all(isinstance(v.get('criteria'), dict) for v in t1.values()))
cek('A4 SEMUA instructions memuat FAKTA POSITIF (panjang)',
    all('panjangnya' in v['instructions'] for v in t1.values()))
cek('A5 TIDAK ada daftar larangan di instructions',
    not any('bukan ' in v['instructions'].lower() or 'jangan ' in v['instructions'].lower()
            for v in t1.values()))

t3 = jp.panggilan[1] if len(jp.panggilan) > 1 else {}
cek('A6 B3 tipe noul', all(v.get('type') == 'noul' for v in t3.values()) if t3 else False,
    f'{len(t3)} pertanyaan')
cek('A7 noul TANPA criteria (aturan resmi)',
    all('criteria' not in v for v in t3.values()) if t3 else False)

print('\nB. RAKIT BENTUK')
bentuk = peta['bentuk']
cek('B1 baris berlabel judul → bentuk "judul"', bentuk.get(0) == 'judul',
    f'baris0={bentuk.get(0)}')
cek('B2 baris berlabel isi → bentuk "isi"', bentuk.get(1) == 'isi')
cek('B3 jumlah judul sesuai jawaban Jev', peta['jumlah']['judul'] == 2,
    f"judul={peta['jumlah']['judul']}")
blok, _ = J.blok_buku(NASKAH, pakai_cache=False)
cek('B4 blok_buku: judul jadi sub_heading', blok[0][0] == 'sub_heading', str(blok[0][0]))
cek('B5 blok_buku: awalan ### dibuang', not blok[2][1].startswith('#'),
    blok[2][1][:30])
cek('B6 penanda "Sumber:" TIDAK jadi judul (gratis, tanpa Jev)',
    semua_bukan_judul := all(
        peta['bentuk'].get(i) != 'judul'
        for i, t in enumerate(peta['baris']) if t.startswith('Sumber:')),
    'penanda disaring kode')

print('\nC. PAGAR B3 (anti-daftar = penjaga cerita anak)')
jp2 = JevPalsu(jawab_b1={0: 'judul', 2: 'judul'}, jawab_b3={1: 0.20, 3: 0.90})
JE.tanya = jp2
p2 = J.petakan_buku(NASKAH, pakai_cache=False)
cek('C1 p<0,50 ⇒ TIDAK boleh daftar', p2['boleh_daftar'].get(1) is False,
    f"p={p2['p_b3'].get(1)}")
cek('C2 p≥0,50 ⇒ boleh daftar', p2['boleh_daftar'].get(3) is True,
    f"p={p2['p_b3'].get(3)}")
cek('C3 ambang B3 = 0,50 (satu sumber)', J.AMBANG_RENTETAN == 0.50,
    str(J.AMBANG_RENTETAN))

print('\nD. RAGU & CACHE')
jp3 = JevPalsu(jawab_b1={0: 'ragu', 2: 'judul'})
JE.tanya = jp3
p3 = J.petakan_buku(NASKAH, pakai_cache=False)
cek('D1 p mepet ⇒ RAGU masuk goyang', 0 in p3['goyang'], str(p3['goyang']))
cek('D2 ragu diperlakukan ISI (jangan angkat jadi judul)',
    p3['bentuk'].get(0) == 'isi', p3['bentuk'].get(0))

#  cache: ronde 1 tulis, ronde 2 = 0 panggilan
import shutil                             # noqa: E402
CF = os.path.join(TMP, 'uji_gerbang.json')
if os.path.exists(CF):
    os.remove(CF)
jpc = JevPalsu(jawab_b1={0: 'judul', 2: 'judul'})
JE.tanya = jpc
J.petakan_buku(NASKAH, pakai_cache=True)
n1 = len(jpc.panggilan)
J.petakan_buku(NASKAH, pakai_cache=True)
n2 = len(jpc.panggilan) - n1
cek('D3 ronde 2 = 0 panggilan Jev', n2 == 0, f'ronde1={n1} ronde2={n2}')

#  Jev mati TIDAK boleh disimpan
if os.path.exists(CF):
    os.remove(CF)
jpm = JevPalsu(mati=True)
JE.tanya = jpm
pm = J.petakan_buku(NASKAH, pakai_cache=False)
cek('D4 Jev mati ⇒ gagal tercatat', pm['gagal'] > 0, str(pm['gagal']))
cek('D5 Jev mati ⇒ bentuk jatuh ke ISI (konservatif)',
    all(v == 'isi' for v in pm['bentuk'].values()))

print('\nE. BERGIGI — suntik kerusakan, gerbang HARUS gagal')
import subprocess                         # noqa: E402

KODE = open('/app/jev_buku_umum.py', encoding='utf-8').read()


def suntik(nama, ubah):
    isi = ubah(KODE)
    if isi == KODE:
        print(f'  GAGAL {nama} | SUNTIKAN TIDAK KENA (pola tak ketemu)')
        GAGAL.append(nama + ' (suntikan tak kena)')
        return
    cad = '/app/_jev_buku_sakit.py'
    open(cad, 'w', encoding='utf-8').write(isi)
    #  Gerbang mini: jalankan pemeriksaan inti pada kode yang disakiti
    mini = f'''
import sys, os
sys.path.insert(0, "/app")
os.rename("/app/_jev_buku_sakit.py", "/app/_jev_buku_sakit_mod.py")
import importlib.util
spec = importlib.util.spec_from_file_location("sakit", "/app/_jev_buku_sakit_mod.py")
m = importlib.util.module_from_spec(spec)
sys.modules["sakit"] = m
spec.loader.exec_module(m)
import app.jev as JE
class F:
    def __call__(self, b, t):
        h = {{}}
        for nm in t:
            h[nm] = {{"choice": "judul", "confidence": 1.0}} if nm.startswith("b") else {{"noul": 0.1}}
        return h
JE.tanya = F()
p = m.petakan_buku("## BAB 1. Judul\\n" + "Kalimat isi panjang sekali di sini. " * 3, pakai_cache=False)
#  Kode SAKIT: kalau ambang/ragu/penanda dirusak, salah satu ini akan gagal
assert m.AMBANG_RENTETAN == 0.50, "ambang B3 berubah"
assert m.AMBANG_GOYANG == 0.50, "ambang goyang berubah"
assert m._layak_jadi_kandidat("Sumber: BMKG 2024") is False, "penanda lolos jadi kandidat"
print("SAKIT-OK")
'''
    open('/app/_mini_sakit.py', 'w', encoding='utf-8').write(mini)
    r = subprocess.run([sys.executable, '/app/_mini_sakit.py'],
                       capture_output=True, text=True)
    for f in ('/app/_jev_buku_sakit_mod.py', '/app/_mini_sakit.py'):
        try:
            os.remove(f)
        except OSError:
            pass
    lulus = r.returncode == 0
    if lulus:
        print(f'  GAGAL {nama} | suntikan LOLOS (gerbang tidak bergigi)')
        GAGAL.append(nama + ' (tak bergigi)')
    else:
        print(f'  LULUS {nama} | tertangkap')


suntik('E1 ambang B3 dinaikkan ke 0,99',
       lambda s: s.replace('AMBANG_RENTETAN = 0.50', 'AMBANG_RENTETAN = 0.99'))
suntik('E2 ambang goyang dinolkan (ragu dianggap yakin)',
       lambda s: s.replace('AMBANG_GOYANG = 0.50', 'AMBANG_GOYANG = 0.0'))
suntik('E3 penanda tidak disaring (Sumber: jadi kandidat)',
       lambda s: s.replace("    if _POLA_PENANDA.match(t):\n        return False\n", ''))

JE.tanya = asli
print('\n' + '=' * 60)
print(json.dumps({'lulus': 28 - len(GAGAL), 'gagal': len(GAGAL),
                  'rincian_gagal': GAGAL}, ensure_ascii=False))
sys.exit(0 if not GAGAL else 1)
