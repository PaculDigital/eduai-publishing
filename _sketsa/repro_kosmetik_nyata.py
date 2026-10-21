"""Reproduksi 3 kosmetik — BUKTI NYATA dari layar editor OO.

Buka /edit/<fid> lewat browser CDP, lalu BACA:
  #1 bahasa editor yang BENAR-BENAR dipakai OO (bukan dari kode kita)
  #2 apakah kata 'Cacah kata' muncul (ID) atau 'Word count' (EN)
  #3 popup multipage: bahasanya apa
Potret layar untuk MATA.
"""
import base64, importlib.util, json, os, subprocess, sys, time

BASE = "https://eduai.bikinaja.id"
FID = sys.argv[1] if len(sys.argv) > 1 else "78"

spec = importlib.util.spec_from_file_location(
    "ph", "/opt/data/skills/creative/bayana-publishing-web/scripts/potret_halaman.py")
ph = importlib.util.module_from_spec(spec); spec.loader.exec_module(ph)


def _d(cmd):
    return subprocess.run(cmd, capture_output=True, text=True).stdout.strip()


T = _d(["docker", "exec", "eduai-app", "python3", "-c",
        "from app.auth import buat_token; print(buat_token(7))"])
C = _d(["docker", "exec", "eduai-app", "python3", "-c",
        "from app.config import SESSION_COOKIE; print(SESSION_COOKIE)"])
print("token/cookie:", "ada" if T else "KOSONG", "/", C)

t = ph.Tab()
try:
    t.perintah('Page.enable'); t.perintah('Runtime.enable'); t.perintah('Network.enable')
    # cookie login
    t.perintah('Network.setCookie', name=C, value=T,
               domain="eduai.bikinaja.id", path="/", secure=True)
    t.perintah('Emulation.setDeviceMetricsOverride', width=1440, height=900,
               deviceScaleFactor=1, mobile=False)
    print("\n=== buka /edit/%s ===" % FID)
    t.perintah('Page.navigate', url=f"{BASE}/edit/{FID}")
    # Tunggu editor BENAR-BENAR tampil (bukan cuma "Menyiapkan editor...")
    for i in range(40):
        time.sleep(3)
        st = t.js("""(() => {
          const f = document.querySelector('iframe');
          let par = 0, menu = 0;
          try {
            const d = f.contentDocument || f.contentWindow.document;
            par = (d.body ? d.body.innerText.length : 0);
            menu = d.querySelectorAll('#toolbar, .toolbar, #header .toolbar').length;
          } catch(e) {}
          const memuat = document.getElementById('memuat');
          const sedang = memuat ? !memuat.hidden : false;
          return JSON.stringify({par, menu, sedangMemuat: sedang});
        })()""")
        o = json.loads(st)
        print('  t=%ss par=%s menu=%s memuat=%s' % ((i+1)*3, o['par'], o['menu'], o['sedangMemuat']))
        if o['par'] > 200 and not o['sedangMemuat']:
            break

    # ---- #1: bahasa editor ----
    print("\n--- #1 BAHASA EDITOR ---")
    info = t.js("""(() => {
      const out = {htmllang: document.documentElement.lang};
      const f = document.querySelector('iframe');
      if (f) {
        out.iframe = f.getAttribute('src') || '';
        try {
          const d = f.contentDocument || f.contentWindow.document;
          out.inner = (d && d.documentElement) ? d.documentElement.lang : 'tak bisa';
          out.judulDalam = d ? (d.title || '') : '';
        } catch(e) { out.inner = 'CORS: ' + e.name; }
      }
      return JSON.stringify(out);
    })()""")
    print(info)

    # ---- #2 & #3: cari kata kunci di dalam iframe OO ----
    print("\n--- #2/#3 CARI KATA DI DALAM EDITOR ---")
    kunci = t.js("""(() => {
      const f = document.querySelector('iframe');
      if (!f) return JSON.stringify({err:'tidak ada iframe'});
      let d; try { d = f.contentDocument || f.contentWindow.document; }
      catch(e) { return JSON.stringify({err:'CORS '+e.name}); }
      const teks = (d.body ? d.body.innerText : '') + ' ';
      const cari = ['Cacah kata','Word count','Multipage view','Tampilan multipage',
                    'Tampilan banyak halaman','Single page','Halaman tunggal',
                    'Peringatan','Warning'];
      const ada = {};
      cari.forEach(k => { ada[k] = teks.includes(k); });
      return JSON.stringify({ada});
    })()""")
    print(kunci)

    # ---- bukti config yang DIKIRIM server ----
    print("\n--- config `lang` yang dikirim server ---")
    c = t.js("""(() => {
      const s = [...document.querySelectorAll('script')].map(x=>x.textContent).join('\\n');
      const m = s.match(/"lang"\\s*:\\s*"([^"]+)"/);
      const l2 = s.match(/lang['"]?\\s*:\\s*['"]([a-z-]+)['"]/i);
      return JSON.stringify({langDiConfig: m ? m[1] : null, lain: l2 ? l2[1] : null});
    })()""")
    print(c)

    potret = "/tmp/kosmetik_sebelum.png"
    dat = t.perintah('Page.captureScreenshot', format='png')
    open(potret, 'wb').write(base64.b64decode(dat['data']))
    print("\nPOTRET ->", potret, os.path.getsize(potret), "byte")
finally:
    t.tutup()
