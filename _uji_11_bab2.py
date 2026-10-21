"""UJI 11 — BAB II (BELUM PERNAH DITUNING) dengan cara SEKARANG.

Bos: "coba di bab lain yang belum pernah dipakai tuning (misal BAB II ke bawah),
      biar ketahuan apakah perbaikannya general atau cuma hafal potongan ini."

⇒ C = UJI TITIK UKUR DASAR: cara SEKARANG (kode beri ID + JEV 4 pilihan),
   TANPA perbaikan ① (sambung baris) dan TANPA perbaikan ② (definisi tajam).
   Rentang: BAB II (baris 660-800) — bagian yang belum pernah dilihat.

Ukur: 3 putaran → goyang · label · simpulkan general atau hafal.
"""
import sys, json, time, html
sys.path.insert(0, '/app')

from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR
from app.models import FileBerkas
from app import satpam

AWAL, AKHIR = 660, 802     # BAB II baru mulai (belum pernah dituning)
PUTARAN = 3
KRITERIA = {                # CARA SEKARANG (sederhana, tanpa tambalan ②)
    'bab': 'Awal BAB (mis. BAB I, BAB II)',
    'subbab': 'Awal SUB-BAB (mis. 1.1, 2.1.3, atau judul bagian)',
    'paragraf': 'Awal PARAGRAF BARU (kalimat pertama paragraf)',
    'biasa': 'Lanjutan/biasa (bukan awal apa pun)',
}


def main():
    fid = int(sys.argv[1]) if len(sys.argv) > 1 else 78
    db = SessionLocal()
    try:
        fb = db.get(FileBerkas, fid)
        p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
        baris = (_teks_dari_berkas(p, fb.nama or '') or '').split('\n')
        akhir = min(AKHIR, len(baris))
        print('═' * 72)
        print(f'📄 fid={fid} · UJI 11: BAB II {AWAL}-{akhir} — CARA SEKARANG (tanpa tuning)')

        def _t(j):
            return ('L%06d| ' % j) + ' '.join(baris[j].split())[:58] \
                if 0 <= j < len(baris) else '(tepi)'

        kand = [i for i in range(AWAL, akhir) if baris[i].strip()]
        paket, tanya = {}, {}
        for n, i in enumerate(kand):
            nm = f'c{n}'
            paket[nm] = {'sebelum': _t(i - 1), 'tengah': _t(i), 'sesudah': _t(i + 1)}
            tanya[nm] = {'type': 'choice',
                         'instructions': (f'Baris `{nm}.tengah` ada di dalam naskah '
                                          f'akademik. Baris tengah ini perannya apa?'),
                         'criteria': dict(KRITERIA)}
        bahan = json.dumps(paket, ensure_ascii=False)
        print(f'   kandidat {len(kand)} · bahan {len(bahan):,} kar')

        putaran = []
        for k in range(PUTARAN):
            t0 = time.time()
            jw = satpam.tanya_bebas_mutu(bahan[:58000], tanya) or {}
            print(f'   ▶ putaran {k+1}: {time.time()-t0:.1f} dtk '
                  f'({len([v for v in jw.values() if v])}/{len(kand)})')
            putaran.append(jw)
            time.sleep(1.0)

        hasil = {}
        for n, i in enumerate(kand):
            vs = []
            for jw in putaran:
                v = (jw.get(f'c{n}') or {}).get('choice')
                if isinstance(v, dict):
                    v = v.get('id') or v.get('label')
                vs.append(v)
            hasil[i] = vs

        goyang = [(i, v) for i, v in hasil.items() if len(set(v)) > 1]
        print(f'\n   🎯 GOYANG: {len(goyang)} dari {len(hasil)} baris '
              f'({100*len(goyang)/max(1,len(hasil)):.0f}%)')
        for i, v in goyang:
            print(f'      L{i:06d} {v} | {baris[i].strip()[:46]}')

        print(f'\n   🔎 SEMUA baris berlabel bab/subbab/paragraf:')
        for i in sorted(hasil):
            v = hasil[i][0]
            if v in ('bab', 'subbab', 'paragraf'):
                emo = {'bab': '🅱️', 'subbab': '🔷', 'paragraf': '📄'}[v]
                print(f'      {emo} L{i:06d} {v:8s} | {baris[i].strip()[:46]}')

        # sajian berdampingan
        BAR = {'bab': ('🅱️', '#c8e6c9', 'AWAL BAB'),
               'subbab': ('🔷', '#bbdefb', 'AWAL SUB-BAB'),
               'paragraf': ('📄', '#fff9c4', 'AWAL PARAGRAF'),
               'biasa': ('', '', '')}
        kiri, kanan = [], []
        for i in range(AWAL, akhir):
            s = baris[i].strip()
            no = f'L{i:06d}'
            if not s:
                kiri.append(f'<div class="b kosong"><span class="id">{no}</span>(kosong)</div>')
                kanan.append(f'<div class="b kosong"><span class="id">{no}</span>(kosong)</div>')
                continue
            kiri.append(f'<div class="b"><span class="id">{no}</span>'
                        f'<span class="tx">{html.escape(s)}</span></div>')
            vs = hasil.get(i, [None])
            emo, bg, ket = BAR.get(vs[0], ('', '', ''))
            st = f' style="background:{bg}"' if bg else ''
            gy = ' <span class="gy">⚠goyang</span>' if len(set(vs)) > 1 else ''
            kanan.append(f'<div class="b"{st}><span class="id">{no}</span>'
                         f'<span class="tg">{emo} {ket}</span>'
                         f'<span class="tx">{html.escape(s)}</span>{gy}</div>')
        dok = f'''<!doctype html><html lang="id"><head><meta charset="utf-8">
<title>Uji 11 — BAB II cara sekarang</title><style>
body{{font-family:system-ui,sans-serif;margin:14px;color:#222}}
h1{{font-size:18px}} .kotak{{background:#fff3e0;padding:9px;border-radius:8px;font-size:13px;margin-bottom:10px}}
.dua{{display:flex;gap:14px}} .kol{{flex:1;min-width:0;border:1px solid #ddd;border-radius:8px;overflow:hidden}}
.kepala{{background:#37474f;color:#fff;padding:6px 9px;font-size:12.5px;font-weight:600}}
.kepala.k2{{background:#1565c0}}
.b{{display:flex;gap:7px;padding:2px 8px;border-bottom:1px solid #f4f4f4;font-size:12.5px;line-height:1.42}}
.id{{color:#999;font-family:monospace;font-size:10px;flex:0 0 60px;padding-top:2px}}
.tx{{flex:1;word-wrap:break-word}} .tg{{flex:0 0 96px;font-size:10px}}
.kosong{{color:#ccc;font-size:10px}} .gy{{color:#d32f2f;font-size:9.5px;font-weight:700}}
</style></head><body>
<h1>🧪 Uji 11 — BAB II (BELUM PERNAH DITUNING) dengan cara SEKARANG</h1>
<div class="kotak"><b>Titik ukur dasar</b> — tanpa perbaikan ①/②. Kalau banyak salah di sini,
artinya cara lama hanya "hafal" BAB I. Kunjungi: {len(kand)} kandidat ·
{len(goyang)} goyang dari {len(hasil)} baris.</div>
<div class="dua">
<div class="kol"><div class="kepala">📄 NASKAH ASLI</div>{''.join(kiri)}</div>
<div class="kol"><div class="kepala k2">🔎 + TANDA JEV (cara sekarang)</div>{''.join(kanan)}</div>
</div></body></html>'''
        open('/app/SAJI_UJI11_BAB2.html', 'w').write(dok)
        print(f'\n   SAJI: /app/SAJI_UJI11_BAB2.html {len(dok):,} byte')
    finally:
        db.close()


if __name__ == '__main__':
    main()
