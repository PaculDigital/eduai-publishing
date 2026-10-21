"""SAJIAN UJI 21 — dua kolom (asli vs bertanda) dari HASIL yang sudah tersimpan.
Tidak memanggil Jev lagi — hanya menyusun tampilan. Aman & cepat.
"""
import sys, json, re, html
sys.path.insert(0, '/app')
from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR
from app.models import FileBerkas

FID = int(sys.argv[1]) if len(sys.argv) > 1 else 81
AWAL = int(sys.argv[2]) if len(sys.argv) > 2 else 280
AKHIR = int(sys.argv[3]) if len(sys.argv) > 3 else 420
JDL = sys.argv[4] if len(sys.argv) > 4 else 'ASIH'
SOROT = [int(x) for x in sys.argv[5:]] if len(sys.argv) > 5 else []

db = SessionLocal()
fb = db.get(FileBerkas, FID)
p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
baris = (_teks_dari_berkas(p, fb.nama or '') or '').split('\n')
AKHIR = min(AKHIR, len(baris))

# ── ④ gabung judul bab (kode) · ⑤ caption pendek (kode) ──
POLA_CAPTION = re.compile(r'^(tabel|gambar|grafik|diagram|bagan|skema)\s*\.?\s*\d', re.I)
POLA_SUMBER = re.compile(r'^(sumber|source)\s*[:.]', re.I)
POLA_MARKER = re.compile(r'^\[\[.*\]\]$')
POLA_BAB = re.compile(r'^BAB\s+([IVX]+)\s*$', re.I)
_PEMBUANG = re.compile(
    r'^\s*(?:\[\[.*?\]\]|Sumber\s*:|Keterangan\s*:'
    r'|DAFTAR\s+(?:PUSTAKA|ISI|TABEL|GAMBAR|LAMPIRAN)'
    r'|LAMPIRAN\b|Lampiran\s+\d)\s*', re.I)
_TITIK_ISI = re.compile(r'\.{4,}|[\u2026]{2,}')
AMBANG = 70


def dibuang(s):
    if _PEMBUANG.match(s) or _TITIK_ISI.search(s) or POLA_MARKER.match(s):
        return True
    if POLA_SUMBER.match(s):
        return True
    if POLA_CAPTION.match(s) and len(s) <= AMBANG:
        return True
    return False


gabung, buang = {}, []
i = AWAL
while i < AKHIR:
    s = baris[i].strip()
    if not s:
        i += 1
        continue
    if dibuang(s):
        buang.append(i)
        i += 1
        continue
    m = POLA_BAB.match(s)
    if m:
        j = i + 1
        while j < AKHIR and not baris[j].strip():
            j += 1
        if j < AKHIR:
            s2 = baris[j].strip()
            if s2 and s2 == s2.upper() and len(s2) > 4 and not dibuang(s2):
                gabung[i] = (s, s2)
                i = j + 1
                continue
    i += 1

kiri, kanan = [], []
for i in range(AWAL, AKHIR):
    s = baris[i].strip()
    no = 'L%06d' % i
    if not s:
        kiri.append('<div class="b kosong"><span class="id">%s</span>(kosong)</div>' % no)
        kanan.append('<div class="b kosong"><span class="id">%s</span>(kosong)</div>' % no)
        continue
    kiri.append('<div class="b"><span class="id">%s</span><span class="tx">%s</span></div>' % (no, html.escape(s)))
    if i in gabung:
        kanan.append('<div class="b gab" style="background:#c8e6c9"><span class="id">%s</span>'
                     '<span class="tg">AWAL BAB</span><span class="tx">%s</span></div>'
                     % (no, html.escape(gabung[i][0] + ' ' + gabung[i][1])))
        continue
    if i in buang:
        kanan.append('<div class="b buang"><span class="id">%s</span>'
                     '<span class="tg">DIBUANG</span><span class="tx">%s</span></div>' % (no, html.escape(s)))
        continue
    sr = ' sorot' if i in SOROT else ''
    kanan.append('<div class="b%s"><span class="id">%s</span><span class="tx">%s</span></div>' % (sr, no, html.escape(s)))

dok = ('<!doctype html><html lang="id"><head><meta charset="utf-8">'
       '<title>Uji 21 - %s</title><style>'
       'body{font-family:system-ui,sans-serif;margin:14px;color:#222}'
       'h1{font-size:17px}.kotak{background:#e8f5e9;padding:9px;border-radius:8px;font-size:13px;margin-bottom:10px}'
       '.dua{display:flex;gap:12px}.kol{flex:1;min-width:0;border:1px solid #ddd;border-radius:8px;overflow:hidden}'
       '.kepala{background:#37474f;color:#fff;padding:6px 9px;font-size:12px;font-weight:600}'
       '.kepala.k2{background:#2e7d32}'
       '.b{display:flex;gap:6px;padding:2px 7px;border-bottom:1px solid #f4f4f4;font-size:12px;line-height:1.4}'
       '.b.sorot{outline:2px solid #e91e63;outline-offset:-2px}'
       '.b.buang{opacity:.45}.b.gab{font-weight:600}'
       '.id{color:#999;font-family:monospace;font-size:9.5px;flex:0 0 58px;padding-top:2px}'
       '.tx{flex:1;word-wrap:break-word}.tg{flex:0 0 80px;font-size:9.5px}'
       '.kosong{color:#ccc;font-size:9.5px}'
       '</style></head><body>'
       '<h1>Uji 21 - %s - hasil KODE (2 PR)</h1>'
       '<div class="kotak"><b>HANYA hasil saringan KODE</b> (bukan label Jev): judul bab digabung, '
       'caption pendek dibuang. Kotak MERAH = baris Bos sorot. '
       'Goyang TIDAK diklaim di sini - lihat angka di chat.</div>'
       '<div class="dua">'
       '<div class="kol"><div class="kepala">NASKAH ASLI</div>%s</div>'
       '<div class="kol"><div class="kepala k2">HASIL KODE (2 PR)</div>%s</div>'
       '</div></body></html>') % (JDL, JDL, ''.join(kiri), ''.join(kanan))

open('/app/SAJI_KODE_%s.html' % JDL, 'w').write(dok)
print('SAJI: /app/SAJI_KODE_%s.html (%d byte)' % (JDL, len(dok)))
print('gabung:', list(gabung.values()))
print('dibuang:', len(buang))
db.close()
