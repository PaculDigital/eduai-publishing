"""GERBANG MUTU JURNAL (12Okt26) — uji mesin penanda mutu di hasil pencarian.

Menguji SATU pintu: `app/pustaka.py::mutu_jurnal()` + `_label_mutu()`.
Bergigi: tiap asersi memakai data NYATA dari Scopus (bukan palsu).

⚠️ Gerbang ini memanggil Scopus (perlu kunci). Kunci TIDAK ada di container
   secara default → jalankan dengan KUNCI disuntik (lihat cara di bawah).

Cara jalan (dari HOST):
    python3 - <<'PY'
    import json, pathlib, subprocess
    key = json.load(open('/opt/data/home/scopus_api_creds.json'))['api_key']
    p = subprocess.run(['docker','exec','-i','-e','SCOPUS_KEY='+key,'-w','/app',
                        'eduai-app','python3','-'],
                       input=pathlib.Path('_gerbang_mutu_jurnal.py').read_bytes(),
                       capture_output=True)
    print(p.stdout.decode())
    PY
"""
import sys

sys.path.insert(0, '/app')

lulus = gagal = 0
pesan_gagal = []


def cek(nama, syarat, ket=''):
    global lulus, gagal
    if syarat:
        lulus += 1
        print('  ✅ %s' % nama)
    else:
        gagal += 1
        pesan_gagal.append(nama)
        print('  ❌ %s %s' % (nama, ket))


from app.pustaka import _label_mutu, mutu_jurnal  # noqa: E402

print('=== 1. LABEL (ambang putusan Bos: 1,0 / 0,4) ===')
cek('SJR 3.498 → Jurnal Kuat', _label_mutu('3.498') == ('Jurnal Kuat', 'kuat'),
    str(_label_mutu('3.498')))
cek('SJR 1.0 (batas) → Kuat', _label_mutu('1.0') == ('Jurnal Kuat', 'kuat'))
cek('SJR 0.999 → Sedang', _label_mutu('0.999') == ('Jurnal Sedang', 'sedang'))
cek('SJR 0.4 (batas) → Sedang', _label_mutu('0.4') == ('Jurnal Sedang', 'sedang'))
cek('SJR 0.399 → Kecil', _label_mutu('0.399') == ('Jurnal Kecil', 'kecil'))
cek('SJR kosong → tak berlabel', _label_mutu('') == ('', ''))
cek('SJR "abc" → tak berlabel', _label_mutu('abc') == ('', ''))

print()
print('=== 2. AMBIL METRIK NYATA dari Scopus ===')
jbr = mutu_jurnal('0148-2963')          # Journal of Business Research
cek('JBR: data terbaca', bool(jbr), str(jbr)[:90])
if jbr:
    cek('JBR: ada SJR', bool(jbr.get('sjr')), str(jbr.get('sjr')))
    cek('JBR: label Kuat', jbr.get('label') == 'Jurnal Kuat', str(jbr.get('label')))
    cek('JBR: ada CiteScore', bool(jbr.get('cite_score')))
    cek('JBR: ada penerbit', bool(jbr.get('penerbit')), str(jbr.get('penerbit')))

print()
print('=== 3. ISSN KARANGAN — HARUS None (tidak mengarang) ===')
karangan = mutu_jurnal('0128-1234')
cek('ISSN karangan → None', karangan is None, str(karangan))

print()
print('=== 4. ISSN KOSONG — HARUS None (tidak memanggil API) ===')
cek('ISSN kosong → None', mutu_jurnal('') is None)
cek('ISSN None → None', mutu_jurnal(None) is None)

print()
print('=== 5. CACHE — panggilan kedua TIDAK menambah ===')
import app.pustaka as _p                                              # noqa: E402
_p._MUTU_CACHE.clear()
a1 = mutu_jurnal('0148-2963')
n1 = len(_p._MUTU_CACHE)
a2 = mutu_jurnal('0148-2963')
n2 = len(_p._MUTU_CACHE)
cek('cache terisi 1 entri', n1 == 1, 'n1=%s' % n1)
cek('panggilan kedua TIDAK tambah entri', n2 == 1, 'n2=%s' % n2)
cek('hasil panggilan kedua sama', a1 == a2)

print()
print('=== 6. BENTUK HASIL (sesuai yg dipakai layar) ===')
if jbr:
    for k in ('sjr', 'cite_score', 'label', 'kelas', 'penerbit'):
        cek('hasil punya kunci %r' % k, k in jbr, str(list(jbr.keys())))

print()
print('=' * 66)
print('GERBANG MUTU JURNAL: %s LULUS / %s GAGAL' % (lulus, gagal))
if pesan_gagal:
    print('GAGAL:', pesan_gagal)
print('=' * 66)
sys.exit(1 if gagal else 0)
