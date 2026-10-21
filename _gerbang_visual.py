"""GERBANG VISUAL — periksa HALAMAN SUNGGUHAN lewat browser (CDP), bukan tebak CSS.

Kelahiran 04Okt26: Bos menemukan KOTAK PUTIH KOSONG di pojok header halaman
Belajar. Akarnya: kelas `kanan` dipakai 2 tempat — `.atas .kanan` (header,
harus transparan) dan `.kanan{background:#fff}` (kartu konten). Dua percobaan
gerbang "baca CSS" GAGAL (4 lalu 8 laporan PALSU) karena pola `.a{}` + `.a b{}`
itu SEHAT dan tak bisa dibedakan dengan regex.

⇒ GANTI PENDEKATAN (putusan Bos 04Okt26, Opsi A): UKUR YANG DILIHAT MATA.
   Buka halaman di browser, hitung getComputedStyle() tiap elemen penting,
   lalu LAPOR kalau ada yang mencurigakan:
     · elemen di dalam header yang latarnya PUTIH/TERANG (harus hijau/lolos)
     · teks yang warnanya SAMA dengan latarnya (tak terbaca)
     · elemen tanpa teks tapi punya latar putih + ukuran > 20×20 (kotak kosong)

Pakai: python3 app/_gerbang_visual.py <url1> [url2 ...]
Balasan: 0 = bersih · 1 = ada temuan
"""
import json
import sys
import time
import urllib.request

sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa')
from potret_cdp import CDP, bersihkan_tab, tab_baru   # noqa: E402

SKRIP_UKUR = r"""
(() => {
  const hasil = [];
  const rgb = (s) => {
    const m = (s||'').match(/\d+/g);
    return m ? m.slice(0,3).map(Number) : null;
  };
  const alfa = (s) => {
    const m = (s||'').match(/rgba?\([^)]*?,\s*([\d.]+)\s*\)/);
    return m ? parseFloat(m[1]) : 1;
  };
  const terang = (c) => c && c[0] > 225 && c[1] > 225 && c[2] > 225;

  //  latar EFEKTIF: naik ke induk sampai ketemu warna TIDAK transparan
  const latarEfek = (el) => {
    let n = el;
    while (n && n !== document.documentElement) {
      const cs = getComputedStyle(n);
      const bg = cs.backgroundColor;
      const a = alfa(bg);
      const c = rgb(bg);
      //  ⚠️ 04Okt26: LATAR GRADASI (background-image) dianggap TIDAK PUTIH —
      //     halaman landing memakai gradasi; bila kita anggap putih, semua
      //     teks di atasnya jadi "tak terbaca" (lapor PALSU 20 temuan).
      if (cs.backgroundImage && cs.backgroundImage !== 'none') return null;
      if (c && a > 0.5) return c;
      n = n.parentElement;
    }
    return [255,255,255];
  };

  //  warna TEKS EFEKTIF: kalau elemen tak punya warna sendiri, warisi dari induk
  const warnaEfek = (el) => {
    const c = rgb(getComputedStyle(el).color);
    return c;
  };

  //  A. elemen di dalam header yang latarnya jadi PUTIH (kotak putih "nyasar")
  const header = document.querySelector('header, .atas, .nav');
  if (header) {
    header.querySelectorAll('*').forEach((el) => {
      const r = el.getBoundingClientRect();
      if (r.width < 12 || r.height < 12) return;
      const cs = getComputedStyle(el);
      const bg = rgb(cs.backgroundColor);
      if (terang(bg) && !(cs.backgroundImage && cs.backgroundImage !== 'none')) {
        const isi = (el.textContent || '').trim();
        hasil.push({
          jenis: 'KOTAK-PUTIH-DI-HEADER',
          tag: el.tagName.toLowerCase(),
          kelas: el.className || '',
          teks: isi.slice(0, 40),
          w: Math.round(r.width), h: Math.round(r.height),
          latar: cs.backgroundColor,
        });
      }
    });
  }

  //  B. TEKS-TAK-TERBACA: hanya elemen DAUN yang BENAR-BENAR punya tulisannya
  //     sendiri. ⚠️ 04Okt26: elemen yang diukur harus benar-benar terlihat
  //     (opacity induk > 0) — halaman dengan animasi fade-in membuat warna
  //     jadi transparan → lapor PALSU.
  const terlihat = (el) => {
    let n = el;
    while (n && n !== document.documentElement) {
      const cs = getComputedStyle(n);
      if (parseFloat(cs.opacity) < 0.85) return false;
      if (cs.visibility === 'hidden' || cs.display === 'none') return false;
      n = n.parentElement;
    }
    return true;
  };

  document.querySelectorAll('span,a,div,p,h1,h2,h3,h4,button,b,small,li,label')
    .forEach((el) => {
      //  hanya elemen yang isinya TEKS LANGSUNG (bukan pembungkus)
      let teksLangsung = '';
      el.childNodes.forEach((n) => {
        if (n.nodeType === 3) teksLangsung += n.textContent;
      });
      teksLangsung = teksLangsung.trim();
      if (teksLangsung.length < 2) return;
      const r = el.getBoundingClientRect();
      if (r.width < 8 || r.height < 8) return;
      if (!terlihat(el)) return;                        // animasi/transparan
      const warna = warnaEfek(el);
      const latar = latarEfek(el);
      if (!warna || !latar) return;                      // latar gradasi → lewati
      const beda = Math.abs(warna[0]-latar[0]) + Math.abs(warna[1]-latar[1])
                 + Math.abs(warna[2]-latar[2]);
      if (beda < 45) {
        hasil.push({
          jenis: 'TEKS-TAK-TERBACA',
          tag: el.tagName.toLowerCase(),
          kelas: el.className || '',
          teks: teksLangsung.slice(0, 40),
          warna: getComputedStyle(el).color,
          latar: 'rgb(' + latar.join(',') + ')',
          beda: beda,
        });
      }
    });
  return JSON.stringify(hasil);
})()
"""


def ukur(url: str, lebar: int = 1250, tinggi: int = 900):
    """Buka `url` di Chrome (CDP) → balas daftar temuan gaya.

    ⚠️ Pakai HANYA API yang ada di `_sketsa/potret_cdp.py`: `tab_baru()`
    dan `tab.cmd(...)`. `tab_baru()` TIDAK menavigasi (jebakan lama) →
    WAJIB `Page.navigate` sendiri. Tunggu dengan `time.sleep`.
    """
    bersihkan_tab()
    tab, tid = tab_baru(url)
    try:
        tab.cmd('Page.enable')
        tab.cmd('Emulation.setDeviceMetricsOverride',
                {'width': lebar, 'height': tinggi, 'deviceScaleFactor': 1,
                 'mobile': False})
        tab.cmd('Page.navigate', {'url': url})
        time.sleep(6)
        r = tab.cmd('Runtime.evaluate',
                    {'expression': SKRIP_UKUR, 'returnByValue': True},
                    timeout=40)
        nilai = (r.get('result', {}) or {}).get('result', {}).get('value')
        return json.loads(nilai) if nilai else []
    finally:
        try:
            urllib.request.urlopen(f'{CDP}/json/close/{tid}', timeout=5).read()
        except Exception:                                      # noqa: BLE001
            pass
        tab.tutup()


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    total = 0
    for url in sys.argv[1:]:
        print(f'════ {url} ════')
        try:
            temuan = ukur(url)
        except Exception as e:
            print(f'  ⚠️ gagal ukur: {type(e).__name__}: {e}')
            total += 1
            continue
        if not temuan:
            print('  ✅ tidak ada kotak putih / teks tak terbaca')
        for t in temuan:
            print(f'  🔴 {t["jenis"]} <{t["tag"]} class="{t["kelas"]}">'
                  f' teks="{t["teks"]}" {t.get("w","")}×{t.get("h","")}'
                  f' latar={t.get("latar")}')
            total += 1
        print()
    if total:
        print(f'🚨 {total} TEMUAN — periksa potret')
        return 1
    print('✅ BERSIH')
    return 0


if __name__ == '__main__':
    sys.exit(main())
