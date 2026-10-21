"""SAJI 3 HASIL REVISI (A/B/C) untuk DINILAI BOS.

Uji 2 sudah jalan 3 cara. Sekarang hasilnya DISAJIKAN sebagai berkas HTML
supaya Bos bisa MEMBACA & MENILAI mana yang terbaik (mata Bos > ukuran Wulan).

3 cara (bahan SAMA, komentar SAMA):
  A · BAB PENUH       — seluruh BAB II (60.288 kar)  [cara SEKARANG]
  B · POTONGAN SAJA   — hanya sub-bab 2.1.5 (980 kar)
  C · POTONGAN + PETA — potongan + peta naskah (1.253 kar)
"""
import sys, time, html, json
sys.path.insert(0, '/app')

from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR, _urai_jawaban
from app.models import FileBerkas
import os, re, urllib.request

KOMENTAR = ("Bagian ini masih terlalu umum, tolong perdalam dengan contoh konkret "
            "dan tambahkan rujukan yang relevan.")
SUBBAB = (1828, 1872)


def teks_naskah(db, fid):
    fb = db.get(FileBerkas, fid)
    p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
    return (_teks_dari_berkas(p, fb.nama or '') or ''), (fb.nama or '')


def panggil(perintah, bahan, judul=''):
    base = os.environ.get('EDUAI_ROUTER_BASE') or 'http://9router:20128/v1'
    kunci = os.environ.get('EDUAI_ROUTER_KEY') or 'x'
    model = os.environ.get('EDUAI_AI_MODEL') or 'EduAi'
    kepala = (f'Kamu membantu mahasiswa memperbaiki naskah tesis. '
              f'{("Bagian yang direvisi: " + judul) if judul else ""}\n'
              f'PERMINTAAN PEMBIMBING: {perintah}\n'
              f'Tulis ULANG bagian yang diberikan sesuai permintaan. '
              f'Keluarkan HANYA teks hasil revisi, tanpa penjelasan tambahan.\n\n'
              f'--- BAHAN ---\n')
    body = json.dumps({'model': model, 'temperature': 0.3,
                       #  🚨 SETELAN PRODUKSI (ACC Bos 29Sep26, app/ai.py:966):
                       #  reasoning WAJIB mati — kalau nyala, jatah token habis
                       #  untuk berpikir → content KOSONG (terukur 15Okt26).
                       'enable_thinking': False,
                       'messages': [{'role': 'user',
                                     'content': kepala + bahan + '\n--- AKHIR BAHAN ---\n'}]}).encode()
    req = urllib.request.Request(base.rstrip('/') + '/chat/completions', data=body,
                                 headers={'Content-Type': 'application/json',
                                          'Authorization': f'Bearer {kunci}'})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=240) as r:
        mentah = r.read().decode()
    isi, info = _urai_jawaban(mentah, model)
    return isi, info.get('model') or model, time.time() - t0


def main():
    fid = int(sys.argv[1]) if len(sys.argv) > 1 else 78
    db = SessionLocal()
    try:
        teks, nama = teks_naskah(db, fid)
        baris = teks.split('\n')
        potongan = '\n'.join(baris[SUBBAB[0]:SUBBAB[1]])
        awal = next(i for i in range(300, len(baris))
                    if re.match(r'^\s*BAB\s+II\b', baris[i], re.I))
        akhir = next(i for i in range(awal + 1, len(baris))
                     if re.match(r'^\s*BAB\s+III\b', baris[i], re.I))
        bab_penuh = '\n'.join(baris[awal:akhir])
        peta = ('PETA NASKAH (posisi bagian yang direvisi):\n'
                '  BAB II · TINJAUAN PUSTAKA\n'
                '    2.1. Tinjauan Teori dan Konsep\n'
                '      2.1.4. Kepercayaan\n'
                '      2.1.5. Komitmen Perusahaan   ← BAGIAN YANG DIREVISI\n'
                '      2.1.6. Komunikasi\n'
                '    2.2. Penelitian Terdahulu\n\n'
                '--- BAGIAN YANG DIREVISI ---\n')

        asli = potongan
        hasil = {}
        for label, bahan in (('A', bab_penuh), ('B', potongan),
                             ('C', peta + potongan)):
            try:
                kel, model, dtk = panggil(KOMENTAR, bahan, 'Komitmen Perusahaan')
                hasil[label] = (kel, model, dtk)
                print(f'{label} OK {dtk:.1f} dtk {len(kel):,} kar')
            except Exception as e:                              # noqa: BLE001
                print(f'{label} GAGAL {type(e).__name__}: {e}')
                hasil[label] = None

        def blok(judul, isi):
            return (f'<h3>{judul}</h3>\n'
                    f'<pre style="white-space:pre-wrap;background:#f7f7f5;'
                    f'padding:12px;border-left:4px solid #ccc;font-size:13px">'
                    f'{html.escape(isi)}</pre>\n')

        bagian = [f'''<!doctype html><html lang="id"><head><meta charset="utf-8">
<title>Uji 2 — 3 Cara Kirim ke AI</title>
<style>body{{font-family:system-ui,sans-serif;max-width:1000px;margin:24px auto;
padding:0 16px;line-height:1.55;color:#222}}
h1{{font-size:22px}} h2{{font-size:18px;margin-top:32px;border-top:2px solid #eee;padding-top:16px}}
.kotak{{background:#eef6ee;padding:12px;border-radius:8px;font-size:14px}}
table{{border-collapse:collapse;font-size:14px;margin:12px 0}}
th,td{{border:1px solid #ddd;padding:6px 10px;text-align:left}}
th{{background:#f2f2f2}}</style></head><body>
<h1>🧪 Uji 2 — Banding 3 Cara Kirim Bagian ke AI</h1>
<div class="kotak"><b>Bagian yang direvisi:</b> 2.1.5. Komitmen Perusahaan
(baris 1828–1872, {len(asli):,} kar)<br>
<b>Komentar pembimbing (SAMA untuk ketiganya):</b><br><i>{html.escape(KOMENTAR)}</i></div>
<table><tr><th>Cara</th><th>Bahan dikirim</th><th>Waktu</th><th>Keluaran</th></tr>
<tr><td><b>A</b> · BAB II penuh <span style="color:#888">(cara sekarang)</span></td>
<td>{len(bab_penuh):,} kar</td><td>{hasil['A'][2]:.1f} dtk</td><td>{len(hasil['A'][0]):,} kar</td></tr>
<tr><td><b>B</b> · Potongan saja</td><td>{len(potongan):,} kar</td>
<td>{hasil['B'][2]:.1f} dtk</td><td>{len(hasil['B'][0]):,} kar</td></tr>
<tr><td><b>C</b> · Potongan + peta naskah</td><td>{len(peta)+len(potongan):,} kar</td>
<td>{hasil['C'][2]:.1f} dtk</td><td>{len(hasil['C'][0]):,} kar</td></tr>
</table>
<p style="font-size:13px;color:#666">Model asli: <b>{hasil['A'][1]}</b> ·
Naskah: {html.escape(nama[:60])}</p>
<h2>0 · NASKAH ASLI (sebelum direvisi)</h2>
{blok('2.1.5. Komitmen Perusahaan — ASLI', asli)}
<h2>1 · CARA A — BAB PENUH</h2>
{blok('Hasil A', hasil['A'][0])}
<h2>2 · CARA B — POTONGAN SAJA</h2>
{blok('Hasil B', hasil['B'][0])}
<h2>3 · CARA C — POTONGAN + PETA</h2>
{blok('Hasil C', hasil['C'][0])}
</body></html>''']

        keluar = '/app/SAJI_UJI2_3_CARA.html'
        open(keluar, 'w').write(''.join(bagian))
        print('SAJI:', keluar, os.path.getsize(keluar), 'byte')
    finally:
        db.close()


if __name__ == '__main__':
    main()
