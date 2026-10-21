"""UJI 20 — ROLLBACK ke cara uji 12 (JENDELA APA-ADANYA) + verifikasi balik.

Saran Bos (A): rollback ke cara uji 12 → verifikasi balik ke 90% → baru pasang
               aturan baru SATU PER SATU, tiap satu diuji ulang.

PELAJARAN UJI 19 (AMBRUK): Wulan salah — kirim "tetangga BERSIH" (baris kosong
dibuang). Padahal BARIS KOSONG = INFORMASI penting untuk Jev:
   "BAB I" diapit baris kosong  ⇒ Jev tahu ini JUDUL BERDIRI SENDIRI ⇒ 🅱️ benar
   "BAB I" nempel baris lain    ⇒ Jev bingung ⇒ salah

⇒ JENDELA = baris j-1, j, j+1 APA ADANYA (termasuk kosong). JANGAN diubah.
⇒ Saringan (①④⑤) HANYA untuk MEMBUANG KANDIDAT, bukan mengubah jendela.

Uji: Asih (280-420) + Tesis 78 BAB I (354-665), 3 putaran.
"""
import sys, json, time, re, html
sys.path.insert(0, '/app')

from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR
from app.models import FileBerkas
from app import satpam

PUTARAN = 3
KRITERIA = {
    'bab': 'Awal BAB (mis. BAB I, BAB II)',
    'subbab': 'Awal SUB-BAB (mis. 1.1, 2.1.3, atau judul bagian)',
    'paragraf': 'Awal PARAGRAF BARU (kalimat pertama paragraf)',
    'biasa': 'Lanjutan/biasa (bukan awal apa pun)',
}
# ── saringan PEMBUANG KANDIDAT (jendela TIDAK diubah) ──
POLA_CAPTION = re.compile(r'^(tabel|gambar|grafik|diagram|bagan|skema)\s*\.?\s*\d', re.I)
POLA_SUMBER = re.compile(r'^(sumber|source)\s*[:.]', re.I)
POLA_MARKER = re.compile(r'^\[\[.*\]\]$')
_PEMBUANG = re.compile(
    r'^\s*(?:\[\[.*?\]\]|Sumber\s*:|Keterangan\s*:'
    r'|DAFTAR\s+(?:PUSTAKA|ISI|TABEL|GAMBAR|LAMPIRAN)'
    r'|LAMPIRAN\b|Lampiran\s+\d)\s*', re.I)
_TITIK_ISI = re.compile(r'\.{4,}|[\u2026]{2,}')


def buang_kandidat(s):
    return bool(POLA_CAPTION.match(s) or POLA_SUMBER.match(s) or POLA_MARKER.match(s)
                or _PEMBUANG.match(s) or _TITIK_ISI.search(s))


def main():
    fid = int(sys.argv[1]) if len(sys.argv) > 1 else 81
    awal = int(sys.argv[2]) if len(sys.argv) > 2 else 280
    akhir = int(sys.argv[3]) if len(sys.argv) > 3 else 420
    jdl = sys.argv[4] if len(sys.argv) > 4 else 'ASIH'
    sorot = [int(x) for x in sys.argv[5:]] if len(sys.argv) > 5 else []

    db = SessionLocal()
    try:
        fb = db.get(FileBerkas, fid)
        p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
        baris = (_teks_dari_berkas(p, fb.nama or '') or '').split('\n')
        akhir = min(akhir, len(baris))

        def _t(j):
            if 0 <= j < len(baris):
                return ('L%06d| ' % j) + ' '.join(baris[j].split())[:58]
            return '(tepi)'

        # kandidat = baris TIDAK KOSONG yang BUKAN pembuang (jendela tetap apa adanya)
        kand = [i for i in range(awal, akhir) if baris[i].strip() and not buang_kandidat(baris[i].strip())]
        print('═' * 72)
        print(f'📄 UJI 20 (ROLLBACK): fid={fid} {jdl} · {awal}-{akhir}')
        print(f'   kandidat {len(kand)} · JENDELA = baris j-1,j,j+1 APA ADANYA (termasuk kosong)')
        print(f'   contoh: L000350 "BAB I" → sebelum={_t(349)!r} sesudah={_t(351)!r}')

        paket, tanya, alamat = {}, {}, []
        for n, i in enumerate(kand):
            nm = f'c{n}'
            alamat.append((nm, i))
            paket[nm] = {'sebelum': _t(i - 1), 'tengah': _t(i), 'sesudah': _t(i + 1)}
            tanya[nm] = {'type': 'choice',
                         'instructions': (f'Baris `{nm}.tengah` ada di dalam naskah '
                                          f'akademik. Baris tengah ini perannya apa?'),
                         'criteria': dict(KRITERIA)}
        bahan = json.dumps(paket, ensure_ascii=False)
        print(f'   bahan {len(bahan):,} kar')

        semua = {i: [] for _n, i in alamat}
        for k in range(PUTARAN):
            t0 = time.time()
            jw = satpam.tanya_bebas_mutu(bahan[:58000], tanya) or {}
            ok = 0
            for nm, i in alamat:
                v = (jw.get(nm) or {}).get('choice')
                if isinstance(v, dict):
                    v = v.get('id') or v.get('label')
                semua[i].append(v)
                if v:
                    ok += 1
            print(f'   ▶ putaran {k+1}: {time.time()-t0:.1f} dtk ({ok}/{len(alamat)})')
            time.sleep(0.8)

        hasil = {}
        print(f'\n   📊 SEBARAN:')
        for nm, i in alamat:
            vs = [x for x in semua[i] if x]
            dari = {}
            for v in vs:
                dari[v] = dari.get(v, 0) + 1
            utama = max(dari, key=dari.get) if dari else None
            pct = 100 * dari.get(utama, 0) / max(1, len(vs))
            hasil[i] = utama
            if utama in ('bab', 'subbab', 'paragraf'):
                emo = {'bab': '🅱️', 'subbab': '🔷', 'paragraf': '📄'}[utama]
                tanda = '✅' if pct >= 90 else '🟡'
                print(f'      {emo} L{i:06d} [{tanda}{pct:.0f}%] {baris[i].strip()[:42]}')
        goyang = [(i, semua[i]) for i, v in hasil.items() if len(set(x for x in semua[i] if x)) > 1]
        print(f'   🎯 GOYANG: {len(goyang)}')
        for i, v in goyang:
            print(f'      L{i:06d} {v} | {baris[i].strip()[:40]}')

        if sorot:
            print('   🔍 BARIS BOS SOROT:')
            for t in sorot:
                if t in hasil:
                    print(f'      L{t:06d} {hasil[t]} | {baris[t].strip()[:40]}')
                else:
                    print(f'      L{t:06d} — dibuang sebagai kandidat (caption/penanda)')

        # ── SAJIAN ──
        BAR = {'bab': ('🅱️', '#c8e6c9', 'AWAL BAB'),
               'subbab': ('🔷', '#bbdefb', 'AWAL SUB-BAB'),
               'paragraf': ('📄', '#fff9c4', 'AWAL PARAGRAF'),
               'biasa': ('', '', '')}
        kiri, kanan = [], []
        for i in range(awal, akhir):
            s = baris[i].strip()
            no = f'L{i:06d}'
            if not s:
                kiri.append(f'<div class="b kosong"><span class="id">{no}</span>(kosong)</div>')
                kanan.append(f'<div class="b kosong"><span class="id">{no}</span>(kosong)</div>')
                continue
            kiri.append(f'<div class="b"><span class="id">{no}</span><span class="tx">{html.escape(s)}</span></div>')
            v = hasil.get(i)
            emo, bg, ket = BAR.get(v, ('', '', ''))
            st = f' style="background:{bg}"' if bg else ''
            sr = ' sorot' if i in sorot else ''
            kanan.append(f'<div class="b{sr}"{st}><span class="id">{no}</span>'
                         f'<span class="tg">{emo} {ket}</span><span class="tx">{html.escape(s)}</span></div>')
        dok = f'''<!doctype html><html lang="id"><head><meta charset="utf-8">
<title>Uji 20 ROLLBACK — {jdl}</title><style>
body{{font-family:system-ui,sans-serif;margin:14px;color:#222}}
h1{{font-size:17px}} .kotak{{background:#fff3e0;padding:9px;border-radius:8px;font-size:13px;margin-bottom:10px}}
.dua{{display:flex;gap:12px}} .kol{{flex:1;min-width:0;border:1px solid #ddd;border-radius:8px;overflow:hidden}}
.kepala{{background:#37474f;color:#fff;padding:6px 9px;font-size:12px;font-weight:600}}
.kepala.k2{{background:#e65100}}
.b{{display:flex;gap:6px;padding:2px 7px;border-bottom:1px solid #f4f4f4;font-size:12px;line-height:1.4}}
.b.sorot{{outline:2px solid #e91e63;outline-offset:-2px}}
.id{{color:#999;font-family:monospace;font-size:9.5px;flex:0 0 58px;padding-top:2px}}
.tx{{flex:1;word-wrap:break-word}} .tg{{flex:0 0 92px;font-size:9.5px}}
.kosong{{color:#ccc;font-size:9.5px}}
</style></head><body>
<h1>🧪 Uji 20 — ROLLBACK ke cara uji 12 · {jdl}</h1>
<div class="kotak"><b>ROLLBACK:</b> jendela = baris <b>APA ADANYA</b> (termasuk baris kosong) — kembali ke cara uji 12 yang 90%.
Saringan hanya membuang KANDIDAT, bukan mengubah jendela. {len(kand)} kandidat · {len(goyang)} goyang.
Kotak <b style="color:#e91e63">MERAH</b> = baris yang Bos sorot.</div>
<div class="dua">
<div class="kol"><div class="kepala">📄 NASKAH ASLI</div>{''.join(kiri)}</div>
<div class="kol"><div class="kepala k2">🔎 + TANDA JEV (rollback)</div>{''.join(kanan)}</div>
</div></body></html>'''
        open(f'/app/SAJI_UJI20_{jdl}.html', 'w').write(dok)
        print(f'\n   SAJI: /app/SAJI_UJI20_{jdl}.html')
    finally:
        db.close()


if __name__ == '__main__':
    main()
