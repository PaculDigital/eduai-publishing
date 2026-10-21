"""E2E penuh: lampiran nyata (docx contoh kalimat + gambar contoh) → AI
menggunakan isinya. Dua putaran: teks & gambar. Jalan di container.
"""
import io
import json
import sys
import urllib.request

sys.path.insert(0, '/app')
from app.auth import buat_token                    # noqa: E402
from app.models import SessionLocal, User          # noqa: E402
from app.lampiran_pembimbing import LAMPIRAN_DIR   # noqa: E402
from PIL import Image, ImageDraw                   # noqa: E402
import zipfile                                     # noqa: E402

db = SessionLocal()
u = db.query(User).filter(User.email == 'wulan@bikinaja.me').first()
db.close()
TOK = 'eduai_session=' + buat_token(u.id)

naskah = ('1.1 Latar Belakang\n\n' +
          ('Kalimat pengisi agar panjang memadai. ' * 40) + '\n')


def panggil(komentar, lampiran):
    body = json.dumps({'naskah': naskah, 'komentar': komentar,
                       'lampiran': lampiran, 'tunggu': 'true'}).encode()
    req = urllib.request.Request(
        'http://127.0.0.1:8000/api/ai/v1/revisi', data=body,
        headers={'Content-Type': 'application/json', 'Cookie': TOK})
    d = json.loads(urllib.request.urlopen(req, timeout=460).read().decode())
    return d.get('jawaban', ''), d.get('model', '')


# ── Putaran 1: docx berisi KALIMAT CONTOH nyata ──────────────────────
KALIMAT = ('KataRahasiaLampiran777: Perkebunan kelapa sawit '
           'berkembang pesat sebagai tulang punggung ekonomi pedesaan.')
buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w') as z:
    z.writestr('word/document.xml',
               '<?xml version="1.0"?><w:document '
               'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
               '<w:body><w:p><w:r><w:t>' + KALIMAT + '</w:t></w:r></w:p>'
               '</w:body></w:document>')
(LAMPIRAN_DIR / 'e2e_lampiran_1a2b3c4d5e6f7a8b9c0d1e2f.docx').write_bytes(
    buf.getvalue())

isi, model = panggil(
    ['Perbaiki kalimat kedua naskah ini (yang berulang "Kalimat pengisi '
     'agar panjang memadai."). Ganti kalimat itu dengan kalimat contoh '
     'yang ada di dalam CONTOH lampiran pembimbing, tanpa mengubah '
     'kalimat lain.'],
    ['e2e_lampiran_1a2b3c4d5e6f7a8b9c0d1e2f.docx'])
lulus1 = 'KataRahasiaLampiran777' in isi or (
    'tulang punggung ekonomi pedesaan' in isi)
print(f'PUTARAN 1 (docx): model={model} → '
      f'{"✅ AI menyalin kalimat contoh" if lulus1 else "❌ " + isi[:160]}')

# ── Putaran 2: gambar berisi teks contoh ─────────────────────────────
img = Image.new('RGB', (520, 90), 'white')
ImageDraw.Draw(img).text((10, 35),
                         'CONTOH: Produksi sawit naik 42 persen.', fill='black')
gb = io.BytesIO()
img.save(gb, 'PNG')
(LAMPIRAN_DIR / 'e2e_lampiran_2b3c4d5e6f7a8b9c0d1e2f3a.png').write_bytes(
    gb.getvalue())

isi2, model2 = panggil(
    ['Perbaiki kalimat kedua naskah ini (yang berulang "Kalimat pengisi '
     'agar panjang memadai."). Ganti kalimat itu dengan kalimat yang '
     'MEMUAT persis ANGKA persentase yang tertulis pada GAMBAR contoh '
     'dari pembimbing ("Produksi sawit naik ... persen"), tanpa '
     'mengubah kalimat lain.'],
    ['e2e_lampiran_2b3c4d5e6f7a8b9c0d1e2f3a.png'])
lulus2 = '42 persen' in isi2 or '42%' in isi2
print(f'PUTARAN 2 (gambar): model={model2} → '
      f'{"✅ AI membaca angka dari gambar" if lulus2 else "❌ " + isi2[:160]}')

print('\nRINGKAS:', '2/2 LULUS' if (lulus1 and lulus2) else 'BELUM LULUS')
sys.exit(0 if (lulus1 and lulus2) else 1)
