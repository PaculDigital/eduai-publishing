"""ANALISA CELAH — hitung nyata: berapa bab, panjang, bagian, dan yang bisa
diselesaikan dengan 3 revisi (paket gratis)."""
import subprocess

EMAIL = 'uji-gratis-render@test.local'


def di(py):
    r = subprocess.run(['docker', 'exec', 'eduai-app', 'python3', '-c', py],
                       capture_output=True, text=True, timeout=240)
    return (r.stdout or '').strip(), (r.stderr or '').strip()


out, err = di(f"""
import sys; sys.path.insert(0,'/app')
from app.models import SessionLocal, User, FileBerkas
from app.ai import deteksi_bab, hitung_bagian, potong_cerdas
from app.config import AI_POTONG_KARAKTER, AI_POTONG_MAKS_BAGIAN
from sqlalchemy import select

db = SessionLocal()
uji = db.scalars(select(User).where(User.email=='{EMAIL}')).first()
fb = db.scalars(select(FileBerkas).where(FileBerkas.user_id==uji.id,
                 FileBerkas.nama=='acuan_tesis.docx')).first()

# Ambil teks dari docx (pakai parser aplikasi)
from app.main import _teks_dari_berkas if hasattr(__import__('app.main', fromlist=['x']), '_teks_dari_berkas') else None
""" + "\n" + """
# fallback: baca docx langsung
import zipfile, re
from app.config import UPLOAD_DIR
p = UPLOAD_DIR / str(uji.id) / fb.nama_simpan
with zipfile.ZipFile(p) as z:
    xml = z.read('word/document.xml').decode('utf-8','replace')
teks = re.sub(r'<[^>]+>', ' ', xml)
teks = re.sub(r'\\s+', ' ', teks).strip()

print('='*66)
print('  ANGKA NYATA — tesis Bos sebagai contoh')
print('='*66)
print(f'  Panjang dokumen   : {len(teks):,} karakter'.replace(',','.'))
print(f'  Batas per bagian  : {AI_POTONG_KARAKTER:,} karakter'.replace(',','.'))
print(f'  Maks bagian       : {AI_POTONG_MAKS_BAGIAN}')
print(f'  Bila SELURUH doc  : {hitung_bagian(teks)} bagian (= revisi)')
print()

bab = deteksi_bab(teks)
print(f'  BAB TERDETEKSI    : {len(bab)}')
print()
print('  ' + '-'*62)
print(f'  {{"Bab":<28}} {{"Karakter":>10}} {{"Bagian":>7}} {{"Kumulatif":>10}}')
print('  ' + '-'*62)
kum = 0
for b in bab:
    bg = max(1, -(-b['panjang'] // AI_POTONG_KARAKTER))
    kum += bg
    tanda = ''
    if kum > 3 and kum - bg <= 3:
        tanda = '  <<< BATAS GRATIS (3) DI SINI'
    print(f"  {{b['label'][:27]:<28}} {{b['panjang']:>10,}} {{bg:>7}} {{kum:>10}}{{tanda}}".replace(',','.'))
print('  ' + '-'*62)
print()
print(f'  TOTAL bagian seluruh bab: {kum}')
print(f'  Kuota GRATIS            : 3 revisi')
print(f'  → Gratis bisa selesai   : {sum(1 for i in range(1,len(bab)+1) if sum(max(1,-(-x[\"panjang\"]//AI_POTONG_KARAKTER)) for x in bab[:i]) <= 3)} bab pertama')
db.close()
""")
print(out or ('ERR: ' + err[:800]))
