"""Buka /edit/80 (dokumen BARU) di browser -> baca bahasa yang TAMPIL + potret."""
import base64, importlib.util, json, os, subprocess, sys, time

BASE = "https://eduai.bikinaja.id"
FID = 80

spec = importlib.util.spec_from_file_location(
    "ph", "/opt/data/skills/creative/bayana-publishing-web/scripts/potret_halaman.py")
ph = importlib.util.module_from_spec(spec); spec.loader.exec_module(ph)


def d(cmd):
    return subprocess.run(cmd, capture_output=True, text=True).stdout.strip()


T = d(["docker", "exec", "eduai-app", "python3", "-c",
       "from app.auth import buat_token; print(buat_token(7))"])
C = d(["docker", "exec", "eduai-app", "python3", "-c",
       "from app.config import SESSION_COOKIE; print(SESSION_COOKIE)"])

t = ph.Tab()
try:
    t.perintah('Page.enable'); t.perintah('Runtime.enable'); t.perintah('Network.enable')
    t.perintah('Network.setCookie', name=C, value=T, domain="eduai.bikinaja.id",
               path="/", secure=True)
    t.perintah('Emulation.setDeviceMetricsOverride', width=1440, height=900,
               deviceScaleFactor=1, mobile=False)
    t.perintah('Page.navigate', url=f"{BASE}/edit/{FID}")
    for i in range(45):
        time.sleep(3)
        st = t.js("""(() => {
          const f = document.querySelector('iframe');
          let par = 0;
          try { const d2 = f.contentDocument || f.contentWindow.document;
                par = d2.body ? d2.body.innerText.length : 0; } catch(e){}
          const m = document.getElementById('memuat');
          return JSON.stringify({par, memuat: m ? !m.hidden : false});
        })()""")
        o = json.loads(st)
        if o['par'] > 300 and not o['memuat']:
            print("  siap pada", (i+1)*3, "detik"); break
    else:
        print("  (belum penuh, lanjut saja)")

    print("\n=== bahasa yang TAMPIL di editor ===")
    hasil = t.js("""(() => {
      const f = document.querySelector('iframe');
      if (!f) return JSON.stringify({err:'tanpa iframe'});
      let d2; try { d2 = f.contentDocument || f.contentWindow.document; }
      catch(e) { return JSON.stringify({err:'CORS'}); }
      const teks = (d2.body ? d2.body.innerText : '');
      const cari = ['English – United States','English - United States','Indonesian',
                    'Indonesia','Cacah kata','Word count','één','sv-SE'];
      const ada = {}; cari.forEach(k => { ada[k] = teks.includes(k); });
      return JSON.stringify({ada, cuplikan: teks.slice(0, 400)});
    })()""")
    print(hasil)

    p = "/tmp/editor_bahasa_baru.png"
    d2 = t.perintah('Page.captureScreenshot', format='png')
    open(p, 'wb').write(base64.b64decode(d2['data']))
    print("\nPOTRET ->", p, os.path.getsize(p), "byte")
finally:
    t.tutup()
