"""UJI E2E LAYAR — dashboard MAHASISWA ↔ PEMBIMBING (AI NYATA, naskah NYATA).

MENGAPA: Bos minta uji end-to-end dari LAYAR, bukan lewat skrip HTTP tiruan.
    Uji HTTP bisa HIJAU walau layarnya rusak (pelajaran "MATI SENYAP" 24Sep26:
    uji teks hijau, MATA menemukan bug).

DASAR ALAT (aturan Bos: jangan bikin alat baru kalau sudah ada):
    `_sketsa/potret_cdp.py` — socket mentah CDP, sudah TERBUKTI.
    Berkas ini HANYA menambah: klik, isi form, baca DOM, unggah berkas,
    dan potret tiap langkah.

NASKAH NYATA : /app/_naskah_bos_uji.docx  (proposal tesis Bos, 63.797 kar)
AKUN MAHASISWA: uji-berbayar-e2e@test.local (id 6, paket penulis)

JALANKAN DI HOST:
    python3 _sketsa/uji_e2e_layar.py
"""
import json
import os
import pathlib
import sys
import time
import urllib.request

sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa')
from potret_cdp import CDP, Tab, bersihkan_tab, tab_baru  # noqa: E402

BASE = 'https://eduai.bikinaja.id'
KELUARAN = pathlib.Path('/opt/data/services/eduai-publishing/_sketsa/e2e_bukti')
KELUARAN.mkdir(exist_ok=True)

EMAIL = 'uji-berbayar-e2e@test.local'
SANDI = 'UjiBayar123!'

LULUS = GAGAL = 0
CATATAN = []


def cek(nama: str, syarat: bool, bukti: str = '') -> bool:
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}' + (f' — {bukti}' if bukti else ''))
    else:
        GAGAL += 1
        print(f'  ❌ {nama}' + (f' — {bukti}' if bukti else ''))
    return bool(syarat)


def info(t: str) -> None:
    print(f'     · {t}')
    CATATAN.append(t)


class Sesi:
    """Satu tab yang dipakai terus (login tetap) + potret tiap langkah."""

    def __init__(self, lebar: int = 1500, tinggi: int = 1400):
        bersihkan_tab()
        self.url0 = f'{BASE}/masuk'
        self.tab, self.tid = tab_baru(self.url0)
        self.tab.cmd('Page.enable')
        self.tab.cmd('Emulation.setDeviceMetricsOverride',
                     {'width': lebar, 'height': tinggi,
                      'deviceScaleFactor': 1, 'mobile': False})
        time.sleep(3)

    # ── inti ────────────────────────────────────────────────────────────
    def js(self, expr: str, tunggu: float = 0.0):
        if tunggu:
            time.sleep(tunggu)
        r = self.tab.cmd('Runtime.evaluate',
                         {'expression': expr, 'returnByValue': True,
                          'awaitPromise': True}, timeout=60)
        if r.get('error'):
            info(f'JS galat: {json.dumps(r)[:150]}')
            return None
        return r.get('result', {}).get('result', {}).get('value')

    def ke(self, url: str, tunggu: float = 4.0):
        self.tab.cmd('Page.navigate', {'url': url})
        time.sleep(tunggu)

    def potret(self, nama: str, tinggi: int | None = None) -> str | None:
        if tinggi:
            self.tab.cmd('Emulation.setDeviceMetricsOverride',
                         {'width': 1500, 'height': tinggi,
                          'deviceScaleFactor': 1, 'mobile': False})
            time.sleep(0.8)
        r = self.tab.cmd('Page.captureScreenshot', {'format': 'png'},
                         timeout=60)
        data = r.get('result', {}).get('data')
        if not data:
            info(f'potret {nama} GAGAL: {json.dumps(r)[:120]}')
            return None
        import base64
        raw = base64.b64decode(data)
        f = KELUARAN / f'{nama}.png'
        f.write_bytes(raw)
        info(f'potret {nama}: {len(raw)} byte')
        return str(f) if len(raw) > 10000 else None

    def tutup(self):
        try:
            urllib.request.urlopen(f'{CDP}/json/close/{self.tid}',
                                   timeout=5).read()
        except Exception:                                      # noqa: BLE001
            pass
        self.tab.tutup()


def isi_form(s: Sesi, nama_field: str, nilai: str) -> bool:
    """Isi input/textarea by name (pakai setter React-safe kalau perlu)."""
    expr = f"""
    (function(){{
      var el = document.querySelector('[name="{nama_field}"]');
      if(!el) return 'TIDAK ADA';
      el.focus();
      el.value = {json.dumps(nilai)};
      el.dispatchEvent(new Event('input', {{bubbles:true}}));
      el.dispatchEvent(new Event('change', {{bubbles:true}}));
      return 'ok:' + el.value.length;
    }})()
    """
    return str(s.js(expr, tunggu=0.3))


def klik(s: Sesi, pemilih: str, tunggu: float = 3.0) -> bool:
    expr = f"""
    (function(){{
      var el = document.querySelector({json.dumps(pemilih)});
      if(!el) return 'TIDAK ADA';
      el.click();
      return 'klik';
    }})()
    """
    r = str(s.js(expr))
    if r.startswith('TIDAK ADA'):
        return False
    time.sleep(tunggu)
    return True
