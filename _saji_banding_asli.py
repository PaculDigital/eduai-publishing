"""SAJI 2 — BANDING BERDAMPINGAN: naskah ASLI vs yang bertanda JEV.

Bos: "Saya butuh aslinya buat bisa bandingkan"

⇒ DUA KOLOM:
   KIRI  = NASKAH ASLI (tanpa tanda apa pun, apa adanya)
   KANAN = NASKAH + tanda Jev

Nomor baris sama di kedua kolom → bisa dibandingkan baris per baris.
"""
import sys, json, time, html
sys.path.insert(0, '/app')

from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR
from app.models import FileBerkas
from app import satpam

RENTANG = (354, 665)


def main():
    fid = int(sys.argv[1]) if len(sys.argv) > 1 else 78
    db = SessionLocal()
    try:
        fb = db.get(FileBerkas, fid)
        p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
        teks = _teks_dari_berkas(p, fb.nama or '') or ''
        baris = teks.split('\n')
        awal, akhir = RENTANG
        akhir = min(akhir, len(baris))

        def _b(j):
            if j < 0 or j >= len(baris):
                return '(tepi)'
            return f'L{j:06d}| ' + ' '.join(baris[j].split())[:60]

        kand = [i for i in range(awal, akhir) if baris[i].strip()]
        paket, tanya = {}, {}
        for n, i in enumerate(kand):
            nm = f'c{n}'
            paket[nm] = {'sebelum': _b(i - 1), 'tengah': _b(i), 'sesudah': _b(i + 1)}
            tanya[nm] = {
                'type': 'choice',
                'instructions': (f'Baris `{nm}.tengah` ada di dalam naskah akademik. '
                                 f'Baris tengah ini perannya apa?'),
                'criteria': {
                    'bab': 'Awal BAB (mis. BAB I, BAB II)',
                    'subbab': 'Awal SUB-BAB (mis. 1.1, 2.1.3, atau judul bagian)',
                    'paragraf': 'Awal PARAGRAF BARU (kalimat pertama paragraf)',
                    'biasa': 'Lanjutan/biasa (bukan awal apa pun)',
                },
            }
        dtk = 0.0
        hasil = {}
        t0 = time.time()
        try:
            jw = satpam.tanya_bebas_mutu(json.dumps(paket, ensure_ascii=False)[:58000], tanya) or {}
            dtk = time.time() - t0
            for n, i in enumerate(kand):
                v = (jw.get(f'c{n}') or {}).get('choice')
                if isinstance(v, dict):
                    v = v.get('id') or v.get('label')
                hasil[i] = v
        except Exception as e:                                  # noqa: BLE001
            print(f'❌ GAGAL panggil Jev: {type(e).__name__}: {e}')

        BAR = {'bab': ('🅱️', '#c8e6c9', 'AWAL BAB'),
               'subbab': ('🔷', '#bbdefb', 'AWAL SUB-BAB'),
               'paragraf': ('📄', '#fff9c4', 'AWAL PARAGRAF'),
               'biasa': ('', '', '')}

        kiri, kanan = [], []
        for i in range(awal, akhir):
            s = baris[i].strip()
            no = f'L{i:06d}'
            if not s:
                kiri.append(f'<div class="b kosong"><span class="id">{no}</span>'
                            f'<span class="tx">(baris kosong)</span></div>')
                kanan.append(f'<div class="b kosong"><span class="id">{no}</span>'
                             f'<span class="tx">(baris kosong)</span></div>')
                continue
            kiri.append(f'<div class="b"><span class="id">{no}</span>'
                        f'<span class="tx">{html.escape(s)}</span></div>')
            v = hasil.get(i)
            emo, bg, ket = BAR.get(v, ('', '', ''))
            st = f' style="background:{bg}"' if bg else ''
            kanan.append(f'<div class="b"{st}><span class="id">{no}</span>'
                         f'<span class="tg">{emo} {ket}</span>'
                         f'<span class="tx">{html.escape(s)}</span></div>')

        n_par = sum(1 for v in hasil.values() if v == 'paragraf')
        n_sub = sum(1 for v in hasil.values() if v == 'subbab')
        n_bab = sum(1 for v in hasil.values() if v == 'bab')

        doc = f'''<!doctype html><html lang="id"><head><meta charset="utf-8">
<title>Banding: Asli vs Bertanda Jev</title>
<style>
body{{font-family:system-ui,sans-serif;margin:16px;color:#222}}
h1{{font-size:19px}} .kotak{{background:#eef6ee;padding:10px;border-radius:8px;font-size:13px;margin-bottom:12px}}
.dua{{display:flex;gap:16px}}
.kol{{flex:1;min-width:0;border:1px solid #ddd;border-radius:8px;overflow:hidden}}
.kepala{{background:#37474f;color:#fff;padding:7px 10px;font-size:13px;font-weight:600;position:sticky;top:0}}
.kepala.k2{{background:#1565c0}}
.b{{display:flex;gap:8px;padding:2px 8px;border-bottom:1px solid #f4f4f4;font-size:12.5px;line-height:1.45}}
.id{{color:#999;font-family:monospace;font-size:10px;flex:0 0 62px;padding-top:2px}}
.tx{{flex:1;word-wrap:break-word}}
.tg{{flex:0 0 100px;font-size:10px;color:#444}}
.kosong{{color:#ccc;font-size:10.5px}}
.ket{{border-collapse:collapse;font-size:12.5px;margin:8px 0}}
.ket th,.ket td{{border:1px solid #ddd;padding:3px 8px}}
</style></head><body>
<h1>⚖️ Banding BERDAMPINGAN — Naskah ASLI vs Bertanda Jev (BAB I Tesis 78)</h1>
<div class="kotak">
KIRI = <b>naskah asli</b> (tanpa tanda, apa adanya) · KANAN = <b>+ tanda Jev</b> ·
nomor baris <code>L######</code> sama di kedua kolom.<br>
1 panggilan Jev · {dtk:.1f} detik · {n_bab} awal BAB · {n_sub} awal SUB-BAB ·
{n_par} awal PARAGRAF.
</div>
<table class="ket"><tr><th>Tanda</th><th>Arti</th></tr>
<tr><td>🅱️ hijau</td><td>Jev: awal BAB</td></tr>
<tr><td>🔷 biru</td><td>Jev: awal SUB-BAB</td></tr>
<tr><td>📄 kuning</td><td>Jev: awal PARAGRAF BARU</td></tr>
<tr><td>putih</td><td>Jev: lanjutan/biasa</td></tr></table>
<div class="dua">
  <div class="kol"><div class="kepala">📄 NASKAH ASLI (tanpa tanda)</div>{''.join(kiri)}</div>
  <div class="kol"><div class="kepala k2">🔎 NASKAH + TANDA JEV</div>{''.join(kanan)}</div>
</div>
</body></html>'''
        open('/app/SAJI_BANDING_ASLI_JEV.html', 'w').write(doc)
        print(f'SAJI: /app/SAJI_BANDING_ASLI_JEV.html {len(doc):,} byte · {dtk:.1f} dtk')
    finally:
        db.close()


if __name__ == '__main__':
    main()
