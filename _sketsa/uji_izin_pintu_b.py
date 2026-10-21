#!/usr/bin/env python3
"""UJI PRIORITAS 1B — KARTU IZIN PINTU B (29Sep26).

Patch editor.html: `if (d.bagian > 1 || !d.bab)` — Pintu B (tanpa bab,
dibalas server `bab:''`) SELALU minta izin; dulu hanya `bagian > 1`,
jadi naskah 1 bagian (44.782 kar) masuk SENYAP tanpa user tahu kuota.

Dua arah (wajib):
  B1 = Pintu B (radio default `__seluruh__`, naskah 44.782 kar = 1 bagian)
       → kartu izin WAJIB TAMPIL ("Ya, proses 1 bagian") — lalu BATAL.
  B2 = Pintu A (radio BAB ke-2 = bab terpilih, 1 bagian)
       → kartu izin TIDAK tampil, tombol langsung "AI sedang bekerja"
       (regresi: revisi sub-bab tetap ringkas, jalankan AI sungguhan TR kecil).

Login browser: cookie `eduai_session` via app.auth.buat_token(7) +
Network.setCookie (cara terbukti di memory Wulan).
Potret: alat TUNGGAL _sketsa/potret_cdp.py (socket mentah, CDP :9333).

Jalankan DARI HOST:  python3 _sketsa/uji_izin_pintu_b.py
"""
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from potret_cdp import Tab, tab_baru, bersihkan_tab, CDP  # noqa: E402

URL = 'https://eduai.bikinaja.id'
FID = 70                      # SKRIPSI-S1 44.782 kar → 1 bagian
KOM = 'Perkuat latar belakang dan rapikan kalimatnya.'
KELUAR = Path('/opt/data/services/eduai-publishing/_arsip')


def token_sesi() -> str:
    p = subprocess.run(
        ['docker', 'exec', '-i', 'eduai-app', 'python3', '-'],
        input=("import sys; sys.path.insert(0,'/app')\n"
               "from app.auth import buat_token\n"
               "print(buat_token(7))\n"),
        capture_output=True, text=True, timeout=30)
    return (p.stdout or '').strip().splitlines()[-1]


def js(tab, ekspresi, timeout=30):
    r = tab.cmd('Runtime.evaluate',
                {'expression': ekspresi, 'returnByValue': True},
                timeout=timeout)
    res = r.get('result', {}).get('result', {})
    if res.get('type') == 'object':
        return res.get('value')
    return res.get('value')


def potret(tab, keluar):
    r = tab.cmd('Page.captureScreenshot', {'format': 'png'}, timeout=60)
    data = r.get('result', {}).get('data')
    if not data:
        print(f'  ❌ tak ada gambar: {json.dumps(r)[:150]}')
        return None
    import base64
    raw = base64.b64decode(data)
    Path(keluar).write_bytes(raw)
    print(f'  ✅ {keluar} — {len(raw)} byte')
    return keluar if len(raw) > 10000 else None


def siapkan(tab, tunggu_bab=False):
    """Login cookie → buka /edit/FID → tunggu daftar bab."""
    tok = token_sesi()
    tab.cmd('Network.enable')
    tab.cmd('Network.setCookie', {
        'name': 'eduai_session', 'value': tok,
        'domain': 'eduai.bikinaja.id', 'path': '/',
        'secure': True, 'httpOnly': True})
    tab.cmd('Page.enable')
    tab.cmd('Emulation.setDeviceMetricsOverride',
            {'width': 1400, 'height': 1300, 'deviceScaleFactor': 1,
             'mobile': False})
    tab.cmd('Page.navigate', {'url': f'{URL}/edit/{FID}'})
    time.sleep(8)
    #  ⚠️ JEBAKAN TERUKUR (uji pertama): daftar bab datang LAMBAT lewat
    #     fetch — baca sekali = `bab:0` padahal nanti muncul. Polling dulu.
    if tunggu_bab:
        for _ in range(15):
            n = js(tab, "document.querySelectorAll(\"input[name='pai-bab']\").length")
            if isinstance(n, int) and n >= 2:
                break
            time.sleep(2)
    return js(tab, "JSON.stringify({"
                   "judul: document.title,"
                   "bab: document.querySelectorAll(\"input[name='pai-bab']\").length,"
                   "terpilih: (document.querySelector(\"input[name='pai-bab']:checked\")||{}).value,"
                   "kotak: !!document.getElementById('pai-kotak')})")


def isi_komentar_jalan(tab):
    js(tab, "(function(){"
            "var k=document.getElementById('pai-kotak');"
            "k.value=" + json.dumps(KOM) + ";"
            "document.getElementById('pai-tambah').click();"
            "return document.querySelectorAll('.pai-komentar, .pai-daftar .baris').length;"
            "})()")
    time.sleep(1)
    return js(tab, "document.getElementById('pai-jalan').click(); 'diklik'")


def baca_izin(tab):
    return js(tab, "JSON.stringify({"
                   "izin_tersembunyi: document.getElementById('pai-wadah-izin').hidden,"
                   "izin_teks: (document.getElementById('pai-wadah-izin').innerText||'').slice(0,300),"
                   "tombol: (document.getElementById('pai-jalan').textContent||'').trim(),"
                   "pesan: (document.querySelector('.pesan, #pesan')||{}).innerText||''})")


def main():
    mode = (sys.argv[1] if len(sys.argv) > 1 else 'SEMUA').upper()
    bersihkan_tab()
    hasil = {}

    if mode in ('SEMUA', 'B1'):
        # ══ B1 — Pintu B (default `__seluruh__`, 1 bagian) → kartu WAJIB
        print("\n══ B1 · Pintu B (seluruh naskah, 44.782 kar = 1 bagian) ══")
        tab, tid = tab_baru('about:blank')
        try:
            print('   buka:', siapkan(tab))
            # pastikan radio default memang `__seluruh__`
            terpilih = js(tab, "(document.querySelector(\"input[name='pai-bab']:checked\")||{}).value")
            if terpilih != '__seluruh__':
                js(tab, "(function(){var r=document.querySelector(\"input[name='pai-bab'][value='__seluruh__']\");"
                        "if(r){r.click();} return 'paksa__seluruh__';})()")
                time.sleep(1)
            print('   radio terpilih =', terpilih)
            print('   klik:', isi_komentar_jalan(tab))
            time.sleep(7)          # waktu /v1/hitung + render kartu
            hasil['B1'] = json.loads(baca_izin(tab) or '{}')
            print('   B1 =', json.dumps(hasil['B1'], ensure_ascii=False))
            # scroll ke kartu izin supaya terlihat di potret
            js(tab, "(function(){var e=document.getElementById('pai-wadah-izin');"
                    "if(e){e.scrollIntoView({block:'center'});} return 'ok';})()")
            time.sleep(1)
            hasil['B1_png'] = str(potret(tab, KELUAR / 'uji_izin_B1_pintu_b.png'))
        finally:
            try:
                urllib.request.urlopen(f'{CDP}/json/close/{tid}', timeout=5).read()
            except Exception:                                       # noqa: BLE001
                pass
            tab.tutup()

    if mode in ('SEMUA', 'B2'):
        # ══ B2 — Pintu A (bab ke-2 terpilih, 1 bagian) → kartu TIDAK tampil
        print("\n══ B2 · Pintu A (bab terpilih ke-2) — regresi: tanpa kartu ══")
        tab, tid = tab_baru('about:blank')
        try:
            print('   buka:', siapkan(tab))
            #  🔑 AKAR GAGAL B2 (2×): daftar bab HANYA dimuat saat panel AI
            #     dibuka (`bukaPanel(true)` → `muatBab()`, editor.html:808).
            #     Skrip lama tak pernah buka panel → `bab:0` terus.
            print('   klik panel:', js(tab, "(function(){"
                                            "var t=document.getElementById('tombol-ai');"
                                            "if(!t){return 'TOMBOL_TIDAK_ADA';}"
                                            "t.click(); return 'ok';})()"))
            # polling SETELAH panel terbuka (fetch /api/ai/v1/bab async)
            for _ in range(15):
                n = js(tab, "document.querySelectorAll(\"input[name='pai-bab']\").length")
                if isinstance(n, int) and n >= 2:
                    break
                time.sleep(2)
            print('   daftar bab:', js(tab, "JSON.stringify({"
                                            "bab:document.querySelectorAll(\"input[name='pai-bab']\").length,"
                                            "terpilih:(document.querySelector(\"input[name='pai-bab']:checked\")||{}).value})"))
            pilih = js(tab, "(function(){var rs=document.querySelectorAll(\"input[name='pai-bab']\");"
                            "if(rs.length<2){return 'HANYA_'+rs.length;}"
                            "rs[1].click(); return rs[1].value;})()")
            print('   radio terpilih =', pilih)
            time.sleep(2)
            print('   klik:', isi_komentar_jalan(tab))
            time.sleep(7)
            hasil['B2'] = json.loads(baca_izin(tab) or '{}')
            print('   B2 =', json.dumps(hasil['B2'], ensure_ascii=False))
            hasil['B2_png'] = str(potret(tab, KELUAR / 'uji_izin_B2_pintu_a.png'))
        finally:
            try:
                urllib.request.urlopen(f'{CDP}/json/close/{tid}', timeout=5).read()
            except Exception:                                       # noqa: BLE001
                pass
            tab.tutup()

    (KELUAR / 'uji_izin_pintu_b_29sep.json').write_text(
        json.dumps(hasil, indent=2, ensure_ascii=False), encoding='utf-8')

    # ═══ PENILAIAN OTOMATIS ═══
    b1 = hasil.get('B1', {})
    b2 = hasil.get('B2', {})
    lulus_b1 = (b1.get('izin_tersembunyi') is False
                and 'proses 1 bagian' in (b1.get('izin_teks') or ''))
    lulus_b2 = (b2.get('izin_tersembunyi') is True
                and 'kerja' in (b2.get('tombol') or '').lower())
    print(f"\n== PENILAIAN ==\n  B1 kartu izin TAMPIL : "
          f"{'✅ LULUS' if lulus_b1 else '❌ GAGAL'}")
    print(f"  B2 tanpa kartu (ringkas): "
          f"{'✅ LULUS' if lulus_b2 else '❌ GAGAL'}")
    return 0 if (lulus_b1 and lulus_b2) else 1


if __name__ == '__main__':
    sys.exit(main())
