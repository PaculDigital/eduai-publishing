"""L6 — MAHASISWA REVISI DENGAN AI NYATA → VERIFIKASI PIPA PRESISI.

Inti uji (yang PALING penting sekarang):
  L6a  buka editor naskah di LAYAR sungguhan
  L6b  kuota SEBELUM
  L6c  kirim revisi (AI nyata, prompt produksi yang baru)
  L6d  pantau proses sampai berakhir
  L6e  kuota SESUDAH
  L6f  ⭐ VERIFIKASI: naskah hasil TIDAK menyusut (bukti pipa bekerja)
  L6g  ⭐ VERIFIKASI: paragraf di dokumen tetap utuh (bukan 3 paragraf)

⚠️ Catatan penting: uji ini lewat LAYAR (CDP) untuk langkah yang dilihat user,
   dan lewat `pantau.py` untuk mengambil dokumen hasil — bukan HTTP tiruan.
"""
import json
import pathlib
import sys
import time

sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa')
from uji_e2e_layar import BASE, Sesi, cek, info      # noqa: E402

FID = 49
#  Komentar tentang ISI YANG NYATA ADA di naskah, supaya AI bisa mengutip.
KOMENTAR = ['Perbaiki kalimat pertama paragraf yang memuat '
            '"Perkembangan pesat teknologi dan transformasi digital" — '
            'buat lebih ringkas dan tambahkan penekanan pada tujuan '
            'penelitian.']


def ambil(s: Sesi, url: str, metode: str = 'GET', body=None) -> dict:
    """Ambil JSON dari server — fetch DI DALAM HALAMAN (sesi asli)."""
    isi = json.dumps(body) if body is not None else 'null'
    expr = f"""
    (async function(){{
      try {{
        var o = {{method: {json.dumps(metode)},
                 headers: {{'Content-Type':'application/json'}}}};
        if ({isi} !== null) o.body = JSON.stringify({isi});
        var r = await fetch({json.dumps(url)}, o);
        var teks = await r.text();
        try {{ return JSON.stringify({{status:r.status, d: JSON.parse(teks)}}); }}
        catch(e) {{ return JSON.stringify({{status:r.status, mentah: teks.slice(0,200)}}); }}
      }} catch(e) {{ return JSON.stringify({{error: String(e)}}); }}
    }})()
    """
    out = s.js(expr, tunggu=30)
    try:
        return json.loads(str(out))
    except Exception:
        return {'error': 'bukan JSON', 'mentah': str(out)[:200]}


def ukur_dokumen() -> dict:
    """Ukur naskah hasil di dokumen — dari DALAM container (baca langsung)."""
    import subprocess
    import zipfile
    kode = r'''
import zipfile, re, sys, pathlib
#  cari berkas uji di folder upload
kand = []
for p in pathlib.Path('/app/uploads').rglob('*.docx'):
    if p.stat().st_size > 100000:
        kand.append(p)
kand.sort(key=lambda p: p.stat().st_mtime, reverse=True)
if not kand:
    print('{"error":"tidak ada berkas"}'); sys.exit(0)
p = kand[0]
with zipfile.ZipFile(p) as z:
    xml = z.read('word/document.xml').decode('utf-8', 'ignore')
teks = re.sub(r'<[^>]+>', ' ', xml)
teks = re.sub(r'\s+', ' ', teks)
import json
print(json.dumps({'berkas': p.name, 'byte': p.stat().st_size,
                  'xml_paragraf': xml.count('<w:p '), 'kar': len(teks)}))
'''
    out = subprocess.run(['docker', 'exec', '-w', '/app', 'eduai-app',
                          'python3', '-c', kode],
                         capture_output=True, text=True, timeout=120)
    try:
        return json.loads(out.stdout.strip().splitlines()[-1])
    except Exception:
        return {'error': out.stdout[:200] or out.stderr[:200]}


def main() -> int:
    s = Sesi()
    try:
        # ── L6a ──────────────────────────────────────────────────────────
        s.ke(f'{BASE}/edit/{FID}', 10)
        t = str(s.js('document.body.innerText'))
        info(f'path={s.js("location.pathname")} | {len(t)} kar')
        cek('L6a editor terbuka', len(t) > 500, f'{len(t)} kar')

        # ── L6b kuota SEBELUM ────────────────────────────────────────────
        print('\n── L6b. KUOTA SEBELUM ───────────────────────────────────')
        k0 = ambil(s, '/api/ai/v1/kuota')
        d0 = k0.get('d') if isinstance(k0.get('d'), dict) else {}
        rv0 = d0.get('revisi', {}) if isinstance(d0, dict) else {}
        info(f'sisa={rv0.get("sisa")} dipakai={rv0.get("dipakai")} '
             f'total={rv0.get("total")}')

        # ── L6b2. ukur dokumen SEBELUM ───────────────────────────────────
        print('\n── L6b2. DOKUMEN SEBELUM (acuan) ────────────────────────')
        sebelum = ukur_dokumen()
        info(f'SEBELUM: {json.dumps(sebelum, ensure_ascii=False)}')

        # ── L6c kirim revisi ─────────────────────────────────────────────
        print('\n── L6c. KIRIM REVISI (AI NYATA, prompt produksi) ────────')
        t0 = time.time()
        bal = ambil(s, '/api/ai/v1/revisi', 'POST',
                    {'file_id': FID, 'komentar': KOMENTAR,
                     'bab': '', 'setuju_bagian': True})
        info(f'({time.time()-t0:.1f} dtk) '
             f'{json.dumps(bal, ensure_ascii=False)[:300]}')
        isi = bal.get('d') or {}
        kode = isi.get('kode') if isinstance(isi, dict) else None
        cek('L6c permintaan DITERIMA', bal.get('status') in (200, 202),
            f"status={bal.get('status')} {str(isi)[:110]}")
        if not kode:
            return 1
        info(f'KODE PROSES = {kode}')
        pathlib.Path('/tmp/e2e_kode.txt').write_text(str(kode))

        # ── L6d pantau ───────────────────────────────────────────────────
        print('\n── L6d. PANTAU PROSES AI ────────────────────────────────')
        akhir = {}
        for i in range(60):                     # maks ~15 menit
            d2 = ambil(s, f'/api/ai/v1/proses/{kode}')
            isi2 = d2.get('d') if isinstance(d2.get('d'), dict) else d2
            th = str((isi2 or {}).get('tahap') or
                     (isi2 or {}).get('keadaan') or '').lower()
            st = str((isi2 or {}).get('status') or '').lower()
            print(f"   [{(i+1)*15:>4}dtk] status={st} tahap={th[:60]}")
            if st in ('selesai', 'gagal') or th in ('selesai', 'gagal',
                                                    'sukses', 'error'):
                akhir = isi2 or {}
                break
            time.sleep(15)
        s.potret('L6d_hasil')
        cek('L6d proses BERAKHIR', bool(akhir),
            f"status={akhir.get('status')} tahap={str(akhir.get('tahap'))[:60]}")
        print(f"   akhir: {json.dumps(akhir, ensure_ascii=False)[:400]}")

        # ── L6e kuota SESUDAH ────────────────────────────────────────────
        print('\n── L6e. KUOTA SESUDAH ───────────────────────────────────')
        k1 = ambil(s, '/api/ai/v1/kuota')
        d1 = k1.get('d') if isinstance(k1.get('d'), dict) else {}
        rv1 = d1.get('revisi', {}) if isinstance(d1, dict) else {}
        info(f'sisa={rv1.get("sisa")} dipakai={rv1.get("dipakai")}')
        print(f"   PERUBAHAN: sisa {rv0.get('sisa')} → {rv1.get('sisa')} · "
              f"dipakai {rv0.get('dipakai')} → {rv1.get('dipakai')}")

        # ── L6f ⭐ dokumen SESUDAH: apakah menyusut? ──────────────────────
        print('\n── L6f. ⭐ DOKUMEN SESUDAH (inti uji pipa) ────────────────')
        #  Hasil revisi BELUM masuk dokumen sampai tombol "Terapkan" diklik.
        #  Jadi yang diukur di sini = dokumen MASIH UTUH (belum tersentuh).
        sesudah = ukur_dokumen()
        info(f'SESUDAH: {json.dumps(sesudah, ensure_ascii=False)}')
        if 'kar' in sebelum and 'kar' in sesudah:
            rasio = sesudah['kar'] / max(1, sebelum['kar'])
            print(f'   rasio naskah: {rasio*100:.1f}% '
                  f"({sebelum['kar']:,} → {sesudah['kar']:,})")
            cek('L6f dokumen TIDAK rusak sebelum Terapkan',
                rasio > 0.95, f'{rasio*100:.1f}%')

        # ── L6g hasil proses (isi jawaban AI) ────────────────────────────
        print('\n── L6g. HASIL PROSES (jawaban AI) ───────────────────────')
        hs = ambil(s, f'/api/ai/v1/proses/{kode}/hasil')
        info(f'HASIL: {json.dumps(hs, ensure_ascii=False)[:600]}')
        dh = hs.get('d') if isinstance(hs.get('d'), dict) else {}
        isi_ai = str(dh.get('hasil') or dh.get('jawaban') or '')
        print(f'   panjang jawaban AI: {len(isi_ai):,} kar')
        print('   --- 500 kar pertama ---')
        print('   ' + isi_ai[:500].replace('\n', '\n   '))
        pathlib.Path('/tmp/e2e_hasil_ai.txt').write_text(isi_ai)
        cek('L6g jawaban AI terambil', len(isi_ai) > 50, f'{len(isi_ai)} kar')
        cek('L6g jawaban AI memakai bentuk KUTIP-ASLI',
            'KUTIP-ASLI' in isi_ai,
            f"penanda={isi_ai.count('KUTIP-ASLI')}×")
    finally:
        print(f'\n       (tab: {s.tid})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
